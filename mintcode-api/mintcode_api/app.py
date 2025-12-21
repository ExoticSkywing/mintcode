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
