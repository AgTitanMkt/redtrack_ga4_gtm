"""
Rotas administrativas para GA4 Integrations.
CRUD completo + interface HTML em /admin/ga4/

Permite cadastrar credenciais GA4 por domínio/funil.
Se nenhuma integração existir, o sistema usa o fallback do .env.
"""
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

from app.services import ga4_destinations

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/ga4", tags=["GA4 Integrations Admin"])


# ── Request Models ───────────────────────────────────────────────

class IntegrationCreate(BaseModel):
    name: str
    domain: str
    page_path: str = ""
    measurement_id: str
    api_secret: str
    use_gtm_server: bool = False


class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    page_path: Optional[str] = None
    measurement_id: Optional[str] = None
    api_secret: Optional[str] = None
    use_gtm_server: Optional[bool] = None
    is_active: Optional[bool] = None


# ── API Endpoints ────────────────────────────────────────────────

@router.get("/integrations")
def list_integrations():
    """Lista todas as integrações GA4 cadastradas."""
    try:
        return ga4_destinations.list_integrations()
    except Exception as e:
        logger.error("Erro ao listar integrações: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integrations/{integration_id}")
def get_integration(integration_id: int):
    """Busca uma integração pelo ID."""
    try:
        result = ga4_destinations.get_integration(integration_id)
        if not result:
            raise HTTPException(status_code=404, detail="Integração não encontrada")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao buscar integração: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/integrations")
def create_integration(req: IntegrationCreate):
    """Cria uma nova integração GA4 para um domínio/página."""
    try:
        return ga4_destinations.create_integration(
            name=req.name,
            domain=req.domain,
            page_path=req.page_path,
            measurement_id=req.measurement_id,
            api_secret=req.api_secret,
            use_gtm_server=req.use_gtm_server,
        )
    except Exception as e:
        logger.error("Erro ao criar integração: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/integrations/{integration_id}")
def update_integration(integration_id: int, req: IntegrationUpdate):
    """Atualiza campos de uma integração existente."""
    try:
        result = ga4_destinations.update_integration(
            integration_id, **req.dict(exclude_unset=True)
        )
        if not result:
            raise HTTPException(status_code=404, detail="Integração não encontrada")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao atualizar integração: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/integrations/{integration_id}")
