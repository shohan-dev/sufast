(() => {
  "use strict";

  const spec = window.__SUFAST_SPEC__ || {};
  const THEME_KEY = "sufast_docs_theme";

  const byId = (id) => document.getElementById(id);

  const state = {
    q: "",
    method: "all",
    theme: "dark",
  };

  const parseUrlState = () => {
    const q = new URLSearchParams(window.location.search);
    return {
      q: q.get("q") || "",
      method: q.get("method") || "all",
      theme: q.get("theme") || "",
    };
  };

  const writeUrlState = () => {
    const p = new URLSearchParams(window.location.search);
    p.delete("q");
    p.delete("method");
    p.delete("theme");
    if (state.q) p.set("q", state.q);
    if (state.method !== "all") p.set("method", state.method);
    if (state.theme) p.set("theme", state.theme);
    const next = `${window.location.pathname}${p.toString() ? `?${p.toString()}` : ""}`;
    window.history.replaceState(null, "", next);
  };

  const flattenOps = () => {
    const rows = [];
    for (const [path, methods] of Object.entries(spec.paths || {})) {
      for (const [method, op] of Object.entries(methods)) {
        const id = `${method}_${path}`.replace(/[^a-zA-Z0-9]/g, "_");
        rows.push({
          id,
          path,
          method: method.toLowerCase(),
          summary: op.summary || "",
          tags: op.tags || [],
        });
      }
    }
    return rows;
  };

  const ops = flattenOps();

  const applyTheme = (theme) => {
    const normalized = theme === "light" ? "light" : "dark";
    state.theme = normalized;
    document.documentElement.setAttribute("data-theme", normalized);
    document.documentElement.style.colorScheme = normalized;
    localStorage.setItem(THEME_KEY, normalized);
    const btn = byId("themeToggle");
    if (btn) btn.textContent = normalized === "dark" ? "Dark" : "Light";
    writeUrlState();
  };

  const redocTheme = () => {
    if (state.theme === "light") {
      return {
        colors: {
          primary: { main: "#546de8" },
          text: { primary: "#111a30", secondary: "#4e5d7d" },
          border: { dark: "#d7e1f6" },
        },
        typography: { fontFamily: 'Inter, "Segoe UI", sans-serif' },
      };
    }
    return {
      colors: {
        primary: { main: "#8fa8ff" },
        text: { primary: "#e8eefc", secondary: "#9aa7c7" },
        border: { dark: "#2f4067" },
      },
      typography: { fontFamily: 'Inter, "Segoe UI", sans-serif' },
    };
  };

  const renderRedoc = () => {
    const host = byId("redoc-container");
    if (!host) return;
    host.innerHTML = "";
    Redoc.init(spec, { theme: redocTheme(), hideDownloadButton: false }, host);
  };

  const quickFilter = () =>
    ops.filter((row) => {
      const qOk = `${row.path} ${row.summary} ${row.tags.join(" ")}`
        .toLowerCase()
        .includes(state.q.toLowerCase());
      const mOk = state.method === "all" || row.method === state.method;
      return qOk && mOk;
    });

  const copyLinkForOp = (row) => {
    const url = new URL(window.location.href);
    url.searchParams.set("q", row.path);
    url.searchParams.set("method", row.method);
    url.searchParams.set("endpoint", row.id);
    navigator.clipboard.writeText(url.toString());
  };

  const renderQuickLinks = () => {
    const host = byId("quickLinks");
    if (!host) return;
    const rows = quickFilter().slice(0, 24);
    host.innerHTML = "";
    if (!rows.length) {
      host.innerHTML = '<span class="quick-link">No quick matches</span>';
      writeUrlState();
      return;
    }
    rows.forEach((row) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "quick-link";
      btn.textContent = `${row.method.toUpperCase()} ${row.path}`;
      btn.addEventListener("click", () => copyLinkForOp(row));
      host.appendChild(btn);
    });
    writeUrlState();
  };

  const bindEvents = () => {
    byId("themeToggle")?.addEventListener("click", () => {
      applyTheme(state.theme === "dark" ? "light" : "dark");
      renderRedoc();
    });

    byId("copyPageLink")?.addEventListener("click", () => {
      navigator.clipboard.writeText(window.location.href);
    });

    byId("q")?.addEventListener("input", (e) => {
      state.q = String(e.target.value || "");
      renderQuickLinks();
    });

    byId("methodFilter")?.addEventListener("change", (e) => {
      state.method = String(e.target.value || "all");
      renderQuickLinks();
    });
  };

  const init = () => {
    const urlState = parseUrlState();
    state.q = urlState.q;
    state.method = urlState.method;
    state.theme = urlState.theme || localStorage.getItem(THEME_KEY) || "dark";
    applyTheme(state.theme || "dark");

    byId("q").value = state.q;
    byId("methodFilter").value = state.method;

    bindEvents();
    renderRedoc();
    renderQuickLinks();
  };

  window.addEventListener("DOMContentLoaded", init);
})();
