from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from mintcode_api.db import Base, engine
from mintcode_api.routes_admin import router as admin_router
from mintcode_api.routes_health import router as health_router
from mintcode_api.routes_redeem import router as redeem_router


def create_app() -> FastAPI:
    app = FastAPI(title="mintcode-api")

    @app.get("/admin-ui", response_class=HTMLResponse)
    def admin_ui() -> str:
        return """<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>MintCode Admin UI</title>
    <style>
      :root { color-scheme: light dark; }
      body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; margin: 20px; }
      .row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
      .card { border: 1px solid rgba(127,127,127,.35); border-radius: 10px; padding: 12px; margin-top: 14px; }
      label { font-size: 12px; opacity: .8; }
      input, select, button, textarea { padding: 8px 10px; border-radius: 8px; border: 1px solid rgba(127,127,127,.35); }
      button { cursor: pointer; }
      table { width: 100%; border-collapse: collapse; }
      th, td { border-bottom: 1px solid rgba(127,127,127,.25); padding: 8px; text-align: left; font-size: 13px; }
      th { position: sticky; top: 0; background: rgba(127,127,127,.08); }
      code { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 12px; }
      .muted { opacity: .7; }
      .right { margin-left: auto; }
      .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
    </style>
  </head>
  <body>
    <h2>MintCode Admin UI</h2>
    <div class=\"card\">
      <div class=\"row\">
        <div>
          <label>Admin Key (Header: <code>X-Admin-Key</code>)</label><br />
          <input id=\"adminKey\" class=\"mono\" placeholder=\"enter admin key\" style=\"min-width: 320px\" />
        </div>
        <button id=\"saveKey\">Save</button>
        <span id=\"keyStatus\" class=\"muted\"></span>
        <div class=\"right\">
          <button id=\"refreshAll\">Refresh</button>
          <label style=\"margin-left: 8px\">Auto refresh</label>
          <select id=\"autoRefresh\">
            <option value=\"0\">Off</option>
            <option value=\"2\" selected>2s</option>
            <option value=\"5\">5s</option>
          </select>
        </div>
      </div>
    </div>

    <div class=\"card\">
      <h3>Generate Vouchers</h3>
      <div class=\"row\">
        <div>
          <label>SKU</label><br />
          <input id=\"genSku\" placeholder=\"default\" />
        </div>
        <div>
          <label>Count</label><br />
          <input id=\"genCount\" type=\"number\" value=\"10\" min=\"1\" max=\"100000\" />
        </div>
        <div>
          <label>Length</label><br />
          <input id=\"genLen\" type=\"number\" value=\"32\" min=\"12\" max=\"64\" />
        </div>
        <div>
          <label>Label (optional)</label><br />
          <input id=\"genLabel\" placeholder=\"\" />
        </div>
        <button id=\"doGenerate\">Generate</button>
      </div>
      <div style=\"margin-top: 10px\">
        <label>Result (plain text codes)</label><br />
        <textarea id=\"genOut\" rows=\"6\" style=\"width: 100%\" spellcheck=\"false\"></textarea>
      </div>
    </div>

    <div class=\"card\">
      <div class=\"row\">
        <h3 style=\"margin: 0\">Batches</h3>
        <div class=\"right\">
          <label>SKU filter</label>
          <input id=\"batchSkuFilter\" placeholder=\"optional\" />
          <button id=\"loadBatches\">Load</button>
        </div>
      </div>
      <div style=\"overflow: auto; max-height: 420px\">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>SKU</th>
              <th>Count</th>
              <th>Created</th>
              <th>Export</th>
            </tr>
          </thead>
          <tbody id=\"batchesBody\"></tbody>
        </table>
      </div>
      <div style=\"margin-top: 10px\">
        <label>Export Output</label><br />
        <textarea id=\"exportOut\" rows=\"6\" style=\"width: 100%\" spellcheck=\"false\"></textarea>
      </div>
    </div>

    <div class=\"card\">
      <h3>Redeem (Create Task)</h3>
      <div class=\"row\">
        <div style=\"flex: 1\">
          <label>Voucher Code</label><br />
          <input id=\"redeemCode\" class=\"mono\" placeholder=\"paste voucher code here\" style=\"width: 100%\" />
        </div>
        <button id=\"doRedeem\">Redeem</button>
      </div>
      <div class=\"muted\" style=\"margin-top: 10px\" id=\"redeemOut\"></div>
    </div>

    <div class=\"card\">
      <div class=\"row\">
        <h3 style=\"margin: 0\">Redeem Tasks</h3>
        <div class=\"right\">
          <label>Status</label>
          <select id=\"taskStatus\">
            <option value=\"\">(any)</option>
            <option value=\"PENDING\">PENDING</option>
            <option value=\"PROCESSING\">PROCESSING</option>
            <option value=\"DONE\">DONE</option>
            <option value=\"FAILED\">FAILED</option>
          </select>
          <label>SKU</label>
          <input id=\"taskSku\" placeholder=\"optional\" />
          <button id=\"loadTasks\">Load</button>
        </div>
      </div>
      <div style=\"overflow: auto; max-height: 520px\">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>SKU</th>
              <th>Status</th>
              <th>Result</th>
              <th>Voucher</th>
              <th>Updated</th>
            </tr>
          </thead>
          <tbody id=\"tasksBody\"></tbody>
        </table>
      </div>
      <div id=\"err\" class=\"muted\" style=\"margin-top: 10px\"></div>
    </div>

    <script>
      const $ = (id) => document.getElementById(id);
      const storageKey = 'mintcode_admin_key';

      function getAdminKey() {
        return ($('adminKey').value || '').trim();
      }

      function setStatus(msg) {
        $('keyStatus').textContent = msg || '';
      }

      function setErr(msg) {
        $('err').textContent = msg || '';
      }

      async function apiFetch(path, opts={}) {
        const key = getAdminKey();
        const headers = new Headers(opts.headers || {});
        if (key) headers.set('X-Admin-Key', key);
        const res = await fetch(path, { ...opts, headers });
        if (!res.ok) {
          const txt = await res.text();
          throw new Error(res.status + ' ' + txt);
        }
        return res;
      }

      async function loadBatches() {
        setErr('');
        const sku = ($('batchSkuFilter').value || '').trim();
        const qs = new URLSearchParams();
        if (sku) qs.set('sku_id', sku);
        qs.set('limit', '50');
        const res = await apiFetch('/admin/batches?' + qs.toString());
        const data = await res.json();
        const body = $('batchesBody');
        body.innerHTML = '';
        for (const b of data) {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td class="mono">${b.id}</td>
            <td class="mono">${b.sku_id}</td>
            <td>${b.count}</td>
            <td class="mono">${b.created_at}</td>
            <td><button data-batch="${b.id}">Export</button></td>
          `;
          tr.querySelector('button').addEventListener('click', async () => {
            try {
              const r = await apiFetch('/admin/vouchers/export/batch/' + b.id);
              $('exportOut').value = await r.text();
            } catch (e) {
              setErr(String(e));
            }
          });
          body.appendChild(tr);
        }
      }

      async function loadTasks() {
        setErr('');
        const status = $('taskStatus').value;
        const sku = ($('taskSku').value || '').trim();
        const qs = new URLSearchParams();
        if (status) qs.set('status', status);
        if (sku) qs.set('sku_id', sku);
        qs.set('limit', '100');
        const res = await apiFetch('/admin/redeem/tasks?' + qs.toString());
        const data = await res.json();
        const body = $('tasksBody');
        body.innerHTML = '';
        for (const t of data) {
          const tr = document.createElement('tr');
          const v = (t.voucher_code || '').slice(0, 12) + ((t.voucher_code || '').length > 12 ? '…' : '');
          tr.innerHTML = `
            <td class="mono">${t.id}</td>
            <td class="mono">${t.sku_id}</td>
            <td class="mono">${t.status}</td>
            <td class="mono">${t.result_code || ''}</td>
            <td class="mono" title="${t.voucher_code || ''}">${v}</td>
            <td class="mono">${t.updated_at}</td>
          `;
          body.appendChild(tr);
        }
      }

      async function doGenerate() {
        setErr('');
        const payload = {
          sku_id: ($('genSku').value || '').trim() || null,
          count: Number($('genCount').value || 10),
          length: Number($('genLen').value || 32),
          label: ($('genLabel').value || '').trim() || null,
          label_length: 6,
          label_pos: 8,
        };
        const res = await apiFetch('/admin/vouchers/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        $('genOut').value = await res.text();
        await loadBatches();
      }

      async function doRedeem() {
        setErr('');
        $('redeemOut').textContent = '';
        const code = ($('redeemCode').value || '').trim();
        if (!code) {
          $('redeemOut').textContent = 'Please input voucher code.';
          return;
        }
        const res = await apiFetch('/redeem', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code }),
        });
        const data = await res.json();
        $('redeemOut').textContent = `Created task_id=${data.task_id}, status=${data.status}`;
        await loadTasks();
      }

      function loadKeyFromStorage() {
        const k = localStorage.getItem(storageKey) || '';
        $('adminKey').value = k;
        setStatus(k ? 'loaded from localStorage' : '');
      }

      function saveKeyToStorage() {
        const k = getAdminKey();
        localStorage.setItem(storageKey, k);
        setStatus(k ? 'saved' : 'cleared');
      }

      let timer = null;
      function resetAutoRefresh() {
        if (timer) clearInterval(timer);
        timer = null;
        const sec = Number($('autoRefresh').value || 0);
        if (sec > 0) {
          timer = setInterval(() => {
            loadTasks().catch(() => {});
          }, sec * 1000);
        }
      }

      $('saveKey').addEventListener('click', () => { saveKeyToStorage(); });
      $('refreshAll').addEventListener('click', async () => {
        try {
          await loadBatches();
          await loadTasks();
        } catch (e) {
          setErr(String(e));
        }
      });
      $('loadBatches').addEventListener('click', () => loadBatches().catch(e => setErr(String(e))));
      $('loadTasks').addEventListener('click', () => loadTasks().catch(e => setErr(String(e))));
      $('doGenerate').addEventListener('click', () => doGenerate().catch(e => setErr(String(e))));
      $('doRedeem').addEventListener('click', () => doRedeem().catch(e => setErr(String(e))));
      $('autoRefresh').addEventListener('change', resetAutoRefresh);

      loadKeyFromStorage();
      resetAutoRefresh();
      $('refreshAll').click();
    </script>
  </body>
</html>"""

    @app.on_event("startup")
    def _startup() -> None:
        Base.metadata.create_all(bind=engine)

    app.include_router(health_router)
    app.include_router(admin_router)
    app.include_router(redeem_router)
    return app


app = create_app()
