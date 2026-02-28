"""
Sufast Swagger UI - Beautiful, interactive API documentation.
Complete Swagger/OpenAPI UI with try-it-out functionality.
"""

import json
from typing import List, Dict, Any, Optional


def generate_swagger_html(openapi_spec: dict, theme: str = "default") -> str:
    """Generate complete Swagger UI HTML page from OpenAPI spec."""
    spec_json = json.dumps(openapi_spec, default=str)
    title = openapi_spec.get("info", {}).get("title", "Sufast API")
    version = openapi_spec.get("info", {}).get("version", "1.0.0")
    description = openapi_spec.get("info", {}).get("description", "")
    
    paths = openapi_spec.get("paths", {})
    tags = openapi_spec.get("tags", [])
    
    # Count routes by method
    method_counts = {"get": 0, "post": 0, "put": 0, "delete": 0, "patch": 0, "websocket": 0}
    total = 0
    for path, methods in paths.items():
        for method, op in methods.items():
            m = method.lower()
            if op.get("x-websocket"):
                method_counts["websocket"] += 1
            elif m in method_counts:
                method_counts[m] += 1
            total += 1
    
    # Build tags sidebar
    tag_names = [t["name"] for t in tags] if tags else ["default"]
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} - API Documentation</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{
  --bg:#f8fafc;--surface:#fff;--surface-hover:#f1f5f9;
  --border:#e2e8f0;--border-light:#f1f5f9;
  --text:#0f172a;--text-secondary:#475569;--text-muted:#94a3b8;
  --primary:#6366f1;--primary-light:#818cf8;--primary-bg:rgba(99,102,241,0.08);
  --get:#3b82f6;--get-bg:rgba(59,130,246,0.08);--get-border:rgba(59,130,246,0.2);
  --post:#22c55e;--post-bg:rgba(34,197,94,0.08);--post-border:rgba(34,197,94,0.2);
  --put:#f59e0b;--put-bg:rgba(245,158,11,0.08);--put-border:rgba(245,158,11,0.2);
  --delete:#ef4444;--delete-bg:rgba(239,68,68,0.08);--delete-border:rgba(239,68,68,0.2);
  --patch:#a855f7;--patch-bg:rgba(168,85,247,0.08);--patch-border:rgba(168,85,247,0.2);
  --ws:#06b6d4;--ws-bg:rgba(6,182,212,0.08);--ws-border:rgba(6,182,212,0.2);
  --success:#10b981;--error:#ef4444;--warning:#f59e0b;
  --code-bg:#1e293b;--code-text:#e2e8f0;
  --radius:8px;--radius-lg:12px;--radius-xl:16px;
  --shadow:0 1px 3px rgba(0,0,0,0.1);--shadow-md:0 4px 12px rgba(0,0,0,0.08);
  --shadow-lg:0 8px 24px rgba(0,0,0,0.1);
  --transition:all 0.2s ease;
}}
body{{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);line-height:1.6;-webkit-font-smoothing:antialiased}}
.layout{{display:flex;min-height:100vh}}
.sidebar{{width:280px;background:var(--surface);border-right:1px solid var(--border);position:fixed;top:0;left:0;bottom:0;overflow-y:auto;z-index:50;transition:transform 0.3s}}
.sidebar-header{{padding:1.5rem;border-bottom:1px solid var(--border)}}
.sidebar-logo{{display:flex;align-items:center;gap:0.75rem;font-size:1.25rem;font-weight:700;color:var(--text)}}
.sidebar-logo i{{color:var(--primary);font-size:1.5rem}}
.sidebar-version{{font-size:0.75rem;color:var(--primary);background:var(--primary-bg);padding:0.15rem 0.5rem;border-radius:20px;font-weight:600;margin-left:auto}}
.sidebar-search{{padding:1rem 1.5rem}}
.sidebar-search input{{width:100%;padding:0.6rem 1rem 0.6rem 2.5rem;border:1px solid var(--border);border-radius:var(--radius);font-size:0.875rem;background:var(--bg);transition:var(--transition);outline:none}}
.sidebar-search input:focus{{border-color:var(--primary);box-shadow:0 0 0 3px var(--primary-bg)}}
.sidebar-search{{position:relative}}
.sidebar-search i{{position:absolute;left:2rem;top:50%;transform:translateY(-50%);color:var(--text-muted);font-size:0.875rem}}
.sidebar-nav{{padding:0.5rem 0}}
.nav-group{{margin-bottom:0.25rem}}
.nav-group-title{{padding:0.5rem 1.5rem;font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-muted)}}
.nav-item{{display:flex;align-items:center;gap:0.5rem;padding:0.45rem 1.5rem;font-size:0.85rem;color:var(--text-secondary);cursor:pointer;transition:var(--transition);border-left:2px solid transparent}}
.nav-item:hover{{background:var(--surface-hover);color:var(--text)}}
.nav-item.active{{background:var(--primary-bg);color:var(--primary);border-left-color:var(--primary);font-weight:600}}
.nav-method{{font-size:0.65rem;font-weight:700;text-transform:uppercase;padding:0.1rem 0.35rem;border-radius:3px;min-width:36px;text-align:center;font-family:'JetBrains Mono',monospace}}
.nav-method.get{{color:var(--get);background:var(--get-bg)}}
.nav-method.post{{color:var(--post);background:var(--post-bg)}}
.nav-method.put{{color:var(--put);background:var(--put-bg)}}
.nav-method.delete{{color:var(--delete);background:var(--delete-bg)}}
.nav-method.patch{{color:var(--patch);background:var(--patch-bg)}}
.nav-method.ws{{color:var(--ws);background:var(--ws-bg)}}
.nav-path{{font-family:'JetBrains Mono',monospace;font-size:0.8rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.main{{margin-left:280px;flex:1;padding:2rem 3rem;max-width:1100px}}
.hero{{margin-bottom:3rem}}
.hero h1{{font-size:2.25rem;font-weight:800;color:var(--text);margin-bottom:0.5rem}}
.hero-desc{{color:var(--text-secondary);font-size:1rem;margin-bottom:1.5rem;max-width:600px}}
.stats{{display:flex;gap:1rem;flex-wrap:wrap}}
.stat-pill{{display:flex;align-items:center;gap:0.4rem;padding:0.35rem 0.85rem;border-radius:20px;font-size:0.8rem;font-weight:600}}
.stat-pill.get{{color:var(--get);background:var(--get-bg)}}
.stat-pill.post{{color:var(--post);background:var(--post-bg)}}
.stat-pill.put{{color:var(--put);background:var(--put-bg)}}
.stat-pill.delete{{color:var(--delete);background:var(--delete-bg)}}
.stat-pill.patch{{color:var(--patch);background:var(--patch-bg)}}
.stat-pill.ws{{color:var(--ws);background:var(--ws-bg)}}
.stat-pill.total{{color:var(--primary);background:var(--primary-bg)}}
.tag-section{{margin-bottom:2.5rem}}
.tag-header{{display:flex;align-items:center;gap:0.75rem;padding:0.75rem 0;margin-bottom:0.75rem;cursor:pointer;user-select:none}}
.tag-header h2{{font-size:1.2rem;font-weight:700;color:var(--text)}}
.tag-badge{{font-size:0.75rem;padding:0.15rem 0.6rem;border-radius:20px;background:var(--primary-bg);color:var(--primary);font-weight:600}}
.tag-header .chevron{{color:var(--text-muted);transition:transform 0.2s;font-size:0.8rem}}
.tag-header.collapsed .chevron{{transform:rotate(-90deg)}}
.tag-content{{transition:max-height 0.3s ease}}
.tag-content.collapsed{{display:none}}
.endpoint{{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);margin-bottom:0.75rem;overflow:hidden;transition:var(--transition)}}
.endpoint:hover{{box-shadow:var(--shadow-md)}}
.endpoint.expanded{{box-shadow:var(--shadow-lg)}}
.ep-header{{display:flex;align-items:center;gap:0.75rem;padding:0.85rem 1.25rem;cursor:pointer;transition:var(--transition)}}
.ep-header:hover{{background:var(--surface-hover)}}
.method-badge{{display:inline-flex;align-items:center;justify-content:center;padding:0.3rem 0.7rem;border-radius:6px;font-size:0.7rem;font-weight:700;text-transform:uppercase;font-family:'JetBrains Mono',monospace;min-width:60px;letter-spacing:0.03em}}
.method-badge.get{{color:var(--get);background:var(--get-bg);border:1px solid var(--get-border)}}
.method-badge.post{{color:var(--post);background:var(--post-bg);border:1px solid var(--post-border)}}
.method-badge.put{{color:var(--put);background:var(--put-bg);border:1px solid var(--put-border)}}
.method-badge.delete{{color:var(--delete);background:var(--delete-bg);border:1px solid var(--delete-border)}}
.method-badge.patch{{color:var(--patch);background:var(--patch-bg);border:1px solid var(--patch-border)}}
.method-badge.ws{{color:var(--ws);background:var(--ws-bg);border:1px solid var(--ws-border)}}
.ep-path{{font-family:'JetBrains Mono',monospace;font-weight:500;font-size:0.9rem;color:var(--text);flex:1}}
.ep-path .param{{color:var(--primary);font-weight:600}}
.ep-summary{{color:var(--text-muted);font-size:0.8rem;max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.ep-tags{{display:flex;gap:0.3rem;flex-wrap:wrap}}
.ep-tag{{font-size:0.65rem;padding:0.1rem 0.5rem;border-radius:20px;background:var(--bg);color:var(--text-muted);font-weight:500;border:1px solid var(--border-light)}}
.ep-expand{{color:var(--text-muted);font-size:0.75rem;transition:transform 0.2s}}
.endpoint.expanded .ep-expand{{transform:rotate(180deg)}}
.ep-body{{display:none;border-top:1px solid var(--border);padding:1.5rem}}
.endpoint.expanded .ep-body{{display:block}}
.ep-desc{{color:var(--text-secondary);font-size:0.9rem;margin-bottom:1.5rem;padding:1rem;background:var(--bg);border-radius:var(--radius);border-left:3px solid var(--primary)}}
.section-title{{font-size:0.8rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:var(--text-muted);margin-bottom:0.75rem;display:flex;align-items:center;gap:0.5rem}}
.params-table{{width:100%;border-collapse:collapse;margin-bottom:1.5rem}}
.params-table th{{text-align:left;font-size:0.75rem;font-weight:600;color:var(--text-muted);padding:0.5rem 0.75rem;border-bottom:2px solid var(--border);text-transform:uppercase;letter-spacing:0.05em}}
.params-table td{{padding:0.65rem 0.75rem;border-bottom:1px solid var(--border-light);font-size:0.875rem;vertical-align:middle}}
.params-table tr:hover td{{background:var(--surface-hover)}}
.param-name{{font-family:'JetBrains Mono',monospace;font-weight:600;color:var(--text)}}
.param-required{{color:var(--delete);font-size:0.7rem;font-weight:600;margin-left:0.3rem}}
.param-type{{font-family:'JetBrains Mono',monospace;font-size:0.8rem;color:var(--primary);background:var(--primary-bg);padding:0.15rem 0.5rem;border-radius:4px}}
.param-in{{font-size:0.75rem;color:var(--text-muted)}}
.param-input{{width:100%;padding:0.5rem 0.75rem;border:1px solid var(--border);border-radius:var(--radius);font-family:'JetBrains Mono',monospace;font-size:0.85rem;transition:var(--transition);outline:none;background:var(--surface)}}
.param-input:focus{{border-color:var(--primary);box-shadow:0 0 0 3px var(--primary-bg)}}
.body-editor{{width:100%;min-height:120px;padding:1rem;border:1px solid var(--border);border-radius:var(--radius);font-family:'JetBrains Mono',monospace;font-size:0.85rem;background:var(--code-bg);color:var(--code-text);resize:vertical;outline:none;line-height:1.5}}
.body-editor:focus{{border-color:var(--primary);box-shadow:0 0 0 3px var(--primary-bg)}}
.try-bar{{display:flex;gap:0.75rem;margin:1.25rem 0;align-items:center;flex-wrap:wrap}}
.btn{{padding:0.5rem 1.25rem;border:none;border-radius:var(--radius);font-weight:600;font-size:0.85rem;cursor:pointer;transition:var(--transition);display:inline-flex;align-items:center;gap:0.4rem}}
.btn:active{{transform:scale(0.97)}}
.btn-primary{{background:var(--primary);color:#fff;box-shadow:0 2px 8px rgba(99,102,241,0.3)}}
.btn-primary:hover{{background:var(--primary-light);box-shadow:0 4px 12px rgba(99,102,241,0.4)}}
.btn-outline{{background:transparent;color:var(--text-secondary);border:1px solid var(--border)}}
.btn-outline:hover{{background:var(--surface-hover);border-color:var(--text-muted)}}
.btn-danger{{background:var(--error);color:#fff}}
.btn-danger:hover{{opacity:0.9}}
.response-area{{margin-top:1rem}}
.res-container{{border-radius:var(--radius-lg);overflow:hidden;border:1px solid var(--border)}}
.res-header{{display:flex;align-items:center;justify-content:space-between;padding:0.75rem 1.25rem;font-size:0.85rem;font-weight:600}}
.res-header.s2xx{{background:linear-gradient(135deg,rgba(16,185,129,0.1),rgba(16,185,129,0.05));color:var(--success);border-bottom:1px solid rgba(16,185,129,0.2)}}
.res-header.s4xx{{background:linear-gradient(135deg,rgba(245,158,11,0.1),rgba(245,158,11,0.05));color:var(--warning);border-bottom:1px solid rgba(245,158,11,0.2)}}
.res-header.s5xx{{background:linear-gradient(135deg,rgba(239,68,68,0.1),rgba(239,68,68,0.05));color:var(--error);border-bottom:1px solid rgba(239,68,68,0.2)}}
.res-header.serr{{background:linear-gradient(135deg,rgba(239,68,68,0.1),rgba(239,68,68,0.05));color:var(--error);border-bottom:1px solid rgba(239,68,68,0.2)}}
.res-status{{display:flex;align-items:center;gap:0.5rem}}
.res-time{{font-size:0.8rem;opacity:0.8;font-family:'JetBrains Mono',monospace}}
.res-body{{position:relative}}
.res-code{{padding:1.25rem;font-family:'JetBrains Mono',monospace;font-size:0.825rem;line-height:1.6;overflow-x:auto;max-height:500px;overflow-y:auto;background:var(--code-bg);color:var(--code-text)}}
.res-copy{{position:absolute;top:0.75rem;right:0.75rem;padding:0.3rem 0.6rem;background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.1);border-radius:6px;color:var(--code-text);cursor:pointer;font-size:0.75rem;opacity:0;transition:var(--transition)}}
.res-body:hover .res-copy{{opacity:1}}
.res-copy:hover{{background:rgba(255,255,255,0.2)}}
.res-copy.copied{{background:var(--success);color:#fff;border-color:var(--success)}}
.res-meta{{padding:0.5rem 1.25rem;background:var(--bg);font-size:0.75rem;color:var(--text-muted);display:flex;justify-content:space-between;border-top:1px solid var(--border-light)}}
.loading-spinner{{display:flex;align-items:center;gap:0.75rem;padding:1.5rem;color:var(--text-secondary);font-weight:500;justify-content:center}}
.loading-spinner i{{animation:spin 1s linear infinite;color:var(--primary)}}
@keyframes spin{{from{{transform:rotate(0deg)}}to{{transform:rotate(360deg)}}}}
.json .key{{color:#c084fc}}.json .str{{color:#34d399}}.json .num{{color:#f97316}}.json .bool{{color:#60a5fa}}.json .null{{color:#94a3b8;font-style:italic}}
.ws-badge{{display:inline-flex;align-items:center;gap:0.35rem;padding:0.2rem 0.6rem;border-radius:20px;font-size:0.7rem;font-weight:600;background:var(--ws-bg);color:var(--ws);border:1px solid var(--ws-border)}}
.mobile-toggle{{display:none;position:fixed;top:1rem;left:1rem;z-index:60;padding:0.5rem;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);cursor:pointer}}
.overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.3);z-index:40}}
@media(max-width:768px){{
  .sidebar{{transform:translateX(-100%)}}
  .sidebar.open{{transform:translateX(0)}}
  .overlay.open{{display:block}}
  .main{{margin-left:0;padding:1rem}}
  .mobile-toggle{{display:flex}}
  .ep-summary{{display:none}}
}}
.tier-badge{{font-size:0.65rem;padding:0.1rem 0.45rem;border-radius:4px;font-weight:600;margin-left:0.5rem}}
.tier-badge.static{{background:#fef2f2;color:#dc2626}}.tier-badge.cached{{background:#fffbeb;color:#d97706}}.tier-badge.dynamic{{background:#eff6ff;color:#2563eb}}
.dark-toggle{{cursor:pointer;padding:0.4rem;border-radius:6px;border:1px solid var(--border);background:transparent;color:var(--text-muted);font-size:0.9rem;transition:var(--transition)}}
.dark-toggle:hover{{background:var(--surface-hover)}}
</style>
</head>
<body>

<button class="mobile-toggle" onclick="toggleSidebar()"><i class="fas fa-bars"></i></button>
<div class="overlay" id="overlay" onclick="toggleSidebar()"></div>

<div class="layout">
<!-- Sidebar -->
<aside class="sidebar" id="sidebar">
  <div class="sidebar-header">
    <div class="sidebar-logo">
      <i class="fas fa-rocket"></i>
      <span>{title}</span>
      <span class="sidebar-version">v{version}</span>
    </div>
  </div>
  <div class="sidebar-search">
    <i class="fas fa-search"></i>
    <input type="text" placeholder="Search endpoints..." oninput="searchEndpoints(this.value)" id="searchInput">
  </div>
  <nav class="sidebar-nav" id="sidebarNav">
    <!-- Populated by JS -->
  </nav>
</aside>

<!-- Main Content -->
<main class="main" id="mainContent">
  <div class="hero">
    <h1>{title}</h1>
    <p class="hero-desc">{description or "Interactive API documentation powered by Sufast hybrid Rust+Python framework"}</p>
    <div class="stats">
      <span class="stat-pill total"><i class="fas fa-globe"></i> {total} endpoints</span>
      {"".join(f'<span class="stat-pill {m}"><i class="fas fa-{_method_icon(m)}"></i> {c} {m.upper()}</span>' for m, c in method_counts.items() if c > 0)}
    </div>
  </div>
  
  <div id="endpointsContainer">
    <!-- Populated by JS -->
  </div>
</main>
</div>

<script>
const spec = {spec_json};

function init() {{
  renderSidebar();
  renderEndpoints();
}}

function renderSidebar() {{
  const nav = document.getElementById('sidebarNav');
  const paths = spec.paths || {{}};
  const tags = spec.tags || [];
  const tagMap = {{}};
  
  // Group by tags
  for (const [path, methods] of Object.entries(paths)) {{
    for (const [method, op] of Object.entries(methods)) {{
      const opTags = op.tags || ['default'];
      for (const tag of opTags) {{
        if (!tagMap[tag]) tagMap[tag] = [];
        tagMap[tag].push({{ path, method, op }});
      }}
    }}
  }}
  
  let html = '';
  for (const [tag, endpoints] of Object.entries(tagMap)) {{
    html += `<div class="nav-group">
      <div class="nav-group-title">${{tag}} (${{endpoints.length}})</div>`;
    for (const ep of endpoints) {{
      const m = ep.op['x-websocket'] ? 'ws' : ep.method;
      const id = makeId(ep.path, ep.method);
      html += `<div class="nav-item" data-id="${{id}}" onclick="scrollToEndpoint('${{id}}')" data-search="${{ep.path}} ${{ep.op.summary||''}} ${{tag}}">
        <span class="nav-method ${{m}}">${{m.toUpperCase()}}</span>
        <span class="nav-path">${{ep.path}}</span>
      </div>`;
    }}
    html += '</div>';
  }}
  nav.innerHTML = html;
}}

function renderEndpoints() {{
  const container = document.getElementById('endpointsContainer');
  const paths = spec.paths || {{}};
  const tags = spec.tags || [];
  const tagMap = {{}};
  
  for (const [path, methods] of Object.entries(paths)) {{
    for (const [method, op] of Object.entries(methods)) {{
      const opTags = op.tags || ['default'];
      const primaryTag = opTags[0] || 'default';
      if (!tagMap[primaryTag]) tagMap[primaryTag] = [];
      tagMap[primaryTag].push({{ path, method, op }});
    }}
  }}
  
  let html = '';
  for (const [tag, endpoints] of Object.entries(tagMap)) {{
    const tagInfo = tags.find(t => t.name === tag) || {{ name: tag, description: '' }};
    html += `<div class="tag-section" data-tag="${{tag}}">
      <div class="tag-header" onclick="toggleTag(this)">
        <i class="fas fa-chevron-down chevron"></i>
        <h2>${{tagInfo.name}}</h2>
        <span class="tag-badge">${{endpoints.length}}</span>
      </div>
      <div class="tag-content">`;
    
    for (const ep of endpoints) {{
      html += renderEndpoint(ep.path, ep.method, ep.op);
    }}
    
    html += '</div></div>';
  }}
  container.innerHTML = html;
}}

function renderEndpoint(path, method, op) {{
  const id = makeId(path, method);
  const m = op['x-websocket'] ? 'ws' : method;
  const params = op.parameters || [];
  const pathParams = params.filter(p => p.in === 'path');
  const queryParams = params.filter(p => p.in === 'query');
  const headerParams = params.filter(p => p.in === 'header');
  const hasBody = ['post','put','patch'].includes(method);
  const tier = op['x-performance-tier'];
  const isWs = op['x-websocket'];
  
  // Highlight path params
  let displayPath = escapeHtml(path).replace(/\\{{([^}}]+)\\}}/g, '<span class="param">{{$1}}</span>');
  
  let tierHtml = '';
  if (tier) tierHtml = `<span class="tier-badge ${{tier}}">${{tier}}</span>`;
  if (isWs) tierHtml = `<span class="ws-badge"><i class="fas fa-plug"></i> WebSocket</span>`;
  
  let tagsHtml = '';
  if (op.tags && op.tags.length > 1) {{
    tagsHtml = '<div class="ep-tags">' + op.tags.slice(1).map(t => `<span class="ep-tag">${{t}}</span>`).join('') + '</div>';
  }}
  
  let bodyHtml = '';
  
  // Parameters section
  let paramsHtml = '';
  const allParams = [...pathParams, ...queryParams, ...headerParams];
  if (allParams.length > 0) {{
    paramsHtml = `<div class="section-title"><i class="fas fa-sliders-h"></i> Parameters</div>
    <table class="params-table"><thead><tr><th>Name</th><th>In</th><th>Type</th><th>Value</th></tr></thead><tbody>`;
    for (const p of allParams) {{
      const req = p.required ? '<span class="param-required">*required</span>' : '';
      const type = p.schema?.type || 'string';
      const example = p.example || p.schema?.default || '';
      paramsHtml += `<tr>
        <td><span class="param-name">${{p.name}}</span>${{req}}</td>
        <td><span class="param-in">${{p.in}}</span></td>
        <td><span class="param-type">${{type}}</span></td>
        <td><input class="param-input" data-name="${{p.name}}" data-in="${{p.in}}" value="${{example}}" placeholder="Enter ${{p.name}}"></td>
      </tr>`;
    }}
    paramsHtml += '</tbody></table>';
  }}
  
  // Request body
  if (hasBody && op.requestBody) {{
    const schema = op.requestBody?.content?.['application/json']?.schema;
    const example = op.requestBody?.content?.['application/json']?.example;
    const defaultBody = example ? JSON.stringify(example, null, 2) : '{{\\n  \\n}}';
    bodyHtml = `<div class="section-title"><i class="fas fa-file-code"></i> Request Body</div>
    <textarea class="body-editor" id="body-${{id}}" placeholder="Enter JSON body...">${{defaultBody}}</textarea>`;
  }}
  
  // Try it section
  let tryHtml = '';
  if (!isWs) {{
    tryHtml = `<div class="try-bar">
      <button class="btn btn-primary" onclick="executeReq('${{id}}','${{path}}','${{method}}')"><i class="fas fa-play"></i> Execute</button>
      <button class="btn btn-outline" onclick="clearRes('${{id}}')"><i class="fas fa-eraser"></i> Clear</button>
    </div>
    <div class="response-area" id="res-${{id}}"></div>`;
  }} else {{
    tryHtml = `<div class="ep-desc">
      <strong>WebSocket Endpoint</strong><br>
      Connect using: <code>ws://host:port${{path}}</code><br>
      Use a WebSocket client to interact with this endpoint.
    </div>`;
  }}
  
  return `<div class="endpoint" id="ep-${{id}}" data-search="${{path}} ${{op.summary||''}} ${{(op.tags||[]).join(' ')}}">
    <div class="ep-header" onclick="toggleEndpoint('${{id}}')">
      <span class="method-badge ${{m}}">${{m.toUpperCase()}}</span>
      <span class="ep-path">${{displayPath}}</span>
      ${{tierHtml}}
      <span class="ep-summary">${{escapeHtml(op.summary || '')}}</span>
      ${{tagsHtml}}
      <i class="fas fa-chevron-down ep-expand"></i>
    </div>
    <div class="ep-body">
      ${{op.description ? `<div class="ep-desc">${{escapeHtml(op.description)}}</div>` : ''}}
      ${{paramsHtml}}
      ${{bodyHtml}}
      ${{tryHtml}}
    </div>
  </div>`;
}}

function makeId(path, method) {{
  return (method + '_' + path).replace(/[^a-zA-Z0-9]/g, '_');
}}

function escapeHtml(s) {{
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}}

function toggleEndpoint(id) {{
  const el = document.getElementById('ep-' + id);
  const wasExpanded = el.classList.contains('expanded');
  // Close all
  document.querySelectorAll('.endpoint.expanded').forEach(e => e.classList.remove('expanded'));
  if (!wasExpanded) {{
    el.classList.add('expanded');
    // Update sidebar active
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const navItem = document.querySelector(`.nav-item[data-id="${{id}}"]`);
    if (navItem) navItem.classList.add('active');
  }}
}}

function scrollToEndpoint(id) {{
  const el = document.getElementById('ep-' + id);
  if (el) {{
    el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    // Expand it
    document.querySelectorAll('.endpoint.expanded').forEach(e => e.classList.remove('expanded'));
    el.classList.add('expanded');
    // Update active
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const navItem = document.querySelector(`.nav-item[data-id="${{id}}"]`);
    if (navItem) navItem.classList.add('active');
  }}
  // Close sidebar on mobile
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('overlay').classList.remove('open');
}}

function toggleTag(header) {{
  header.classList.toggle('collapsed');
  header.nextElementSibling.classList.toggle('collapsed');
}}

function toggleSidebar() {{
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('overlay').classList.toggle('open');
}}

function searchEndpoints(query) {{
  const q = query.toLowerCase();
  // Filter sidebar
  document.querySelectorAll('.nav-item').forEach(item => {{
    const text = item.getAttribute('data-search').toLowerCase();
    item.style.display = text.includes(q) ? '' : 'none';
  }});
  // Filter endpoints
  document.querySelectorAll('.endpoint').forEach(ep => {{
    const text = ep.getAttribute('data-search').toLowerCase();
    ep.style.display = text.includes(q) ? '' : 'none';
  }});
  // Show/hide tag sections
  document.querySelectorAll('.tag-section').forEach(section => {{
    const visible = section.querySelectorAll('.endpoint:not([style*="display: none"])');
    section.style.display = visible.length > 0 ? '' : 'none';
  }});
}}

async function executeReq(id, pathTemplate, method) {{
  const epEl = document.getElementById('ep-' + id);
  const inputs = epEl.querySelectorAll('.param-input');
  const resEl = document.getElementById('res-' + id);
  
  let url = pathTemplate;
  let queryParts = [];
  let headers = {{'Accept': 'application/json'}};
  
  for (const input of inputs) {{
    const name = input.dataset.name;
    const inType = input.dataset.in;
    const val = input.value.trim();
    
    if (!val && input.closest('tr')?.querySelector('.param-required')) {{
      input.focus();
      input.style.borderColor = 'var(--error)';
      setTimeout(() => input.style.borderColor = '', 2000);
      return;
    }}
    
    if (inType === 'path') {{
      url = url.replace(`{{${{name}}}}`, encodeURIComponent(val));
    }} else if (inType === 'query' && val) {{
      queryParts.push(`${{encodeURIComponent(name)}}=${{encodeURIComponent(val)}}`);
    }} else if (inType === 'header' && val) {{
      headers[name] = val;
    }}
  }}
  
  if (queryParts.length) url += '?' + queryParts.join('&');
  
  let fetchOpts = {{ method: method.toUpperCase(), headers }};
  
  // Body for POST/PUT/PATCH
  const bodyEditor = document.getElementById('body-' + id);
  if (bodyEditor && bodyEditor.value.trim()) {{
    fetchOpts.body = bodyEditor.value.trim();
    headers['Content-Type'] = 'application/json';
  }}
  
  resEl.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-lg"></i> Sending request...</div>';
  
  try {{
    const t0 = performance.now();
    const resp = await fetch(url, fetchOpts);
    const t1 = performance.now();
    const time = Math.round(t1 - t0);
    
    const ct = resp.headers.get('content-type') || '';
    let body, isJson = false;
    if (ct.includes('json')) {{
      body = await resp.json();
      isJson = true;
    }} else {{
      const text = await resp.text();
      try {{ body = JSON.parse(text); isJson = true; }} catch {{ body = text; }}
    }}
    
    const statusClass = resp.status < 300 ? 's2xx' : resp.status < 500 ? 's4xx' : 's5xx';
    const statusIcon = resp.status < 300 ? 'check-circle' : resp.status < 500 ? 'exclamation-triangle' : 'times-circle';
    
    const formatted = isJson ? highlightJson(JSON.stringify(body, null, 2)) : escapeHtml(String(body));
    const rawText = isJson ? JSON.stringify(body, null, 2) : String(body);
    const size = new Blob([rawText]).size;
    
    resEl.innerHTML = `<div class="res-container">
      <div class="res-header ${{statusClass}}">
        <div class="res-status"><i class="fas fa-${{statusIcon}}"></i> ${{resp.status}} ${{resp.statusText}}</div>
        <span class="res-time">${{time}}ms</span>
      </div>
      <div class="res-body">
        <button class="res-copy" onclick="copyRes(this, '${{id}}')"><i class="fas fa-copy"></i> Copy</button>
        <pre class="res-code json" id="rescode-${{id}}">${{formatted}}</pre>
      </div>
      <div class="res-meta">
        <span>${{ct || 'unknown'}}</span>
        <span>${{size}} bytes</span>
      </div>
    </div>`;
  }} catch (err) {{
    resEl.innerHTML = `<div class="res-container">
      <div class="res-header serr"><div class="res-status"><i class="fas fa-exclamation-triangle"></i> Network Error</div></div>
      <div class="res-body"><pre class="res-code json">${{highlightJson(JSON.stringify({{error: err.message, type: err.name}}, null, 2))}}</pre></div>
    </div>`;
  }}
}}

function clearRes(id) {{
  document.getElementById('res-' + id).innerHTML = '';
}}

function copyRes(btn, id) {{
  const code = document.getElementById('rescode-' + id);
  if (code) {{
    navigator.clipboard.writeText(code.textContent).then(() => {{
      btn.innerHTML = '<i class="fas fa-check"></i> Copied';
      btn.classList.add('copied');
      setTimeout(() => {{ btn.innerHTML = '<i class="fas fa-copy"></i> Copy'; btn.classList.remove('copied'); }}, 2000);
    }});
  }}
}}

function highlightJson(json) {{
  return escapeHtml(json).replace(
    /("(\\\\u[a-zA-Z0-9]{{4}}|\\\\[^u]|[^\\\\"])*"(\\s*:)?|\\b(true|false|null)\\b|-?\\d+(?:\\.\\d*)?(?:[eE][+\\-]?\\d+)?)/g,
    function(m) {{
      let c = 'num';
      if (/^"/.test(m)) {{ c = /:$/.test(m) ? 'key' : 'str'; }}
      else if (/true|false/.test(m)) c = 'bool';
      else if (/null/.test(m)) c = 'null';
      return '<span class="' + c + '">' + m + '</span>';
    }}
  );
}}

window.addEventListener('DOMContentLoaded', init);
</script>
</body>
</html>'''


def _method_icon(method: str) -> str:
    """Get FontAwesome icon for HTTP method."""
    icons = {
        "get": "download",
        "post": "plus",
        "put": "pen",
        "delete": "trash",
        "patch": "wrench",
        "websocket": "plug",
    }
    return icons.get(method.lower(), "globe")


def generate_redoc_html(openapi_spec: dict) -> str:
    """Generate ReDoc documentation page."""
    spec_json = json.dumps(openapi_spec, default=str)
    title = openapi_spec.get("info", {}).get("title", "Sufast API")
    
    return f'''<!DOCTYPE html>
<html>
<head>
<title>{title} - ReDoc</title>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
<style>body{{margin:0;padding:0}}</style>
</head>
<body>
<div id="redoc-container"></div>
<script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
<script>
Redoc.init({spec_json}, {{
  theme: {{
    colors: {{ primary: {{ main: '#6366f1' }} }},
    typography: {{ fontFamily: 'Inter, sans-serif' }}
  }}
}}, document.getElementById('redoc-container'));
</script>
</body>
</html>'''