def delete_integration(integration_id: int):
    """Remove uma integração."""
    try:
        deleted = ga4_destinations.delete_integration(integration_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Integração não encontrada")
        return {"ok": True, "deleted": integration_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao deletar integração: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Interface HTML ───────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
def admin_page():
    """Interface administrativa para gerenciar integrações GA4."""
    return _ADMIN_HTML


_ADMIN_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GA4 Integrations Admin</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #0f1117; color: #e0e0e0; padding: 20px; max-width: 1100px; margin: 0 auto; }
  h1 { margin-bottom: 8px; color: #fff; }
  .subtitle { color: #888; margin-bottom: 24px; font-size: 14px; }
  .fallback-info { background: #1a1f2e; border: 1px solid #2d3548; border-radius: 8px;
                   padding: 14px 18px; margin-bottom: 24px; font-size: 13px; }
  .fallback-info code { background: #252b3b; padding: 2px 6px; border-radius: 4px; color: #7dd3fc; }
  table { width: 100%; border-collapse: collapse; margin-bottom: 24px; }
  th { text-align: left; padding: 10px 12px; background: #1a1f2e; color: #aaa; font-size: 12px;
       text-transform: uppercase; letter-spacing: 0.5px; }
  td { padding: 10px 12px; border-bottom: 1px solid #1e2333; font-size: 14px; }
  tr:hover td { background: #161b28; }
  .badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
  .badge-on { background: #0e3a2d; color: #34d399; }
  .badge-off { background: #3b1c1c; color: #f87171; }
  .btn { padding: 6px 14px; border: none; border-radius: 6px; cursor: pointer;
         font-size: 13px; font-weight: 500; transition: background .15s; }
  .btn-primary { background: #3b82f6; color: #fff; }
  .btn-primary:hover { background: #2563eb; }
  .btn-danger { background: #7f1d1d; color: #fca5a5; }
  .btn-danger:hover { background: #991b1b; }
  .btn-sm { padding: 4px 10px; font-size: 12px; }
  .form-card { background: #1a1f2e; border: 1px solid #2d3548; border-radius: 8px;
               padding: 20px; margin-bottom: 24px; }
  .form-card h2 { font-size: 16px; margin-bottom: 16px; color: #fff; }
  .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .form-group { display: flex; flex-direction: column; gap: 4px; }
  .form-group.full { grid-column: 1 / -1; }
  label { font-size: 12px; color: #999; text-transform: uppercase; letter-spacing: 0.5px; }
  input[type="text"], select { background: #0f1117; border: 1px solid #2d3548; border-radius: 6px;
         padding: 8px 12px; color: #e0e0e0; font-size: 14px; }
  input:focus, select:focus { outline: none; border-color: #3b82f6; }
  .form-actions { margin-top: 16px; display: flex; gap: 10px; }
  .empty-row td { text-align: center; color: #666; padding: 30px; }
  .toast { position: fixed; top: 20px; right: 20px; padding: 12px 20px; border-radius: 8px;
           font-size: 14px; z-index: 999; transition: opacity .3s; }
  .toast-ok { background: #0e3a2d; color: #34d399; border: 1px solid #166534; }
  .toast-err { background: #3b1c1c; color: #f87171; border: 1px solid #7f1d1d; }
  .hidden { display: none; }
</style>
</head>
<body>

<h1>GA4 Integrations</h1>
<p class="subtitle">Gerencie credenciais GA4 por domínio/funil. Se nenhuma integração ativa existir, o sistema usa o fallback do .env.</p>

<div class="fallback-info">
  Fallback atual: <code id="fb-mid">carregando...</code> &nbsp;|&nbsp;
  GTM Server: <code id="fb-gtm">-</code>
</div>

<table>
  <thead>
    <tr>
      <th>Nome</th><th>Domínio</th><th>Path</th><th>Measurement ID</th>
      <th>GTM</th><th>Status</th><th>Ações</th>
    </tr>
  </thead>
  <tbody id="table-body">
    <tr class="empty-row"><td colspan="7">Carregando...</td></tr>
  </tbody>
</table>

<div class="form-card" id="form-card">
  <h2 id="form-title">Nova Integração</h2>
  <div class="form-grid">
    <div class="form-group">
      <label>Nome (identificador)</label>
      <input type="text" id="f-name" placeholder="ex: Funil VSL Principal">
    </div>
    <div class="form-group">
      <label>Domínio (sem https://)</label>
      <input type="text" id="f-domain" placeholder="ex: meusite.com">
    </div>
    <div class="form-group">
      <label>Page Path (opcional)</label>
      <input type="text" id="f-path" placeholder="ex: /lp/vsl1">
    </div>
    <div class="form-group">
      <label>Measurement ID</label>
      <input type="text" id="f-mid" placeholder="G-XXXXXXXXXX">
    </div>
    <div class="form-group">
      <label>API Secret</label>
      <input type="text" id="f-secret" placeholder="api_secret">
    </div>
    <div class="form-group">
      <label>GTM Server</label>
      <select id="f-gtm"><option value="false">Desabilitado</option><option value="true">Habilitado</option></select>
    </div>
  </div>
  <div class="form-actions">
    <button class="btn btn-primary" id="btn-save" onclick="saveForm()">Salvar</button>
    <button class="btn hidden" id="btn-cancel" onclick="cancelEdit()">Cancelar</button>
  </div>
</div>

<div class="toast hidden" id="toast"></div>

<script>
var API = '/admin/ga4/integrations';
var editingId = null;

function toast(msg, ok) {
  var t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast ' + (ok ? 'toast-ok' : 'toast-err');
  setTimeout(function() { t.className = 'toast hidden'; }, 3000);
}

function loadFallback() {
  // Mostra info de fallback a partir do health ou simplesmente indica que está configurado
  document.getElementById('fb-mid').textContent = '(definido no .env)';
  document.getElementById('fb-gtm').textContent = '(definido no .env)';
}

function loadTable() {
  fetch(API).then(function(r) { return r.json(); }).then(function(rows) {
    var tb = document.getElementById('table-body');
    if (!rows.length) {
      tb.innerHTML = '<tr class="empty-row"><td colspan="7">Nenhuma integração cadastrada. Usando fallback do .env.</td></tr>';
      return;
    }
    tb.innerHTML = rows.map(function(r) {
      var active = r.is_active;
      return '<tr>' +
        '<td>' + esc(r.name) + '</td>' +
        '<td>' + esc(r.domain) + '</td>' +
        '<td>' + (r.page_path || '<em style="color:#555">qualquer</em>') + '</td>' +
        '<td><code>' + esc(r.measurement_id) + '</code></td>' +
        '<td>' + (r.use_gtm_server ? '<span class="badge badge-on">ON</span>' : '<span class="badge badge-off">OFF</span>') + '</td>' +
        '<td>' + (active ? '<span class="badge badge-on">Ativo</span>' : '<span class="badge badge-off">Inativo</span>') + '</td>' +
        '<td>' +
          '<button class="btn btn-primary btn-sm" onclick="editRow(' + r.id + ')">Editar</button> ' +
          '<button class="btn btn-sm" style="background:#374151;color:#d1d5db" onclick="toggleActive(' + r.id + ',' + !active + ')">' + (active ? 'Desativar' : 'Ativar') + '</button> ' +
          '<button class="btn btn-danger btn-sm" onclick="deleteRow(' + r.id + ')">Excluir</button>' +
        '</td></tr>';
    }).join('');
  }).catch(function(e) {
    document.getElementById('table-body').innerHTML = '<tr class="empty-row"><td colspan="7">Erro ao carregar: ' + e + '</td></tr>';
  });
}

function esc(s) { if (!s) return ''; var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

function clearForm() {
  editingId = null;
  document.getElementById('form-title').textContent = 'Nova Integração';
  document.getElementById('btn-cancel').classList.add('hidden');
  ['f-name','f-domain','f-path','f-mid','f-secret'].forEach(function(id) { document.getElementById(id).value = ''; });
  document.getElementById('f-gtm').value = 'false';
}

function cancelEdit() { clearForm(); }

function saveForm() {
  var body = {
    name: document.getElementById('f-name').value.trim(),
    domain: document.getElementById('f-domain').value.trim(),
    page_path: document.getElementById('f-path').value.trim(),
    measurement_id: document.getElementById('f-mid').value.trim(),
    api_secret: document.getElementById('f-secret').value.trim(),
    use_gtm_server: document.getElementById('f-gtm').value === 'true',
  };
  if (!body.name || !body.domain || !body.measurement_id || !body.api_secret) {
    toast('Preencha nome, domínio, measurement ID e API secret', false); return;
  }
  var method = editingId ? 'PUT' : 'POST';
  var url = editingId ? API + '/' + editingId : API;
  fetch(url, { method: method, headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) })
    .then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(function() { toast(editingId ? 'Atualizado!' : 'Criado!', true); clearForm(); loadTable(); })
    .catch(function(e) { toast('Erro: ' + e, false); });
}

function editRow(id) {
  fetch(API + '/' + id).then(function(r) { return r.json(); }).then(function(r) {
    editingId = r.id;
    document.getElementById('form-title').textContent = 'Editando: ' + r.name;
    document.getElementById('btn-cancel').classList.remove('hidden');
    document.getElementById('f-name').value = r.name;
    document.getElementById('f-domain').value = r.domain;
    document.getElementById('f-path').value = r.page_path || '';
    document.getElementById('f-mid').value = r.measurement_id;
    document.getElementById('f-secret').value = r.api_secret;
    document.getElementById('f-gtm').value = r.use_gtm_server ? 'true' : 'false';
  });
}

function toggleActive(id, newState) {
  fetch(API + '/' + id, { method: 'PUT', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({is_active: newState}) })
    .then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(function() { toast(newState ? 'Ativado!' : 'Desativado!', true); loadTable(); })
    .catch(function(e) { toast('Erro: ' + e, false); });
}

function deleteRow(id) {
  if (!confirm('Tem certeza que deseja excluir esta integração?')) return;
  fetch(API + '/' + id, { method: 'DELETE' })
    .then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(function() { toast('Excluído!', true); loadTable(); })
    .catch(function(e) { toast('Erro: ' + e, false); });
}

loadFallback();
loadTable();
</script>
</body>
</html>"""
