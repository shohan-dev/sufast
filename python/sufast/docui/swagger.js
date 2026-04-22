(() => {
  "use strict";

  const spec = window.__SUFAST_SPEC__ || {};
  const defaultTheme = window.__SUFAST_DEFAULT_THEME__ || "dark";

  const KEYS = {
    theme: "sufast_docs_theme",
    favorites: "sufast_docs_favorites",
    recent: "sufast_docs_recent",
  };

  const state = {
    q: "",
    method: "all",
    endpoint: "",
    favoritesOnly: false,
    theme: defaultTheme,
    activeNavIndex: -1,
  };

  let activeLinkMenu = null;
  let toastTimer = null;

  const dom = {
    byId(id) {
      return document.getElementById(id);
    },
  };

  const readJSON = (key, fallback) => {
    try {
      return JSON.parse(localStorage.getItem(key) || JSON.stringify(fallback));
    } catch {
      return fallback;
    }
  };

  const writeJSON = (key, value) => {
    localStorage.setItem(key, JSON.stringify(value));
  };

  const escapeHtml = (value) => {
    const d = document.createElement("div");
    d.textContent = value == null ? "" : String(value);
    return d.innerHTML;
  };

  const safeJSON = (value) => {
    try {
      return JSON.stringify(value, null, 2);
    } catch {
      return String(value);
    }
  };

  const showToast = (message) => {
    let toast = document.querySelector(".toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.className = "toast";
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add("show");
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("show"), 1400);
  };

  const highlightJson = (value) => {
    const raw = typeof value === "string" ? value : safeJSON(value);
    const escaped = raw
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
    return escaped.replace(
      /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\btrue\b|\bfalse\b|\bnull\b|-?\d+(?:\.\d+)?(?:[eE][+\-]?\d+)?)/g,
      (m) => {
        let cls = "json-number";
        if (/^"/.test(m)) cls = /:$/.test(m) ? "json-key" : "json-string";
        else if (m === "true" || m === "false") cls = "json-boolean";
        else if (m === "null") cls = "json-null";
        return `<span class="${cls}">${m}</span>`;
      }
    );
  };

  const renderJsonView = (value) => {
    const raw = typeof value === "string" ? value : safeJSON(value);
    const lines = raw.split("\n");
    return `
      <div class="json-view">
        ${lines
          .map((line) => `<div class="json-line">${highlightJson(line)}</div>`)
          .join("")}
      </div>
    `;
  };

  const operationId = (path, method) =>
    `${method}_${path}`.replace(/[^a-zA-Z0-9]/g, "_");

  const parseUrlState = () => {
    const q = new URLSearchParams(window.location.search);
    return {
      q: q.get("q") || "",
      method: q.get("method") || "all",
      endpoint: q.get("endpoint") || "",
      favoritesOnly: q.get("favorites") === "1",
      theme: q.get("theme") || "",
    };
  };

  const writeUrlState = (partial) => {
    const params = new URLSearchParams(window.location.search);
    const next = {
      q: partial.q ?? state.q ?? "",
      method: partial.method ?? state.method ?? "all",
      endpoint: partial.endpoint ?? state.endpoint ?? "",
      favoritesOnly: partial.favoritesOnly ?? state.favoritesOnly ?? false,
      theme: partial.theme ?? state.theme ?? defaultTheme,
    };
    params.delete("q");
    params.delete("method");
    params.delete("endpoint");
    params.delete("favorites");
    params.delete("theme");
    if (next.q) params.set("q", next.q);
    if (next.method && next.method !== "all") params.set("method", next.method);
    if (next.endpoint) params.set("endpoint", next.endpoint);
    if (next.favoritesOnly) params.set("favorites", "1");
    if (next.theme) params.set("theme", next.theme);
    const nextUrl = `${window.location.pathname}${
      params.toString() ? `?${params.toString()}` : ""
    }`;
    window.history.replaceState(null, "", nextUrl);
  };

  const getFavorites = () => new Set(readJSON(KEYS.favorites, []));
  const setFavorites = (set) => writeJSON(KEYS.favorites, Array.from(set));
  const getRecent = () => readJSON(KEYS.recent, []);
  const setRecent = (arr) => writeJSON(KEYS.recent, arr.slice(0, 8));

  const markRecent = (id) => {
    const rec = getRecent().filter((x) => x !== id);
    rec.unshift(id);
    setRecent(rec);
  };

  const flattenOps = () => {
    const rows = [];
    const paths = spec.paths || {};
    for (const [path, methods] of Object.entries(paths)) {
      for (const [method, op] of Object.entries(methods)) {
        const m = op["x-websocket"] ? "ws" : method.toLowerCase();
        const tags = op.tags || ["default"];
        rows.push({
          id: operationId(path, method),
          path,
          method: method.toLowerCase(),
          methodLabel: m,
          op,
          primaryTag: tags[0] || "default",
          searchable: `${path} ${op.summary || ""} ${op.description || ""} ${tags.join(
            " "
          )}`.toLowerCase(),
        });
      }
    }
    return rows;
  };

  const ops = flattenOps();
  const byIdMap = new Map(ops.map((op) => [op.id, op]));

  const applyTheme = (theme) => {
    const normalized = theme === "light" ? "light" : "dark";
    state.theme = normalized;
    document.documentElement.setAttribute("data-theme", normalized);
    document.documentElement.style.colorScheme = normalized;
    localStorage.setItem(KEYS.theme, normalized);
    const btn = dom.byId("themeToggle");
    const mBtn = dom.byId("mobileTheme");
    if (btn) btn.textContent = normalized === "dark" ? "Dark" : "Light";
    if (mBtn) mBtn.textContent = normalized === "dark" ? "Theme: Dark" : "Theme: Light";
    writeUrlState({ theme: normalized });
  };

  const groupByTag = (items) => {
    const grouped = {};
    for (const item of items) {
      if (!grouped[item.primaryTag]) grouped[item.primaryTag] = [];
      grouped[item.primaryTag].push(item);
    }
    return grouped;
  };

  const renderQuickPins = () => {
    const host = dom.byId("quickPins");
    if (!host) return;
    const favs = getFavorites();
    const rec = getRecent();
    const out = [];

    for (const id of favs) {
      const item = byIdMap.get(id);
      if (!item) continue;
      out.push({
        id,
        label: `★ ${item.methodLabel.toUpperCase()} ${item.path}`,
      });
    }

    for (const id of rec) {
      if (favs.has(id)) continue;
      const item = byIdMap.get(id);
      if (!item) continue;
      out.push({
        id,
        label: `Recent ${item.methodLabel.toUpperCase()} ${item.path}`,
      });
    }

    host.innerHTML = "";
    if (!out.length) {
      host.innerHTML = '<span class="quick-pin">No quick pins yet</span>';
      return;
    }
    out.slice(0, 10).forEach((pin) => {
      const b = document.createElement("button");
      b.className = "quick-pin";
      b.type = "button";
      b.textContent = pin.label;
      b.addEventListener("click", () => focusEndpoint(pin.id, true));
      host.appendChild(b);
    });
  };

  const navItems = () =>
    Array.from(document.querySelectorAll(".nav-list .nav-item"));

  const setActiveNav = (id) => {
    const items = navItems();
    state.activeNavIndex = -1;
    items.forEach((btn, idx) => {
      const active = btn.dataset.id === id;
      btn.classList.toggle("active", active);
      if (active) state.activeNavIndex = idx;
    });
  };

  const renderNav = (filtered) => {
    const nav = dom.byId("navList");
    if (!nav) return;
    nav.innerHTML = "";
    filtered.forEach((item) => {
      const b = document.createElement("button");
      b.className = "nav-item";
      b.type = "button";
      b.dataset.id = item.id;
      b.textContent = `${item.methodLabel.toUpperCase()} ${item.path}`;
      b.addEventListener("click", () => focusEndpoint(item.id, true));
      nav.appendChild(b);
    });
    setActiveNav(state.endpoint);
  };

  const renderParamInputs = (item) => {
    const params = item.op.parameters || [];
    if (!params.length) return "";
    const rows = params.slice(0, 8);
    return `
      <div class="param-grid">
        ${rows
          .map(
            (p) => `
          <div class="field">
            <label>${escapeHtml(p.name)} (${escapeHtml(p.in || "query")})</label>
            <input
              type="text"
              data-param-name="${escapeHtml(p.name)}"
              data-param-in="${escapeHtml(p.in || "query")}"
              value="${escapeHtml(p.example || p.schema?.default || "")}"
            />
          </div>`
          )
          .join("")}
      </div>
    `;
  };

  const renderBodyEditor = (item) => {
    if (!["post", "put", "patch"].includes(item.method)) return "";
    const ex = item.op.requestBody?.content?.["application/json"]?.example;
    const text = ex ? safeJSON(ex) : "{}";
    return `
      <div class="field">
        <label>Request JSON body</label>
        <textarea id="body-${item.id}">${escapeHtml(text)}</textarea>
      </div>
    `;
  };

  const renderResponseExamples = (item) => {
    const responses = item.op.responses || {};
    const sections = [];
    for (const [status, meta] of Object.entries(responses)) {
      const example = meta?.content?.["application/json"]?.example;
      if (!example) continue;
      sections.push(`
        <details class="response-block">
          <summary>Response Example (${escapeHtml(status)})</summary>
          ${renderJsonView(example)}
        </details>
      `);
    }
    return sections.join("");
  };

  const buildEndpointCard = (item) => {
    const favs = getFavorites();
    const isFav = favs.has(item.id);
    return `
      <article class="endpoint" id="ep-${item.id}" data-id="${item.id}">
        <div class="endpoint-header">
          <span class="method">${item.methodLabel.toUpperCase()}</span>
          <code class="path">${escapeHtml(item.path)}</code>
          <span class="summary">${escapeHtml(item.op.summary || "No summary")}</span>
          <div class="actions">
            <button class="icon ${isFav ? "active" : ""}" data-act="fav" type="button" title="Favorite">★</button>
            <button class="icon" data-act="copy" type="button" title="Link options">Link</button>
          </div>
        </div>
        <div class="endpoint-body">
          <p class="desc">${escapeHtml(item.op.description || "No description.")}</p>
          ${renderParamInputs(item)}
          ${renderBodyEditor(item)}
          ${renderResponseExamples(item)}
          <div class="response-runtime" id="res-${item.id}"></div>
          <div class="try-row">
            <button class="btn" data-act="exec" type="button">Execute</button>
            <button class="btn ghost" data-act="clear" type="button">Clear</button>
          </div>
        </div>
      </article>
    `;
  };

  const renderGroups = (filtered) => {
    const host = dom.byId("groups");
    if (!host) return;
    const grouped = groupByTag(filtered);
    host.innerHTML = "";

    for (const [tag, items] of Object.entries(grouped)) {
      const section = document.createElement("section");
      section.className = "tag-group";
      section.innerHTML = `
        <h2 class="tag-title">${escapeHtml(tag)} <span>(${items.length})</span></h2>
        ${items.map(buildEndpointCard).join("")}
      `;
      host.appendChild(section);
    }

    bindCardInteractions();
  };

  const buildRequestFromInputs = (item, card) => {
    let path = item.path;
    const query = new URLSearchParams();
    const headers = {};
    card.querySelectorAll("input[data-param-name]").forEach((el) => {
      const name = el.dataset.paramName || "";
      const where = el.dataset.paramIn || "query";
      const value = (el.value || "").trim();
      if (!value) return;
      if (where === "path") {
        path = path.replace(`{${name}}`, encodeURIComponent(value));
      } else if (where === "query") {
        query.set(name, value);
      } else if (where === "header") {
        headers[name] = value;
      }
    });
    const qs = query.toString();
    const url = qs ? `${path}?${qs}` : path;
    const init = {
      method: item.method.toUpperCase(),
      headers,
    };
    if (["post", "put", "patch"].includes(item.method)) {
      const body = dom.byId(`body-${item.id}`);
      if (body && body.value.trim()) {
        init.body = body.value.trim();
        init.headers["Content-Type"] = "application/json";
      }
    }
    return { url, init };
  };

  const executeRequest = async (item, card) => {
    const resEl = dom.byId(`res-${item.id}`);
    if (!resEl) return;
    const { url, init } = buildRequestFromInputs(item, card);
    resEl.innerHTML = "<div class='state-card'>Sending request...</div>";
    try {
      const started = performance.now();
      const resp = await fetch(url, init);
      const elapsed = Math.round(performance.now() - started);
      const raw = await resp.text();
      const ct = resp.headers.get("content-type") || "unknown";
      const headers = Object.fromEntries(resp.headers.entries());
      let parsedBody = raw;
      if ((ct || "").toLowerCase().includes("json")) {
        try {
          parsedBody = JSON.parse(raw);
        } catch {
          parsedBody = raw;
        }
      } else {
        try {
          parsedBody = JSON.parse(raw);
        } catch {
          parsedBody = raw;
        }
      }
      resEl.innerHTML = `
        <details class="response-block" open>
          <summary>Status / Body (${resp.status}) ${escapeHtml(
            resp.statusText
          )} · ${elapsed}ms</summary>
          ${renderJsonView(parsedBody)}
        </details>
        <details class="response-block">
          <summary>Raw Headers / Metadata</summary>
          ${renderJsonView({ contentType: ct, headers })}
        </details>
      `;
    } catch (error) {
      resEl.innerHTML = `
        <div class="state-card error">
          <strong>Request failed</strong>
          <span>${escapeHtml(String(error))}</span>
        </div>
      `;
    }
  };

  const setEndpointExpanded = (id, expanded) => {
    const card = dom.byId(`ep-${id}`);
    if (!card) return;
    card.classList.toggle("expanded", expanded);
  };

  const focusEndpoint = (id, smooth) => {
    const card = dom.byId(`ep-${id}`);
    if (!card) return;
    document.querySelectorAll(".endpoint.expanded").forEach((e) => {
      if (e.id !== `ep-${id}`) e.classList.remove("expanded");
    });
    card.classList.add("expanded");
    card.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: "start" });
    state.endpoint = id;
    setActiveNav(id);
    writeUrlState({ endpoint: id });
    markRecent(id);
    renderQuickPins();
  };

  const copyDocsDeepLink = (id) => {
    const url = new URL(window.location.href);
    url.searchParams.set("endpoint", id);
    if (state.method !== "all") url.searchParams.set("method", state.method);
    if (state.q) url.searchParams.set("q", state.q);
    if (state.favoritesOnly) url.searchParams.set("favorites", "1");
    navigator.clipboard.writeText(url.toString()).then(() => {
      showToast("Copied docs deep link");
    });
  };

  const buildVisitUrl = (item) => {
    let url = item.path;
    const query = new URLSearchParams();
    const params = item.op.parameters || [];
    for (const p of params) {
      const val = p.example ?? p.schema?.default ?? (p.in === "path" ? "1" : "");
      if (!val && val !== 0) continue;
      if (p.in === "path") {
        url = url.replace(`{${p.name}}`, encodeURIComponent(String(val)));
      } else if (p.in === "query") {
        query.set(p.name, String(val));
      }
    }
    const qs = query.toString();
    return qs ? `${url}?${qs}` : url;
  };

  const buildAbsoluteEndpointUrl = (item) => {
    const rel = buildVisitUrl(item);
    return new URL(rel, window.location.origin).toString();
  };

  const closeLinkMenu = () => {
    if (activeLinkMenu) {
      activeLinkMenu.remove();
      activeLinkMenu = null;
    }
  };

  const openLinkMenu = (event, id, item) => {
    event.stopPropagation();
    closeLinkMenu();
    const rect = event.currentTarget.getBoundingClientRect();
    const menu = document.createElement("div");
    menu.className = "link-menu";
    menu.innerHTML = `
      <button type="button" class="link-menu-btn" data-menu="copy">Copy Link</button>
      <button type="button" class="link-menu-btn" data-menu="visit">Visit Endpoint</button>
    `;
    menu.style.top = `${Math.round(rect.bottom + 8)}px`;
    menu.style.left = `${Math.round(rect.right - 150)}px`;
    document.body.appendChild(menu);
    activeLinkMenu = menu;

    menu.querySelector('[data-menu="copy"]')?.addEventListener("click", () => {
      const endpointUrl = buildAbsoluteEndpointUrl(item);
      navigator.clipboard.writeText(endpointUrl).then(() => {
        showToast("Copied endpoint URL");
      });
      closeLinkMenu();
    });
    menu.querySelector('[data-menu="visit"]')?.addEventListener("click", () => {
      const visitUrl = buildVisitUrl(item);
      window.open(visitUrl, "_blank", "noopener");
      showToast("Opened endpoint in new tab");
      closeLinkMenu();
    });
  };

  const bindCardInteractions = () => {
    document.querySelectorAll(".endpoint").forEach((card) => {
      const id = card.dataset.id || "";
      const item = byIdMap.get(id);
      if (!item) return;

      const header = card.querySelector(".endpoint-header");
      header?.addEventListener("click", (e) => {
        if (e.target && e.target.closest("[data-act]")) return;
        const nowExpanded = !card.classList.contains("expanded");
        document.querySelectorAll(".endpoint.expanded").forEach((el) => {
          if (el !== card) el.classList.remove("expanded");
        });
        card.classList.toggle("expanded", nowExpanded);
        state.endpoint = nowExpanded ? id : "";
        writeUrlState({ endpoint: state.endpoint });
        if (nowExpanded) {
          setActiveNav(id);
          markRecent(id);
          renderQuickPins();
        }
      });

      card.querySelector('[data-act="fav"]')?.addEventListener("click", (e) => {
        e.stopPropagation();
        const favs = getFavorites();
        if (favs.has(id)) favs.delete(id);
        else favs.add(id);
        setFavorites(favs);
        applyFilters();
      });

      card.querySelector('[data-act="copy"]')?.addEventListener("click", (e) => {
        openLinkMenu(e, id, item);
      });

      card.querySelector('[data-act="exec"]')?.addEventListener("click", (e) => {
        e.stopPropagation();
        executeRequest(item, card);
      });

      card.querySelector('[data-act="clear"]')?.addEventListener("click", (e) => {
        e.stopPropagation();
        const resEl = dom.byId(`res-${id}`);
        if (resEl) resEl.innerHTML = "";
      });
    });
  };

  const filteredOps = () => {
    const favs = getFavorites();
    return ops.filter((item) => {
      const qOk = item.searchable.includes(state.q.toLowerCase());
      const mOk = state.method === "all" || item.methodLabel === state.method;
      const fOk = !state.favoritesOnly || favs.has(item.id);
      return qOk && mOk && fOk;
    });
  };

  const applyFilters = () => {
    const loading = dom.byId("loadingState");
    const empty = dom.byId("emptyState");
    const error = dom.byId("errorState");
    const errorText = dom.byId("errorText");
    if (loading) loading.hidden = false;
    if (error) error.hidden = true;
    try {
      const filtered = filteredOps();
      renderNav(filtered);
      renderGroups(filtered);
      renderQuickPins();

      const meta = dom.byId("resultsMeta");
      if (meta) meta.textContent = `${filtered.length} endpoint(s) visible`;
      if (empty) empty.hidden = filtered.length > 0;

      state.activeNavIndex = -1;
      navItems().forEach((b, idx) => {
        if (b.classList.contains("active")) state.activeNavIndex = idx;
      });

      writeUrlState({
        q: state.q,
        method: state.method,
        favoritesOnly: state.favoritesOnly,
      });
    } catch (err) {
      if (errorText) errorText.textContent = String(err);
      if (error) error.hidden = false;
    } finally {
      if (loading) loading.hidden = true;
    }
  };

  const restoreState = () => {
    const url = parseUrlState();
    state.q = url.q || "";
    state.method = url.method || "all";
    state.endpoint = url.endpoint || "";
    state.favoritesOnly = !!url.favoritesOnly;
    state.theme = url.theme || localStorage.getItem(KEYS.theme) || defaultTheme;
  };

  const bindLayoutActions = () => {
    const sidebar = dom.byId("sidebar");
    const overlay = dom.byId("overlay");
    const openMobile = () => {
      sidebar?.classList.add("open");
      overlay?.classList.add("open");
    };
    const closeMobile = () => {
      sidebar?.classList.remove("open");
      overlay?.classList.remove("open");
    };

    dom.byId("mobileOpen")?.addEventListener("click", openMobile);
    dom.byId("mobileClose")?.addEventListener("click", closeMobile);
    overlay?.addEventListener("click", closeMobile);

    const toggleTheme = () =>
      applyTheme(document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark");

    dom.byId("themeToggle")?.addEventListener("click", toggleTheme);
    dom.byId("mobileTheme")?.addEventListener("click", toggleTheme);

    dom.byId("favoritesOnly")?.addEventListener("click", () => {
      state.favoritesOnly = !state.favoritesOnly;
      dom.byId("favoritesOnly")?.classList.toggle("active", state.favoritesOnly);
      applyFilters();
    });

    dom.byId("searchInput")?.addEventListener("input", (e) => {
      state.q = String(e.target.value || "");
      applyFilters();
    });

    document.querySelectorAll("#methodFilters .chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        document
          .querySelectorAll("#methodFilters .chip")
          .forEach((x) => x.classList.remove("active"));
        chip.classList.add("active");
        state.method = chip.dataset.method || "all";
        applyFilters();
      });
    });

    dom.byId("expandAll")?.addEventListener("click", () => {
      document.querySelectorAll(".endpoint").forEach((el) => el.classList.add("expanded"));
    });

    dom.byId("collapseAll")?.addEventListener("click", () => {
      document.querySelectorAll(".endpoint").forEach((el) => el.classList.remove("expanded"));
      state.endpoint = "";
      writeUrlState({ endpoint: "" });
    });

    dom.byId("clearFilters")?.addEventListener("click", () => {
      state.q = "";
      state.method = "all";
      state.favoritesOnly = false;
      dom.byId("searchInput").value = "";
      dom.byId("favoritesOnly")?.classList.remove("active");
      document
        .querySelectorAll("#methodFilters .chip")
        .forEach((x) => x.classList.toggle("active", x.dataset.method === "all"));
      applyFilters();
    });
  };

  const bindKeyboard = () => {
    document.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        dom.byId("searchInput")?.focus();
        dom.byId("searchInput")?.select();
        return;
      }
      if (e.key === "Escape") {
        closeLinkMenu();
        const search = dom.byId("searchInput");
        if (document.activeElement === search) {
          search.blur();
          return;
        }
      }
      const items = navItems();
      if (!items.length) return;
      if (e.key === "ArrowDown") {
        e.preventDefault();
        state.activeNavIndex = Math.min(items.length - 1, state.activeNavIndex + 1);
        items[state.activeNavIndex]?.focus();
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        state.activeNavIndex = Math.max(0, state.activeNavIndex - 1);
        items[state.activeNavIndex]?.focus();
      } else if (e.key === "Enter") {
        const focused = document.activeElement;
        if (focused && focused.classList.contains("nav-item")) {
          focused.click();
        }
      }
    });
  };

  const hydrateUIFromState = () => {
    dom.byId("searchInput").value = state.q;
    dom.byId("favoritesOnly")?.classList.toggle("active", state.favoritesOnly);
    document.querySelectorAll("#methodFilters .chip").forEach((chip) => {
      chip.classList.toggle("active", chip.dataset.method === state.method);
    });
  };

  const init = () => {
    restoreState();
    applyTheme(state.theme || defaultTheme);
    bindLayoutActions();
    bindKeyboard();
    hydrateUIFromState();
    applyFilters();
    if (state.endpoint) {
      setTimeout(() => focusEndpoint(state.endpoint, false), 110);
    }

    document.addEventListener("click", (e) => {
      if (!activeLinkMenu) return;
      const inMenu = e.target && e.target.closest(".link-menu");
      const onLinkButton = e.target && e.target.closest('[data-act="copy"]');
      if (!inMenu && !onLinkButton) closeLinkMenu();
    });
  };

  window.addEventListener("DOMContentLoaded", init);
})();
