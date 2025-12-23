from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

from mintcode_api.config import settings
from mintcode_api.db import Base, engine
from mintcode_api.routes_admin import router as admin_router
from mintcode_api.routes_dev import router as dev_router
from mintcode_api.routes_health import router as health_router
from mintcode_api.routes_redeem import router as redeem_router


def create_app() -> FastAPI:
    app = FastAPI(title="mintcode-api")

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/redeem-ui")

    @app.get("/admin-ui", response_class=HTMLResponse)
    def admin_ui() -> str:
        html = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>MintCode Admin</title>
    <style>
      :root {
        --bg: #ffffff; --bg-alt: #f8fafc; --text: #0f172a; --text-muted: #64748b;
        --border: #e2e8f0; --primary: #3b82f6; --primary-hover: #2563eb;
        --danger: #ef4444; --success: #22c55e;
        --sidebar-bg: #0f172a; --sidebar-text: #94a3b8; --sidebar-active: #ffffff;
        --sidebar-active-bg: #1e293b;
      }
      @media (prefers-color-scheme: dark) {
        :root {
          --bg: #0f172a; --bg-alt: #1e293b; --text: #f1f5f9; --text-muted: #94a3b8;
          --border: #334155; --primary: #60a5fa; --primary-hover: #3b82f6;
          --sidebar-bg: #020617; --sidebar-active-bg: #1e293b;
        }
      }
      * { box-sizing: border-box; outline: none; }
      body { margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: var(--bg); color: var(--text); height: 100vh; overflow: hidden; }
      
      /* Login View */
      #loginView {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: var(--bg-alt); display: flex; align-items: center; justify-content: center;
        z-index: 1000;
      }
      .login-card {
        background: var(--bg); padding: 40px; border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
        width: 100%; max-width: 400px; border: 1px solid var(--border);
      }
      .login-header { text-align: center; margin-bottom: 24px; }
      .login-header h1 { font-size: 24px; font-weight: 600; margin: 0; color: var(--text); }
      .login-header p { margin: 8px 0 0; color: var(--text-muted); font-size: 14px; }
      
      /* Dashboard Layout */
      #dashboardView { display: none; height: 100%; display: flex; }
      aside {
        width: 240px; background: var(--sidebar-bg); color: var(--sidebar-text);
        display: flex; flex-direction: column; flex-shrink: 0;
      }
      aside .brand {
        padding: 20px; font-size: 18px; font-weight: 700; color: #fff;
        border-bottom: 1px solid rgba(255,255,255,0.1);
      }
      aside nav { flex: 1; padding: 12px; overflow-y: auto; }
      .nav-item {
        display: block; padding: 10px 12px; margin-bottom: 4px;
        border-radius: 6px; cursor: pointer; transition: all .2s;
        font-size: 14px; font-weight: 500;
      }
      .nav-item:hover { background: rgba(255,255,255,0.05); color: #fff; }
      .nav-item.active { background: var(--sidebar-active-bg); color: var(--sidebar-active); }
      
      aside .user-info {
        padding: 16px; border-top: 1px solid rgba(255,255,255,0.1);
        font-size: 13px;
      }
      .logout-btn {
        background: none; border: none; color: var(--danger);
        padding: 0; cursor: pointer; font-size: 13px; margin-top: 8px;
      }

      main { flex: 1; overflow-y: auto; background: var(--bg-alt); padding: 24px; position: relative; }
      
      /* Components */
      .section { display: none; max-width: 1200px; margin: 0 auto; }
      .section.active { display: block; animation: fadeIn .2s; }
      @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: 0; } }
      
      h2 { font-size: 20px; font-weight: 600; margin: 0 0 20px; color: var(--text); }
      .card { background: var(--bg); border-radius: 8px; border: 1px solid var(--border); padding: 20px; margin-bottom: 20px; }
      .row { display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-end; }
      
      label { display: block; font-size: 13px; font-weight: 500; color: var(--text-muted); margin-bottom: 6px; }
      input, select, textarea {
        width: 100%; padding: 8px 12px; border-radius: 6px;
        border: 1px solid var(--border); background: var(--bg); color: var(--text);
        font-size: 14px; transition: border-color .2s;
      }
      input:focus, select:focus, textarea:focus { border-color: var(--primary); }
      
      button {
        padding: 8px 16px; border-radius: 6px; border: none;
        background: var(--primary); color: white; font-size: 14px; font-weight: 500;
        cursor: pointer; transition: opacity .2s;
      }
      button:hover { opacity: .9; }
      button.secondary { background: transparent; border: 1px solid var(--border); color: var(--text); }
      button.secondary:hover { background: var(--bg-alt); }
      
      table { width: 100%; border-collapse: collapse; font-size: 13px; }
      th { text-align: left; padding: 12px; border-bottom: 1px solid var(--border); color: var(--text-muted); font-weight: 500; }
      td { padding: 12px; border-bottom: 1px solid var(--border); color: var(--text); }
      tr:last-child td { border-bottom: none; }
      .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
      
      .status-badge {
        display: inline-block; padding: 2px 8px; border-radius: 12px;
        font-size: 12px; font-weight: 500;
      }
      .badge-PENDING { background: #e2e8f0; color: #475569; }
      .badge-WAITING_SMS { background: #dbeafe; color: #1e40af; }
      .badge-CODE_READY { background: #dcfce7; color: #166534; }
      .badge-DONE { background: #f0fdf4; color: #15803d; }
      .badge-FAILED { background: #fee2e2; color: #991b1b; }
      .badge-CANCELED { background: #f1f5f9; color: #64748b; }
      
      #globalErr {
        position: fixed; bottom: 20px; right: 20px;
        background: #fee2e2; color: #991b1b; padding: 12px 20px;
        border-radius: 8px; border: 1px solid #fecaca;
        display: none; z-index: 2000; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
      }
    </style>
  </head>
  <body>
    <!-- Login View -->
    <div id="loginView">
      <div class="login-card">
        <div class="login-header">
          <h1>MintCode Admin</h1>
          <p>请输入管理员密钥以继续</p>
        </div>
        <div style="margin-bottom: 20px;">
          <label>Admin Key</label>
          <input type="password" id="loginKey" placeholder="Enter your key..." />
        </div>
        <button onclick="doLogin()" style="width: 100%">进入后台</button>
        <div id="loginErr" style="color: var(--danger); font-size: 13px; margin-top: 12px; text-align: center; display: none;"></div>
      </div>
    </div>

    <!-- Dashboard View -->
    <div id="dashboardView" style="display: none;">
      <aside>
        <div class="brand">MintCode</div>
        <nav>
          <div class="nav-item active" onclick="nav('tasks')">兑换任务 (Redeem)</div>
          <div class="nav-item" onclick="nav('vouchers')">卡密管理 (Vouchers)</div>
          <div class="nav-item" onclick="nav('config')">配置 (Configuration)</div>
          <div class="nav-item" onclick="nav('test')">手动测试 (Manual)</div>
        </nav>
        <div class="user-info">
          <div style="margin-bottom: 4px; opacity: .8;">Admin Access</div>
          <button class="logout-btn" onclick="doLogout()">退出登录</button>
        </div>
      </aside>
      
      <main>
        <!-- Tasks Section -->
        <div id="view-tasks" class="section active">
          <div class="row" style="margin-bottom: 20px; justify-content: space-between;">
            <h2>兑换任务列表</h2>
            <div class="row" style="gap: 8px;">
              <select id="taskStatus" style="width: 120px" onchange="loadTasks()">
                <option value="">全部状态</option>
                <option value="PENDING">PENDING</option>
                <option value="WAITING_SMS">WAITING_SMS</option>
                <option value="PROCESSING">PROCESSING</option>
                <option value="CODE_READY">CODE_READY</option>
                <option value="DONE">DONE</option>
                <option value="FAILED">FAILED</option>
                <option value="CANCELED">CANCELED</option>
              </select>
              <input id="taskSku" placeholder="SKU 过滤" style="width: 120px" />
              <button onclick="loadTasks()">刷新</button>
              <div style="font-size: 12px; display: flex; align-items: center; gap: 4px;">
                <input type="checkbox" id="autoRefresh" checked style="width: auto;" /> 自动刷新
              </div>
            </div>
          </div>
          
          <div class="card" style="padding: 0; overflow: hidden;">
            <div style="overflow-x: auto;">
              <table style="min-width: 1000px;">
                <thead>
                  <tr>
                    <th style="width: 60px">ID</th>
                    <th>SKU</th>
                    <th>Status</th>
                    <th>Phone</th>
                    <th>Code</th>
                    <th>Voucher</th>
                    <th>Updated</th>
                    <th style="width: 120px">Actions</th>
                  </tr>
                </thead>
                <tbody id="tasksBody"></tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Vouchers Section -->
        <div id="view-vouchers" class="section">
          <h2>卡密生成与管理</h2>
          
          <div class="card">
            <h3 style="margin-top: 0">批量生成</h3>
            <div class="row">
              <div style="flex: 1; min-width: 120px;">
                <label>SKU</label>
                <input id="genSku" placeholder="default" />
              </div>
              <div style="width: 100px;">
                <label>数量</label>
                <input id="genCount" type="number" value="10" />
              </div>
              <div style="width: 100px;">
                <label>长度</label>
                <input id="genLen" type="number" value="32" />
              </div>
              <div style="flex: 1; min-width: 120px;">
                <label>标签 (可选)</label>
                <input id="genLabel" placeholder="" />
              </div>
              <div style="width: 100px;">
                <label>&nbsp;</label>
                <button onclick="doGenerate()" style="width: 100%">生成</button>
              </div>
            </div>
            <div style="margin-top: 16px;">
              <label>生成结果</label>
              <textarea id="genOut" rows="5" spellcheck="false" placeholder="生成的卡密将显示在这里..."></textarea>
            </div>
          </div>

          <div class="card">
            <div class="row" style="justify-content: space-between; margin-bottom: 16px;">
              <h3 style="margin: 0">生成批次记录</h3>
              <div class="row" style="gap: 8px;">
                <input id="batchSkuFilter" placeholder="SKU 过滤" style="width: 120px" />
                <button onclick="loadBatches()" class="secondary">刷新列表</button>
              </div>
            </div>
            <table style="margin-bottom: 16px;">
              <thead><tr><th>ID</th><th>SKU</th><th>Count</th><th>Time</th><th>Action</th></tr></thead>
              <tbody id="batchesBody"></tbody>
            </table>
            <label>导出结果</label>
            <textarea id="exportOut" rows="5" spellcheck="false" placeholder="导出的卡密将显示在这里..."></textarea>
          </div>
        </div>

        <!-- Config Section -->
        <div id="view-config" class="section">
          <h2>供应商配置 (SKU Config)</h2>
          
          <div class="card">
            <h3 style="margin-top: 0">SKU 设置 (5sim)</h3>
            <div class="row" style="margin-bottom: 16px;">
              <div style="flex: 2;">
                <label>目标 SKU ID</label>
                <div class="row" style="gap: 0;">
                  <input id="cfgSku" class="mono" placeholder="e.g. tg1" style="border-top-right-radius: 0; border-bottom-right-radius: 0;" />
                  <button onclick="loadSkuConfig()" style="border-top-left-radius: 0; border-bottom-left-radius: 0;">加载配置</button>
                </div>
              </div>
              <div style="flex: 3;">
                 <label>历史记录</label>
                 <select id="cfgHist"></select>
              </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 20px;">
              <div>
                <label>Country</label>
                <input id="cfgCountry" class="mono" placeholder="e.g. russia / any" />
              </div>
              <div>
                <label>Operator</label>
                <input id="cfgOperator" class="mono" placeholder="e.g. any" />
              </div>
              <div>
                <label>Product</label>
                <input id="cfgProduct" class="mono" placeholder="e.g. telegram" />
              </div>
              <div>
                <label>Category</label>
                <select id="cfgCategory">
                  <option value="activation">activation</option>
                  <option value="hosting">hosting</option>
                </select>
              </div>
              <div>
                <label>Poll Interval (s)</label>
                <input id="cfgPoll" type="number" value="5" min="1" />
              </div>
            </div>
            
            <div class="row" style="margin-bottom: 20px;">
              <div style="display: flex; gap: 8px; align-items: center;">
                <input id="cfgReuse" type="checkbox" style="width: auto;" /> <label style="margin:0; display:inline;">Reuse Number</label>
              </div>
              <div style="display: flex; gap: 8px; align-items: center; margin-left: 16px;">
                <input id="cfgVoice" type="checkbox" style="width: auto;" /> <label style="margin:0; display:inline;">Voice SMS</label>
              </div>
            </div>

            <div class="row">
               <button onclick="saveSkuConfig()">保存配置</button>
               <span id="cfgOut" class="mono" style="font-size: 13px; color: var(--text-muted); margin-left: 10px;"></span>
            </div>
          </div>

          <div class="card">
            <h3 style="margin-top: 0">推荐配置 (Auto-collected)</h3>
            <div class="row" style="margin-bottom: 12px;">
              <input id="featSku" placeholder="SKU (Optional)" style="width: 200px;" />
              <button onclick="loadFeatured()" class="secondary">加载推荐</button>
            </div>
            <div style="overflow-x: auto;">
              <table>
                <thead>
                  <tr>
                    <th>Success</th><th>Avg Cost</th><th>Last</th><th>Details</th><th>Actions</th>
                  </tr>
                </thead>
                <tbody id="featuredBody"></tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Manual Test Section -->
        <div id="view-test" class="section">
          <h2>手动测试</h2>
          <div class="card">
            <label>输入卡密进行测试 (Create Task)</label>
            <div class="row">
              <input id="redeemCode" class="mono" placeholder="paste voucher code here" style="flex: 1;" />
              <button onclick="doRedeem()">执行兑换</button>
            </div>
            <pre id="redeemOut" style="background: var(--bg-alt); padding: 12px; border-radius: 6px; margin-top: 16px; min-height: 60px; font-size: 13px;"></pre>
            <div id="redeemActions" class="row" style="margin-top: 12px;"></div>
          </div>
        </div>
      </main>
    </div>
    
    <div id="globalErr"></div>

    <script>
      const $ = (id) => document.getElementById(id);
      const storageKey = 'mintcode_admin_key';
      
      // --- Auth & Nav ---
      function init() {
        const key = localStorage.getItem(storageKey);
        if (key) {
          showDashboard();
        } else {
          showLogin();
        }
        
        // Auto refresh setup
        setInterval(() => {
          if ($('dashboardView').style.display !== 'none' && $('autoRefresh').checked) {
             const activeNav = document.querySelector('.nav-item.active').innerText;
             if (activeNav.includes('Redeem') && document.getElementById('view-tasks').classList.contains('active')) {
               loadTasks(true);
             }
          }
        }, 2000);
      }
      
      function showLogin() {
        $('loginView').style.display = 'flex';
        $('dashboardView').style.display = 'none';
        $('loginKey').value = '';
        $('loginKey').focus();
      }
      
      function showDashboard() {
        $('loginView').style.display = 'none';
        $('dashboardView').style.display = 'flex';
        loadTasks();
      }
      
      async function doLogin() {
        const key = $('loginKey').value.trim();
        if (!key) return;
        
        // Verify key by making a lightweight call
        localStorage.setItem(storageKey, key);
        try {
          await apiFetch('/admin/batches?limit=1');
          showDashboard();
        } catch (e) {
          $('loginErr').style.display = 'block';
          $('loginErr').innerText = '登录失败: Key 无效';
          localStorage.removeItem(storageKey);
        }
      }
      
      function doLogout() {
        localStorage.removeItem(storageKey);
        showLogin();
      }
      
      function nav(view) {
        document.querySelectorAll('.section').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
        
        $('view-' + view).classList.add('active');
        
        // Highlight nav item
        const map = { 'tasks': 0, 'vouchers': 1, 'config': 2, 'test': 3 };
        document.querySelectorAll('.nav-item')[map[view]].classList.add('active');
        
        if (view === 'tasks') loadTasks();
        if (view === 'vouchers') loadBatches();
        if (view === 'config') { /* lazy load */ }
      }

      function notify(msg, isErr=false) {
        const el = $('globalErr');
        el.innerText = msg;
        el.style.backgroundColor = isErr ? '#fee2e2' : '#dcfce7';
        el.style.color = isErr ? '#991b1b' : '#166534';
        el.style.borderColor = isErr ? '#fecaca' : '#bbf7d0';
        el.style.display = 'block';
        setTimeout(() => { el.style.display = 'none'; }, 3000);
      }

      async function apiFetch(path, opts={}) {
        const key = localStorage.getItem(storageKey);
        const headers = new Headers(opts.headers || {});
        if (key) headers.set('X-Admin-Key', key);
        
        try {
          const res = await fetch(path, { ...opts, headers });
          if (res.status === 401 || res.status === 403) {
            doLogout();
            throw new Error('Unauthorized');
          }
          if (!res.ok) {
            const txt = await res.text();
            throw new Error(txt || res.statusText);
          }
          return res;
        } catch (e) {
          if (e.message !== 'Unauthorized') notify(e.message, true);
          throw e;
        }
      }

      // --- Tasks ---
      async function loadTasks(silent=false) {
        if (!silent) $('tasksBody').innerHTML = '<tr><td colspan="8" style="text-align:center">Loading...</td></tr>';
        const status = $('taskStatus').value;
        const sku = ($('taskSku').value || '').trim();
        const qs = new URLSearchParams();
        if (status) qs.set('status', status);
        if (sku) qs.set('sku_id', sku);
        qs.set('limit', '50');
        
        try {
          const res = await apiFetch('/admin/redeem/tasks?' + qs.toString());
          const data = await res.json();
          renderTasks(data);
        } catch (e) {
          // handled by apiFetch
        }
      }
      
      function renderTasks(data) {
        const body = $('tasksBody');
        body.innerHTML = '';
        if (!data || data.length === 0) {
          body.innerHTML = '<tr><td colspan="8" style="text-align:center; color:var(--text-muted)">无数据</td></tr>';
          return;
        }
        
        data.forEach(t => {
          const tr = document.createElement('tr');
          const statusClass = `badge-${t.status}`;
          const updated = (t.updated_at || '').replace('T', ' ').split('.')[0];
          
          let actionsHtml = '';
          if (['PENDING','WAITING_SMS','PROCESSING','FAILED'].includes(t.status)) {
             actionsHtml += `<button class="secondary" style="padding:2px 6px; font-size:12px; margin-right:4px" onclick="taskAction(${t.id}, 'cancel', '${t.voucher_code}')">取消</button>`;
          }
          if (t.status === 'CODE_READY') {
             actionsHtml += `<button style="padding:2px 6px; font-size:12px;" onclick="taskAction(${t.id}, 'complete', '${t.voucher_code}')">完成</button>`;
          }
          if (t.status === 'CANCELED') {
             actionsHtml += `<button class="secondary" style="padding:2px 6px; font-size:12px;" onclick="taskAction(${t.id}, 'next', '${t.voucher_code}')">重试</button>`;
          }

          tr.innerHTML = `
            <td class="mono">${t.id}</td>
            <td class="mono">${t.sku_id}</td>
            <td><span class="status-badge ${statusClass}">${t.status}</span></td>
            <td class="mono">${t.phone || '-'}</td>
            <td class="mono" style="color:var(--primary); font-weight:700">${t.result_code || '-'}</td>
            <td class="mono" title="${t.voucher_code}">${t.voucher_code.slice(0,8)}...</td>
            <td class="mono" style="font-size:12px">${updated}</td>
            <td>${actionsHtml}</td>
          `;
          body.appendChild(tr);
        });
      }
      
      async function taskAction(id, action, code) {
        try {
          await apiFetch(`/redeem/${id}/${action}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({code})
          });
          loadTasks(true);
          notify(`Action ${action} success`);
        } catch (e) { }
      }

      // --- Vouchers ---
      async function doGenerate() {
        const btn = document.querySelector('#view-vouchers button');
        btn.disabled = true; btn.innerText = 'Generating...';
        try {
           const payload = {
             sku_id: ($('genSku').value || '').trim() || null,
             count: Number($('genCount').value || 10),
             length: Number($('genLen').value || 32),
             label: ($('genLabel').value || '').trim() || null
           };
           const res = await apiFetch('/admin/vouchers/generate', {
             method: 'POST',
             headers: {'Content-Type': 'application/json'},
             body: JSON.stringify(payload)
           });
           $('genOut').value = await res.text();
           loadBatches();
           notify('Generation complete');
        } finally {
           btn.disabled = false; btn.innerText = '生成';
        }
      }
      
      async function loadBatches() {
         const qs = new URLSearchParams({limit: '20'});
         if ($('batchSkuFilter').value) qs.set('sku_id', $('batchSkuFilter').value);
         
         const res = await apiFetch('/admin/batches?' + qs.toString());
         const data = await res.json();
         const tbody = $('batchesBody');
         tbody.innerHTML = '';
         data.forEach(b => {
           const tr = document.createElement('tr');
           tr.innerHTML = `
             <td class="mono">${b.id}</td>
             <td class="mono">${b.sku_id}</td>
             <td>${b.count}</td>
             <td class="mono">${(b.created_at||'').split('T')[0]}</td>
             <td><button class="secondary" style="padding:2px 8px" onclick="exportBatch(${b.id})">Export</button></td>
           `;
           tbody.appendChild(tr);
         });
      }
      
      async function exportBatch(id) {
         const res = await apiFetch('/admin/vouchers/export/batch/' + id);
         $('exportOut').value = await res.text();
      }

      // --- Config ---
      async function loadSkuConfig() {
         const sku = $('cfgSku').value.trim();
         if(!sku) return notify('Please enter SKU', true);
         
         const res = await apiFetch('/admin/sku/' + encodeURIComponent(sku) + '/provider-config');
         const d = await res.json();
         $('cfgCountry').value = d.country || '';
         $('cfgOperator').value = d.operator || '';
         $('cfgProduct').value = d.product || '';
         $('cfgCategory').value = d.category || 'activation';
         $('cfgPoll').value = d.poll_interval_seconds || 5;
         $('cfgReuse').checked = !!d.reuse;
         $('cfgVoice').checked = !!d.voice;
         
         loadConfigHistory(sku);
         notify('Config loaded');
      }
      
      async function saveSkuConfig() {
         const sku = $('cfgSku').value.trim();
         if(!sku) return;
         
         const payload = {
           provider: 'fivesim',
           country: $('cfgCountry').value.trim(),
           operator: $('cfgOperator').value.trim() || 'any',
           product: $('cfgProduct').value.trim(),
           category: $('cfgCategory').value,
           poll_interval_seconds: Number($('cfgPoll').value),
           reuse: $('cfgReuse').checked,
           voice: $('cfgVoice').checked
         };
         
         await apiFetch('/admin/sku/' + encodeURIComponent(sku) + '/provider-config', {
           method: 'PUT',
           headers: {'Content-Type': 'application/json'},
           body: JSON.stringify(payload)
         });
         notify('Config saved');
         loadConfigHistory(sku);
      }
      
      async function loadConfigHistory(sku) {
         const res = await apiFetch('/admin/sku/' + encodeURIComponent(sku) + '/provider-config/history?limit=20');
         const data = await res.json();
         const sel = $('cfgHist');
         sel.innerHTML = '<option value="">Select from history...</option>';
         data.forEach((h, i) => {
           const opt = document.createElement('option');
           opt.text = `${h.created_at.split('T')[0]} - ${h.country}/${h.operator}`;
           // We could store full data in memory, but for simplicity just show log
           sel.appendChild(opt);
         });
      }
      
      async function loadFeatured() {
        const sku = $('featSku').value.trim() || $('cfgSku').value.trim();
        if(!sku) return notify('Enter SKU for featured', true);
        
        const res = await apiFetch(`/admin/sku/${encodeURIComponent(sku)}/provider-config/successes?limit=20`);
        const data = await res.json();
        const tbody = $('featuredBody');
        tbody.innerHTML = '';
        data.forEach(f => {
           const tr = document.createElement('tr');
           tr.innerHTML = `
             <td>${f.success_count}</td>
             <td>${Number(f.avg_success_cost).toFixed(2)}</td>
             <td class="mono">${(f.last_success_at||'').split('T')[0]}</td>
             <td class="mono">${f.country}/${f.operator}</td>
             <td><button class="secondary" style="padding:2px 8px" onclick="applyFeatured('${f.country}','${f.operator}','${f.product}')">Apply</button></td>
           `;
           tbody.appendChild(tr);
        });
      }
      
      function applyFeatured(c, o, p) {
         $('cfgCountry').value = c;
         $('cfgOperator').value = o;
         $('cfgProduct').value = p;
         notify('Applied to form (Click Save to commit)');
      }

      // --- Manual ---
      async function doRedeem() {
         const code = $('redeemCode').value.trim();
         if(!code) return notify('Input code', true);
         $('redeemOut').innerText = 'Starting...';
         const res = await apiFetch('/redeem', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({code})
         });
         const d = await res.json();
         $('redeemOut').innerText = JSON.stringify(d, null, 2);
         loadTasks(true);
      }

      // Boot
      init();
    </script>
  </body>
</html>"""
        return html.replace("__REDEEM_WAIT_SECONDS__", str(int(settings.redeem_wait_seconds)))

    @app.get("/redeem-ui", response_class=HTMLResponse)
    def redeem_ui() -> str:
        redeem_html = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
  <title>MintCode 兑换</title>
  <style>
    :root {
      --primary: #6366f1;
      --primary-hover: #4f46e5;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --text: #1e293b;
      --text-muted: #64748b;
      --border: #e2e8f0;
      --radius: 12px;
    }
    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #0f172a;
        --card-bg: #1e293b;
        --text: #f1f5f9;
        --text-muted: #94a3b8;
        --border: #334155;
      }
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      justify-content: center;
      align-items: flex-start;
      padding: 24px 16px;
    }
    .container {
      width: 100%;
      max-width: 420px;
    }
    .card {
      background: var(--card-bg);
      border-radius: var(--radius);
      box-shadow: 0 4px 6px -1px rgba(0,0,0,.1), 0 2px 4px -2px rgba(0,0,0,.1);
      padding: 24px;
      margin-bottom: 16px;
    }
    .logo {
      text-align: center;
      margin-bottom: 24px;
    }
    .logo h1 {
      font-size: 24px;
      font-weight: 700;
      background: linear-gradient(135deg, var(--primary), #a855f7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .logo p {
      color: var(--text-muted);
      font-size: 14px;
      margin-top: 4px;
    }
    .input-group {
      margin-bottom: 16px;
    }
    .input-group label {
      display: block;
      font-size: 14px;
      font-weight: 500;
      margin-bottom: 8px;
      color: var(--text);
    }
    .input-group input {
      width: 100%;
      padding: 12px 16px;
      font-size: 16px;
      border: 2px solid var(--border);
      border-radius: var(--radius);
      background: var(--bg);
      color: var(--text);
      transition: border-color .2s, box-shadow .2s;
      outline: none;
    }
    .input-group input:focus {
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(99,102,241,.15);
    }
    .input-group input::placeholder {
      color: var(--text-muted);
    }
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 12px 24px;
      font-size: 16px;
      font-weight: 600;
      border: none;
      border-radius: var(--radius);
      cursor: pointer;
      transition: all .2s;
      width: 100%;
    }
    .btn-primary {
      background: var(--primary);
      color: white;
    }
    .btn-primary:hover:not(:disabled) {
      background: var(--primary-hover);
      transform: translateY(-1px);
    }
    .btn-primary:disabled {
      opacity: .6;
      cursor: not-allowed;
    }
    .btn-outline {
      background: transparent;
      border: 2px solid var(--border);
      color: var(--text);
    }
    .btn-outline:hover {
      border-color: var(--primary);
      color: var(--primary);
    }
    .btn-danger {
      background: var(--danger);
      color: white;
    }
    .btn-danger:hover {
      background: #dc2626;
    }
    .btn-success {
      background: var(--success);
      color: white;
    }
    .btn-success:hover {
      background: #059669;
    }
    .btn-sm {
      padding: 8px 16px;
      font-size: 14px;
    }
    .status-card {
      display: none;
    }
    .status-card.active {
      display: block;
    }
    .steps {
      display: flex;
      justify-content: space-between;
      margin-bottom: 24px;
      position: relative;
    }
    .steps::before {
      content: '';
      position: absolute;
      top: 16px;
      left: 24px;
      right: 24px;
      height: 2px;
      background: var(--border);
      z-index: 0;
    }
    .step {
      display: flex;
      flex-direction: column;
      align-items: center;
      position: relative;
      z-index: 1;
      flex: 1;
    }
    .step-dot {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: var(--border);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      font-weight: 600;
      color: var(--text-muted);
      transition: all .3s;
    }
    .step.active .step-dot {
      background: var(--primary);
      color: white;
      box-shadow: 0 0 0 4px rgba(99,102,241,.2);
    }
    .step.done .step-dot {
      background: var(--success);
      color: white;
    }
    .step.error .step-dot {
      background: var(--danger);
      color: white;
    }
    .step-label {
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 8px;
      text-align: center;
    }
    .info-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 0;
      border-bottom: 1px solid var(--border);
    }
    .info-row:last-child {
      border-bottom: none;
    }
    .info-label {
      font-size: 14px;
      color: var(--text-muted);
    }
    .info-value {
      font-size: 14px;
      font-weight: 500;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .copy-btn {
      padding: 4px 8px;
      font-size: 12px;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      cursor: pointer;
      color: var(--text-muted);
      transition: all .2s;
    }
    .copy-btn:hover {
      border-color: var(--primary);
      color: var(--primary);
    }
    .copy-btn.copied {
      background: var(--success);
      border-color: var(--success);
      color: white;
    }
    .code-display {
      background: linear-gradient(135deg, var(--primary), #a855f7);
      color: white;
      padding: 20px;
      border-radius: var(--radius);
      text-align: center;
      margin: 16px 0;
    }
    .code-display .label {
      font-size: 12px;
      opacity: .8;
      margin-bottom: 8px;
    }
    .code-display .code {
      font-size: 32px;
      font-weight: 700;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      letter-spacing: 4px;
    }
    .timer {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      background: var(--bg);
      border-radius: 20px;
      font-size: 13px;
      color: var(--text-muted);
    }
    .timer.warning {
      background: rgba(245,158,11,.1);
      color: var(--warning);
    }
    .timer.danger {
      background: rgba(239,68,68,.1);
      color: var(--danger);
    }
    .status-badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
    }
    .status-badge.pending { background: rgba(99,102,241,.1); color: var(--primary); }
    .status-badge.processing { background: rgba(245,158,11,.1); color: var(--warning); }
    .status-badge.waiting { background: rgba(59,130,246,.1); color: #3b82f6; }
    .status-badge.ready { background: rgba(16,185,129,.1); color: var(--success); }
    .status-badge.done { background: rgba(16,185,129,.1); color: var(--success); }
    .status-badge.failed { background: rgba(239,68,68,.1); color: var(--danger); }
    .status-badge.canceled { background: rgba(107,114,128,.1); color: #6b7280; }
    .actions {
      display: flex;
      gap: 12px;
      margin-top: 16px;
    }
    .actions .btn {
      flex: 1;
    }
    .error-msg {
      background: rgba(239,68,68,.1);
      color: var(--danger);
      padding: 12px 16px;
      border-radius: var(--radius);
      font-size: 14px;
      margin-top: 16px;
      display: none;
    }
    .error-msg.show {
      display: block;
    }
    .hint {
      font-size: 13px;
      color: var(--text-muted);
      text-align: center;
      margin-top: 16px;
      line-height: 1.6;
    }
    .phone-highlight {
      background: #f8fafc;
      border: 2px dashed var(--primary);
      padding: 24px;
      border-radius: var(--radius);
      text-align: center;
      margin: 24px 0;
      position: relative;
    }
    .phone-highlight .label {
      font-size: 13px;
      color: var(--text-muted);
      margin-bottom: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .phone-highlight .phone {
      font-size: 36px;
      font-weight: 800;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      color: var(--primary);
      text-shadow: 0 2px 0 rgba(0,0,0,0.05);
      letter-spacing: 1px;
      margin-bottom: 16px;
    }
    .phone-highlight .copy-btn {
      background: var(--primary);
      color: white;
      border: none;
      padding: 8px 16px;
      font-size: 13px;
      font-weight: 500;
      box-shadow: 0 2px 4px rgba(99,102,241,0.2);
    }
    .phone-highlight .copy-btn:hover {
      background: var(--primary-hover);
      transform: translateY(-1px);
    }
    .phone-highlight .copy-btn.copied {
      background: var(--success);
    }
    .spinner {
      width: 20px;
      height: 20px;
      border: 2px solid rgba(255,255,255,.3);
      border-top-color: white;
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    .fade-in {
      animation: fadeIn .3s ease;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .tabs {
      display: flex;
      border-bottom: 1px solid var(--border);
      margin-bottom: 20px;
    }
    .tab {
      flex: 1;
      padding: 12px;
      text-align: center;
      cursor: pointer;
      font-size: 14px;
      font-weight: 500;
      color: var(--text-muted);
      border-bottom: 2px solid transparent;
      transition: all .2s;
    }
    .tab:hover {
      color: var(--primary);
    }
    .tab.active {
      color: var(--primary);
      border-bottom-color: var(--primary);
    }
    .tab-content {
      display: none;
    }
    .tab-content.active {
      display: block;
    }
    .query-result {
      background: var(--bg);
      border-radius: var(--radius);
      padding: 16px;
      margin-top: 16px;
    }
    .query-result .result-row {
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      border-bottom: 1px solid var(--border);
    }
    .query-result .result-row:last-child {
      border-bottom: none;
    }
    .query-result .result-label {
      color: var(--text-muted);
      font-size: 13px;
    }
    .query-result .result-value {
      font-weight: 500;
      font-size: 13px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="logo">
      <h1>MintCode</h1>
      <p>短信验证码兑换服务</p>
    </div>

    <!-- 输入卡片 -->
    <div class="card" id="inputCard">
      <div class="tabs">
        <div class="tab active" onclick="switchTab('redeem')">兑换验证码</div>
        <div class="tab" onclick="switchTab('query')">查询订单</div>
      </div>

      <div id="redeemTab" class="tab-content active">
        <div class="input-group">
          <label for="voucher">兑换码</label>
          <input type="text" id="voucher" placeholder="请输入您的兑换码" autocomplete="off" spellcheck="false" />
        </div>
        <button class="btn btn-primary" id="startBtn" onclick="startRedeem()">
          开始兑换
        </button>
        <div class="error-msg" id="inputError"></div>
      </div>

      <div id="queryTab" class="tab-content">
        <div class="input-group">
          <label for="queryVoucher">卡密</label>
          <input type="text" id="queryVoucher" placeholder="请输入要查询的卡密" autocomplete="off" spellcheck="false" />
        </div>
        <button class="btn btn-primary" id="queryBtn" onclick="queryOrder()">
          查询订单
        </button>
        <div class="error-msg" id="queryError"></div>
        <div id="queryResult" style="display:none;"></div>
      </div>
    </div>

    <!-- 状态卡片 -->
    <div class="card status-card" id="statusCard">
      <div class="steps">
        <div class="step" id="step1">
          <div class="step-dot">1</div>
          <div class="step-label">提交</div>
        </div>
        <div class="step" id="step2">
          <div class="step-dot">2</div>
          <div class="step-label">获取号码</div>
        </div>
        <div class="step" id="step3">
          <div class="step-dot">3</div>
          <div class="step-label">等待短信</div>
        </div>
        <div class="step" id="step4">
          <div class="step-dot">4</div>
          <div class="step-label">完成</div>
        </div>
      </div>

      <div class="info-row">
        <span class="info-label">状态</span>
        <span class="status-badge pending" id="statusBadge">处理中</span>
      </div>

      <div class="phone-highlight" id="phoneSection" style="display:none;">
        <div class="label">请使用此号码在目标平台触发短信</div>
        <div class="phone" id="phoneDisplay">-</div>
        <button class="copy-btn" style="margin-top:12px;" onclick="copyText('phoneDisplay', this)">复制号码</button>
      </div>

      <div class="code-display" id="codeSection" style="display:none;">
        <div class="label">验证码已到达</div>
        <div class="code" id="codeDisplay">-</div>
        <button class="copy-btn" style="margin-top:12px;background:rgba(255,255,255,.2);border-color:rgba(255,255,255,.3);color:white;" onclick="copyText('codeDisplay', this)">复制验证码</button>
      </div>

      <div class="info-row" id="timerRow" style="display:none;">
        <span class="info-label">剩余时间</span>
        <span class="timer" id="timerDisplay">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
          <span id="timerValue">--:--</span>
        </span>
      </div>

      <div class="info-row" id="countryRow" style="display:none;">
        <span class="info-label">国家/地区</span>
        <span class="info-value" id="countryDisplay">-</span>
      </div>

      <div class="error-msg" id="statusError"></div>

      <div class="actions" id="actions"></div>

      <div class="hint" id="hintText"></div>
    </div>

  </div>

  <script>
    const redeemWaitSeconds = __REDEEM_WAIT_SECONDS__;
    let currentTaskId = null;
    let currentVoucher = '';
    let pollTimer = null;
    let countdownTimer = null;
    let expiresAt = null;
    let providerStartedAt = null;

    function switchTab(tab) {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      if (tab === 'redeem') {
        document.querySelector('.tabs .tab:first-child').classList.add('active');
        document.getElementById('redeemTab').classList.add('active');
      } else {
        document.querySelector('.tabs .tab:last-child').classList.add('active');
        document.getElementById('queryTab').classList.add('active');
      }
      hideError('inputError');
      hideError('queryError');
      document.getElementById('queryResult').style.display = 'none';
    }

    async function queryOrder() {
      const code = document.getElementById('queryVoucher').value.trim();
      if (!code) {
        showError('queryError', '请输入卡密');
        return;
      }
      hideError('queryError');

      const btn = document.getElementById('queryBtn');
      btn.disabled = true;
      btn.innerHTML = '<div class="spinner"></div> 查询中...';

      try {
        const res = await fetch('/redeem/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code: code })
        });
        const data = await res.json();
        if (!res.ok) {
          const errMap = {
            'invalid_code': '卡密无效',
            'no_order': '该卡密暂无订单记录'
          };
          showError('queryError', errMap[data.detail] || data.detail || '查询失败');
          document.getElementById('queryResult').style.display = 'none';
          btn.disabled = false;
          btn.innerHTML = '查询订单';
          return;
        }

        renderQueryResult(data);
        btn.disabled = false;
        btn.innerHTML = '查询订单';
      } catch (e) {
        showError('queryError', '网络错误，请重试');
        btn.disabled = false;
        btn.innerHTML = '查询订单';
      }
    }

    function renderQueryResult(data) {
      const statusMap = {
        'PENDING': '排队中',
        'PROCESSING': '处理中',
        'WAITING_SMS': '等待短信',
        'CODE_READY': '验证码已到达',
        'DONE': '已完成',
        'FAILED': '失败',
        'CANCELED': '已取消'
      };
      let html = '<div class="query-result">';
      html += '<div class="result-row"><span class="result-label">状态</span><span class="result-value">' + (statusMap[data.status] || data.status) + '</span></div>';
      if (data.phone) {
        html += '<div class="result-row"><span class="result-label">手机号</span><span class="result-value">' + data.phone + '</span></div>';
      }
      if (data.country) {
        html += '<div class="result-row"><span class="result-label">国家/地区</span><span class="result-value">' + formatCountry(data.country) + '</span></div>';
      }
      if (data.result_code) {
        html += '<div class="result-row"><span class="result-label">验证码</span><span class="result-value" style="font-family:monospace;font-size:16px;color:var(--primary);">' + data.result_code + '</span></div>';
      }
      html += '</div>';
      document.getElementById('queryResult').innerHTML = html;
      document.getElementById('queryResult').style.display = 'block';
    }

    function formatCountry(raw) {
      if (!raw) return '';
      const key = String(raw).trim().toLowerCase();
      const map = {
        'england': { flag: '🇬🇧', en: 'England', zh: '英国' },
        'united kingdom': { flag: '🇬🇧', en: 'United Kingdom', zh: '英国' },
        'great britain': { flag: '🇬🇧', en: 'Great Britain', zh: '英国' },
        'usa': { flag: '🇺🇸', en: 'United States', zh: '美国' },
        'united states': { flag: '🇺🇸', en: 'United States', zh: '美国' },
        'russia': { flag: '🇷🇺', en: 'Russia', zh: '俄罗斯' },
        'ukraine': { flag: '🇺🇦', en: 'Ukraine', zh: '乌克兰' },
        'france': { flag: '🇫🇷', en: 'France', zh: '法国' },
        'germany': { flag: '🇩🇪', en: 'Germany', zh: '德国' },
        'italy': { flag: '🇮🇹', en: 'Italy', zh: '意大利' },
        'spain': { flag: '🇪🇸', en: 'Spain', zh: '西班牙' },
        'poland': { flag: '🇵🇱', en: 'Poland', zh: '波兰' },
        'netherlands': { flag: '🇳🇱', en: 'Netherlands', zh: '荷兰' },
        'sweden': { flag: '🇸🇪', en: 'Sweden', zh: '瑞典' },
        'norway': { flag: '🇳🇴', en: 'Norway', zh: '挪威' },
        'finland': { flag: '🇫🇮', en: 'Finland', zh: '芬兰' },
        'denmark': { flag: '🇩🇰', en: 'Denmark', zh: '丹麦' },
        'australia': { flag: '🇦🇺', en: 'Australia', zh: '澳大利亚' },
        'canada': { flag: '🇨🇦', en: 'Canada', zh: '加拿大' },
        'japan': { flag: '🇯🇵', en: 'Japan', zh: '日本' },
        'korea': { flag: '🇰🇷', en: 'Korea', zh: '韩国' },
        'south korea': { flag: '🇰🇷', en: 'South Korea', zh: '韩国' },
        'hong kong': { flag: '🇭🇰', en: 'Hong Kong', zh: '中国香港' },
        'taiwan': { flag: '🇹🇼', en: 'Taiwan', zh: '中国台湾' },
        'china': { flag: '🇨🇳', en: 'China', zh: '中国' },
        'singapore': { flag: '🇸🇬', en: 'Singapore', zh: '新加坡' },
        'india': { flag: '🇮🇳', en: 'India', zh: '印度' },
        'brazil': { flag: '🇧🇷', en: 'Brazil', zh: '巴西' },
        'mexico': { flag: '🇲🇽', en: 'Mexico', zh: '墨西哥' },
        'turkey': { flag: '🇹🇷', en: 'Turkey', zh: '土耳其' },
        'israel': { flag: '🇮🇱', en: 'Israel', zh: '以色列' },
      };
      const v = map[key];
      if (!v) return String(raw);
      const parts = [v.flag, v.en, v.zh].filter(Boolean);
      return parts.join(' ');
    }

    function showError(elementId, msg) {
      const el = document.getElementById(elementId);
      el.textContent = msg;
      el.classList.add('show');
    }

    function hideError(elementId) {
      document.getElementById(elementId).classList.remove('show');
    }

    function copyText(elementId, btn) {
      const text = document.getElementById(elementId).textContent;
      navigator.clipboard.writeText(text).then(() => {
        btn.textContent = '已复制';
        btn.classList.add('copied');
        setTimeout(() => {
          btn.textContent = elementId === 'codeDisplay' ? '复制验证码' : '复制号码';
          btn.classList.remove('copied');
        }, 2000);
      });
    }

    function updateSteps(step, error = false) {
      for (let i = 1; i <= 4; i++) {
        const el = document.getElementById('step' + i);
        el.classList.remove('active', 'done', 'error');
        if (error && i === step) {
          el.classList.add('error');
        } else if (i < step) {
          el.classList.add('done');
        } else if (i === step) {
          el.classList.add('active');
        }
      }
    }

    function updateStatusBadge(status) {
      const badge = document.getElementById('statusBadge');
      badge.className = 'status-badge';
      const map = {
        'PENDING': ['pending', '排队中'],
        'PROCESSING': ['processing', '处理中'],
        'WAITING_SMS': ['waiting', '等待短信'],
        'CODE_READY': ['ready', '验证码已到达'],
        'DONE': ['done', '已完成'],
        'FAILED': ['failed', '失败'],
        'CANCELED': ['canceled', '已取消']
      };
      const [cls, text] = map[status] || ['pending', status];
      badge.classList.add(cls);
      badge.textContent = text;
    }

    function updateTimer() {
      let remaining = null;
      if (expiresAt) {
        remaining = Math.max(0, Math.floor((new Date(expiresAt).getTime() - Date.now()) / 1000));
      } else if (providerStartedAt) {
        const elapsed = Math.floor((Date.now() - new Date(providerStartedAt).getTime()) / 1000);
        remaining = Math.max(0, redeemWaitSeconds - elapsed);
      }

      if (remaining !== null) {
        document.getElementById('timerRow').style.display = 'flex';
        const mins = Math.floor(remaining / 60);
        const secs = remaining % 60;
        document.getElementById('timerValue').textContent = mins + ':' + String(secs).padStart(2, '0');

        const timerEl = document.getElementById('timerDisplay');
        timerEl.classList.remove('warning', 'danger');
        if (remaining < 30) {
          timerEl.classList.add('danger');
        } else if (remaining < 60) {
          timerEl.classList.add('warning');
        }
      } else {
        document.getElementById('timerRow').style.display = 'none';
      }
    }

    function renderActions(status) {
      const container = document.getElementById('actions');
      container.innerHTML = '';

      if (['PENDING', 'PROCESSING', 'WAITING_SMS'].includes(status)) {
        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'btn btn-outline btn-sm';
        cancelBtn.textContent = '取消';
        cancelBtn.onclick = () => doAction('cancel');
        container.appendChild(cancelBtn);
      }

      if (status === 'CODE_READY') {
        const completeBtn = document.createElement('button');
        completeBtn.className = 'btn btn-success btn-sm';
        completeBtn.textContent = '收到验证码，点击确认完成';
        completeBtn.onclick = () => doAction('complete');
        container.appendChild(completeBtn);
      }

      if (status === 'DONE') {
        const nextBtn = document.createElement('button');
        nextBtn.className = 'btn btn-primary btn-sm';
        nextBtn.textContent = '获取下一个号码';
        nextBtn.onclick = () => resetUI();
        container.appendChild(nextBtn);
      }

      if (['CANCELED', 'FAILED'].includes(status)) {
        const nextBtn = document.createElement('button');
        nextBtn.className = 'btn btn-primary btn-sm';
        nextBtn.textContent = '重新获取号码';
        nextBtn.onclick = () => doAction('next');
        container.appendChild(nextBtn);
      }
    }

    function updateHint(status) {
      const hint = document.getElementById('hintText');
      const hints = {
        'PENDING': '正在为您分配手机号码，请稍候...',
        'PROCESSING': '正在处理中，请稍候...',
        'WAITING_SMS': '请在目标平台使用上方号码触发短信验证',
        'CODE_READY': '验证码已到达，请尽快使用并点击确认完成',
        'DONE': '此订单已完成，您可以使用新的卡密继续兑换',
        'FAILED': '兑换失败，您可以重新获取号码再试',
        'CANCELED': '已取消，您可以重新获取号码'
      };
      hint.textContent = hints[status] || '';
    }

    async function startRedeem() {
      const voucher = document.getElementById('voucher').value.trim();
      if (!voucher) {
        showError('inputError', '请输入兑换码');
        return;
      }
      hideError('inputError');
      currentVoucher = voucher;

      const btn = document.getElementById('startBtn');
      btn.disabled = true;
      btn.innerHTML = '<div class="spinner"></div> 处理中...';

      try {
        const res = await fetch('/redeem', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code: voucher })
        });
        const data = await res.json();
        if (!res.ok) {
          const errMap = {
            'invalid_code': '兑换码无效',
            'voucher_used': '此卡密已被使用'
          };
          const msg = errMap[data.detail] || data.detail || '请求失败';
          showError('inputError', msg);
          btn.disabled = false;
          btn.innerHTML = '开始兑换';
          return;
        }

        currentTaskId = data.task_id;
        expiresAt = data.expires_at;
        providerStartedAt = data.provider_started_at;
        document.getElementById('inputCard').style.display = 'none';
        document.getElementById('statusCard').classList.add('active');
        document.getElementById('statusCard').classList.add('fade-in');
        updateUI(data);
        startPolling();
      } catch (e) {
        showError('inputError', '网络错误，请重试');
        btn.disabled = false;
        btn.innerHTML = '开始兑换';
      }
    }

    function updateUI(data) {
      const status = data.status;
      updateStatusBadge(status);

      // Step progress - error shows at the step where it happened
      if (status === 'PENDING') updateSteps(1);
      else if (status === 'PROCESSING') updateSteps(2);
      else if (status === 'WAITING_SMS') updateSteps(3);
      else if (['CODE_READY', 'DONE'].includes(status)) updateSteps(4);
      else if (status === 'CANCELED') {
        // Show error at current progress: if no phone yet, step 1; otherwise step 3
        updateSteps(data.phone ? 3 : 1, true);
      } else if (status === 'FAILED') {
        // Failed usually during SMS wait
        updateSteps(data.phone ? 3 : 2, true);
      }

      // Phone
      if (data.phone) {
        document.getElementById('phoneSection').style.display = 'block';
        document.getElementById('phoneDisplay').textContent = data.phone;
      } else {
        document.getElementById('phoneSection').style.display = 'none';
      }

      // Code
      if (data.result_code && ['CODE_READY', 'DONE'].includes(status)) {
        document.getElementById('codeSection').style.display = 'block';
        document.getElementById('codeDisplay').textContent = data.result_code;
      } else {
        document.getElementById('codeSection').style.display = 'none';
      }

      // Country
      if (data.country) {
        document.getElementById('countryRow').style.display = 'flex';
        document.getElementById('countryDisplay').textContent = formatCountry(data.country);
      } else {
        document.getElementById('countryRow').style.display = 'none';
      }

      // Timer
      expiresAt = data.expires_at;
      providerStartedAt = data.provider_started_at;
      updateTimer();

      // Actions
      renderActions(status);
      updateHint(status);

      // Error display
      hideError('statusError');

      // Final states
      if (['DONE', 'FAILED', 'CANCELED'].includes(status)) {
        stopPolling();
        document.getElementById('timerRow').style.display = 'none';
      }
    }

    async function doAction(action) {
      if (!currentTaskId) return;
      try {
        const res = await fetch('/redeem/' + currentTaskId + '/' + action, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code: currentVoucher })
        });
        const data = await res.json();
        if (!res.ok) {
          showError('statusError', data.detail || '操作失败');
          return;
        }
        updateUI(data);
        if (!['DONE', 'FAILED', 'CANCELED'].includes(data.status)) {
          startPolling();
        }
      } catch (e) {
        showError('statusError', '网络错误');
      }
    }

    function startPolling() {
      stopPolling();
      pollTimer = setInterval(async () => {
        if (!currentTaskId) return;
        try {
          const res = await fetch('/redeem/' + currentTaskId);
          if (res.ok) {
            const data = await res.json();
            updateUI(data);
          }
        } catch (e) {}
      }, 2000);

      countdownTimer = setInterval(updateTimer, 1000);
    }

    function stopPolling() {
      if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
      if (countdownTimer) { clearInterval(countdownTimer); countdownTimer = null; }
    }

    function resetUI() {
      stopPolling();
      currentTaskId = null;
      currentVoucher = '';
      expiresAt = null;
      providerStartedAt = null;

      document.getElementById('voucher').value = '';
      document.getElementById('inputCard').style.display = 'block';
      document.getElementById('statusCard').classList.remove('active', 'fade-in');
      document.getElementById('phoneSection').style.display = 'none';
      document.getElementById('codeSection').style.display = 'none';
      document.getElementById('timerRow').style.display = 'none';
      document.getElementById('actions').innerHTML = '';
      hideError('inputError');
      hideError('statusError');

      const btn = document.getElementById('startBtn');
      btn.disabled = false;
      btn.innerHTML = '开始兑换';

      updateSteps(0);
    }

    // Enter key to submit
    document.getElementById('voucher').addEventListener('keypress', (e) => {
      if (e.key === 'Enter') startRedeem();
    });
  </script>
</body>
</html>"""
        return redeem_html.replace("__REDEEM_WAIT_SECONDS__", str(int(settings.redeem_wait_seconds)))

    @app.on_event("startup")
    def _startup() -> None:
        if bool(getattr(settings, "db_auto_create_tables", True)):
            Base.metadata.create_all(bind=engine)

    app.include_router(health_router)
    app.include_router(admin_router)
    app.include_router(dev_router)
    app.include_router(redeem_router)
    return app


app = create_app()
