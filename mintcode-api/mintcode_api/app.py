from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from mintcode_api.config import settings
from mintcode_api.db import Base, engine
from mintcode_api.routes_admin import router as admin_router
from mintcode_api.routes_dev import router as dev_router
from mintcode_api.routes_health import router as health_router
from mintcode_api.routes_redeem import router as redeem_router


def create_app() -> FastAPI:
    app = FastAPI(title="mintcode-api")

    @app.get("/admin-ui", response_class=HTMLResponse)
    def admin_ui() -> str:
        html = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
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

    <div class="card">
      <h3>SKU Provider Config (5sim)</h3>
      <div class="row">
        <div>
          <label>SKU ID</label><br />
          <input id="cfgSku" class="mono" placeholder="e.g. tg1" />
        </div>
        <div>
          <label>Category</label><br />
          <select id=\"cfgCategory\">
            <option value=\"activation\" selected>activation</option>
            <option value=\"hosting\">hosting</option>
          </select>
        </div>
        <div>
          <label>Country</label><br />
          <input id=\"cfgCountry\" class=\"mono\" placeholder=\"e.g. russia / any\" />
        </div>
        <div>
          <label>Operator</label><br />
          <input id=\"cfgOperator\" class=\"mono\" placeholder=\"e.g. any\" />
        </div>
        <div>
          <label>Product</label><br />
          <input id=\"cfgProduct\" class=\"mono\" placeholder=\"e.g. telegram\" />
        </div>
        <div>
          <label>Poll (sec)</label><br />
          <input id=\"cfgPoll\" type=\"number\" value=\"5\" min=\"1\" max=\"300\" />
        </div>
        <div>
          <label>Reuse</label><br />
          <input id=\"cfgReuse\" type=\"checkbox\" />
        </div>
        <div>
          <label>Voice</label><br />
          <input id="cfgVoice" type="checkbox" />
        </div>
        <div>
          <label>History</label><br />
          <select id="cfgHist" style="min-width: 320px"></select>
        </div>
        <button id="cfgLoad">Load</button>
        <button id="cfgSave">Save</button>
        <button id="cfgHistLoad">Load History</button>
      </div>
      <div class="muted" style="margin-top: 10px" id="cfgOut"></div>
    </div>

    <div class="card">
      <div class="row">
        <h3 style="margin: 0">Featured Provider Configs (Auto-collected)</h3>
        <div class="right">
          <label>SKU</label>
          <input id="featSku" placeholder="optional" />
          <button id="loadFeatured">Load</button>
        </div>
      </div>
      <div style="overflow: auto; max-height: 260px">
        <table>
          <thead>
            <tr>
              <th>Count</th>
              <th>Avg Cost</th>
              <th>Total Cost</th>
              <th>Last</th>
              <th>Country</th>
              <th>Operator</th>
              <th>Product</th>
              <th>Reuse</th>
              <th>Voice</th>
              <th>Poll</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody id="featuredBody"></tbody>
        </table>
      </div>
      <div class="muted" style="margin-top: 10px" id="featuredOut"></div>
    </div>

    <div class="card">
      <h3>Redeem (Create Task)</h3>
      <div class="row">
        <div style="flex: 1">
          <label>Voucher Code</label><br />
          <input id="redeemCode" class="mono" placeholder="paste voucher code here" style="width: 100%" />
        </div>
        <button id="doRedeem">Redeem</button>
      </div>
      <div class="muted" style="margin-top: 10px" id="redeemOut"></div>
      <div class="row" style="margin-top: 10px" id="redeemActions"></div>
    </div>

    <div class=\"card\">
      <div class=\"row\">
        <h3 style=\"margin: 0\">Redeem Tasks</h3>
        <div class=\"right\">
          <label>Status</label>
          <select id=\"taskStatus\">
            <option value=\"\">(any)</option>
            <option value=\"PENDING\">PENDING</option>
            <option value=\"WAITING_SMS\">WAITING_SMS</option>
            <option value=\"PROCESSING\">PROCESSING</option>
            <option value=\"CODE_READY\">CODE_READY</option>
            <option value=\"DONE\">DONE</option>
            <option value=\"FAILED\">FAILED</option>
            <option value=\"CANCELED\">CANCELED</option>
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
              <th>Phone</th>
              <th>Order</th>
              <th>Upstream</th>
              <th>Price</th>
              <th>Error</th>
              <th>Actions</th>
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
      const redeemWaitLimitSeconds = __REDEEM_WAIT_SECONDS__;

      function getAdminKey() {
        return ($('adminKey').value || '').trim();
      }

      let featuredItems = [];
      async function loadFeatured() {
        setErr('');
        $('featuredOut').textContent = '';
        const sku = (($('featSku').value || '').trim() || ($('cfgSku').value || '').trim());
        if (!sku) {
          $('featuredOut').textContent = 'Please input sku_id.';
          return;
        }
        const res = await apiFetch('/admin/sku/' + encodeURIComponent(sku) + '/provider-config/successes?limit=50');
        const data = await res.json();
        featuredItems = Array.isArray(data) ? data : [];
        const body = $('featuredBody');
        body.innerHTML = '';
        for (let i = 0; i < featuredItems.length; i++) {
          const f = featuredItems[i];
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td class="mono">${f.success_count}</td>
            <td class="mono">${Number(f.avg_success_cost || 0).toFixed(4)}</td>
            <td class="mono">${Number(f.total_success_cost || 0).toFixed(4)}</td>
            <td class="mono">${(f.last_success_at || '').replace('T', ' ').replace('Z', '')}</td>
            <td class="mono">${f.country}</td>
            <td class="mono">${f.operator}</td>
            <td class="mono">${f.product}</td>
            <td class="mono">${f.reuse ? '1' : '0'}</td>
            <td class="mono">${f.voice ? '1' : '0'}</td>
            <td class="mono">${f.poll_interval_seconds}</td>
            <td><button data-idx="${i}">Apply</button></td>
          `;
          tr.querySelector('button').addEventListener('click', () => {
            try {
              const idx = Number(tr.querySelector('button').getAttribute('data-idx'));
              const item = featuredItems[idx];
              if (!item) return;
              $('cfgSku').value = item.sku_id;
              $('cfgCategory').value = item.category || 'activation';
              $('cfgCountry').value = item.country || '';
              $('cfgOperator').value = item.operator || 'any';
              $('cfgProduct').value = item.product || '';
              $('cfgPoll').value = String(item.poll_interval_seconds || 5);
              $('cfgReuse').checked = !!item.reuse;
              $('cfgVoice').checked = !!item.voice;
              $('cfgOut').textContent = 'Applied featured config. Click Save to set as current.';
            } catch (e) {
              setErr(String(e));
            }
          });
          body.appendChild(tr);
        }
        $('featuredOut').textContent = 'Loaded ' + String(featuredItems.length) + ' items for sku_id=' + sku;
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
          const p = (t.phone || '').slice(0, 18) + ((t.phone || '').length > 18 ? '…' : '');
          const err = (t.last_error || '').slice(0, 20) + ((t.last_error || '').length > 20 ? '…' : '');
          const price = (t.price === null || t.price === undefined) ? '' : Number(t.price).toFixed(4);
          tr.innerHTML = `
            <td class="mono">${t.id}</td>
            <td class="mono">${t.sku_id}</td>
            <td class="mono">${t.status}</td>
            <td class="mono">${t.result_code || ''}</td>
            <td class="mono" title="${t.phone || ''}">${p}</td>
            <td class="mono">${t.order_id || ''}</td>
            <td class="mono">${t.upstream_status || ''}</td>
            <td class="mono">${price}</td>
            <td class="mono" title="${t.last_error || ''}">${err}</td>
            <td class="mono actions"></td>
            <td class="mono" title="${t.voucher_code || ''}">${v}</td>
            <td class="mono">${(t.updated_at || '').replace('T', ' ').replace('Z', '')}</td>
          `;

          const actions = tr.querySelector('.actions');
          const canCancel = (t.status === 'WAITING_SMS' || t.status === 'PENDING' || t.status === 'PROCESSING' || t.status === 'FAILED');
          const canNext = (t.status === 'CANCELED');
          const canComplete = (t.status === 'CODE_READY');
          if (canCancel) {
            const btnCancel = document.createElement('button');
            btnCancel.textContent = '取消';
            btnCancel.addEventListener('click', async () => {
              try {
                await apiFetch('/redeem/' + String(t.id) + '/cancel', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ code: t.voucher_code }),
                });
                await loadTasks();
              } catch (e) { setErr(String(e)); }
            });
            actions.appendChild(btnCancel);
          }
          if (canNext) {
            const btnNext = document.createElement('button');
            btnNext.textContent = '购买下一个号码';
            btnNext.addEventListener('click', async () => {
              try {
                await apiFetch('/redeem/' + String(t.id) + '/next', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ code: t.voucher_code }),
                });
                await loadTasks();
              } catch (e) { setErr(String(e)); }
            });
            actions.appendChild(btnNext);
          }
          if (canComplete) {
            const btnComplete = document.createElement('button');
            btnComplete.textContent = '完成';
            btnComplete.addEventListener('click', async () => {
              try {
                await apiFetch('/redeem/' + String(t.id) + '/complete', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ code: t.voucher_code }),
                });
                await loadTasks();
              } catch (e) { setErr(String(e)); }
            });
            actions.appendChild(btnComplete);
          }
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

      async function loadSkuConfig() {
        setErr('');
        $('cfgOut').textContent = '';
        const sku = ($('cfgSku').value || '').trim();
        if (!sku) {
          $('cfgOut').textContent = 'Please input sku_id.';
          return;
        }
        const res = await apiFetch('/admin/sku/' + encodeURIComponent(sku) + '/provider-config');
        const data = await res.json();
        $('cfgCategory').value = data.category || 'activation';
        $('cfgCountry').value = data.country || '';
        $('cfgOperator').value = data.operator || 'any';
        $('cfgProduct').value = data.product || '';
        $('cfgPoll').value = String(data.poll_interval_seconds || 5);
        $('cfgReuse').checked = !!data.reuse;
        $('cfgVoice').checked = !!data.voice;
        $('cfgOut').textContent = 'Loaded.';
        await loadSkuConfigHistory();
      }

      let cfgHistItems = [];
      async function loadSkuConfigHistory() {
        const sku = ($('cfgSku').value || '').trim();
        if (!sku) return;
        const sel = $('cfgHist');
        sel.innerHTML = '';
        cfgHistItems = [];
        try {
          const res = await apiFetch('/admin/sku/' + encodeURIComponent(sku) + '/provider-config/history?limit=30');
          const data = await res.json();
          if (!Array.isArray(data)) return;
          cfgHistItems = data;
          for (let i = 0; i < data.length; i++) {
            const h = data[i];
            const opt = document.createElement('option');
            const label = `${h.created_at}  ${h.country}/${h.operator}/${h.product}  poll=${h.poll_interval_seconds}`;
            opt.value = String(i);
            opt.textContent = label;
            sel.appendChild(opt);
          }
        } catch (e) {
          // ignore
        }
      }

      function applyHistoryItem(h) {
        if (!h) return;
        $('cfgCategory').value = h.category || 'activation';
        $('cfgCountry').value = h.country || '';
        $('cfgOperator').value = h.operator || 'any';
        $('cfgProduct').value = h.product || '';
        $('cfgPoll').value = String(h.poll_interval_seconds || 5);
        $('cfgReuse').checked = !!h.reuse;
        $('cfgVoice').checked = !!h.voice;
        $('cfgOut').textContent = 'Loaded from history.';
      }

      async function saveSkuConfig() {
        setErr('');
        $('cfgOut').textContent = '';
        const sku = ($('cfgSku').value || '').trim();
        if (!sku) {
          $('cfgOut').textContent = 'Please input sku_id.';
          return;
        }
        const payload = {
          provider: 'fivesim',
          category: $('cfgCategory').value,
          country: ($('cfgCountry').value || '').trim(),
          operator: ($('cfgOperator').value || '').trim() || 'any',
          product: ($('cfgProduct').value || '').trim(),
          reuse: $('cfgReuse').checked,
          voice: $('cfgVoice').checked,
          poll_interval_seconds: Number($('cfgPoll').value || 5),
        };
        const res = await apiFetch('/admin/sku/' + encodeURIComponent(sku) + '/provider-config', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        $('cfgOut').textContent = 'Saved for sku_id=' + data.sku_id;
        await loadSkuConfigHistory();
      }

      async function doRedeem() {
        setErr('');
        $('redeemOut').textContent = '';
        $('redeemActions').innerHTML = '';
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
        renderRedeemActions(data);
        await loadTasks();
        pollRedeemStatus(data.task_id).catch(e => setErr(String(e)));
      }

      function renderRedeemActions(d) {
        const wrap = $('redeemActions');
        wrap.innerHTML = '';
        if (!d || !d.task_id) return;

        const voucherCode = ($('redeemCode').value || '').trim();
        const taskId = String(d.task_id);

        const mkBtn = (text, onClick) => {
          const b = document.createElement('button');
          b.textContent = text;
          b.addEventListener('click', () => onClick().catch(e => setErr(String(e))));
          return b;
        };

        const canCancel = (d.status === 'WAITING_SMS' || d.status === 'PENDING' || d.status === 'PROCESSING' || d.status === 'FAILED');
        const canNext = (d.status === 'CANCELED' || d.status === 'FAILED');
        const canComplete = (d.status === 'CODE_READY');

        if (canCancel) {
          wrap.appendChild(mkBtn('取消', async () => {
            await apiFetch('/redeem/' + taskId + '/cancel', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ code: voucherCode }),
            });
            await pollRedeemStatus(Number(taskId));
          }));
        }

        if (canNext) {
          const hint = document.createElement('div');
          hint.className = 'muted';
          hint.style.marginRight = '10px';
          hint.textContent = '该卡密当前已结束/取消。再次 Redeem 会继续使用同一个任务；如需重新下单请点击：';
          wrap.appendChild(hint);
          wrap.appendChild(mkBtn('购买下一个号码', async () => {
            await apiFetch('/redeem/' + taskId + '/next', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ code: voucherCode }),
            });
            await pollRedeemStatus(Number(taskId));
          }));
        }

        if (canComplete) {
          wrap.appendChild(mkBtn('完成', async () => {
            await apiFetch('/redeem/' + taskId + '/complete', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ code: voucherCode }),
            });
            await pollRedeemStatus(Number(taskId));
          }));
        }
      }

      let redeemPollTimer = null;
      async function pollRedeemStatus(taskId) {
        if (redeemPollTimer) clearInterval(redeemPollTimer);
        redeemPollTimer = null;

        const tick = async () => {
          const r = await apiFetch('/redeem/' + String(taskId));
          const d = await r.json();
          const phone = d.phone ? ` phone=${d.phone}` : '';
          const upstream = d.upstream_status ? ` upstream=${d.upstream_status}` : '';
          const code = d.result_code ? ` code=${d.result_code}` : '';
          let remain = '';
          if (d.status === 'WAITING_SMS' || d.status === 'PROCESSING' || d.status === 'PENDING' || d.status === 'CODE_READY') {
            let left = null;
            if (d.expires_at) {
              const ex = Date.parse(d.expires_at);
              if (!Number.isNaN(ex)) {
                left = Math.max(0, Math.floor((ex - Date.now()) / 1000));
              }
            }
            if (left === null && d.provider_started_at) {
              const ms = Date.parse(d.provider_started_at);
              if (!Number.isNaN(ms)) {
                const elapsed = Math.floor((Date.now() - ms) / 1000);
                left = Math.max(0, redeemWaitLimitSeconds - elapsed);
              }
            }
            if (left !== null) remain = ` wait_left=${left}s`;
          }
          $('redeemOut').textContent = `task_id=${d.task_id}, status=${d.status}${phone}${upstream}${remain}${code}`;
          renderRedeemActions(d);
          if (d.phone) {
            $('redeemOut').textContent += `\nUse this phone to trigger SMS on the target platform (register/login).`;
          }
          if (d.status === 'DONE' || d.status === 'FAILED' || d.status === 'CANCELED') {
            if (redeemPollTimer) clearInterval(redeemPollTimer);
            redeemPollTimer = null;
          }
          await loadTasks();
        };

        await tick();
        redeemPollTimer = setInterval(() => {
          tick().catch(e => setErr(String(e)));
        }, 1500);
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
      $('cfgLoad').addEventListener('click', () => loadSkuConfig().catch(e => setErr(String(e))));
      $('cfgSave').addEventListener('click', () => saveSkuConfig().catch(e => setErr(String(e))));
      $('loadFeatured').addEventListener('click', () => loadFeatured().catch(e => setErr(String(e))));
      $('cfgHistLoad').addEventListener('click', () => {
        try {
          const idx = Number(($('cfgHist').value || '0'));
          const h = cfgHistItems[idx];
          applyHistoryItem(h);
        } catch (e) { setErr(String(e)); }
      });
      $('doRedeem').addEventListener('click', () => doRedeem().catch(e => setErr(String(e))));
      $('autoRefresh').addEventListener('change', resetAutoRefresh);

      loadKeyFromStorage();
      resetAutoRefresh();
      $('refreshAll').click();
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
      <div class="input-group">
        <label for="voucher">兑换码</label>
        <input type="text" id="voucher" placeholder="请输入您的兑换码" autocomplete="off" spellcheck="false" />
      </div>
      <button class="btn btn-primary" id="startBtn" onclick="startRedeem()">
        开始兑换
      </button>
      <div class="error-msg" id="inputError"></div>
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
        'DONE': '兑换已完成，您可以使用新的卡密继续兑换',
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
          const msg = data.detail === 'invalid_code' ? '兑换码无效' : (data.detail || '请求失败');
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
