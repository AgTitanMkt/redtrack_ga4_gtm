"""
Dashboard Master — Interface completa de gerenciamento.
Servido como HTML puro em /dashboard/ (sem build step, sem container separado).

Gerencia:
  - Integrações GA4 multi-domínio (CRUD)
  - Webhooks CartPanda/ClickBank (URLs + setup)
  - Instalação do tracker.js
  - Diagnóstico em tempo real (DB, Redis, GTM SS, GA4)
  - Testes de envio GA4/GTM SS
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard", response_class=HTMLResponse)
@router.get("/dashboard/", response_class=HTMLResponse)
def dashboard():
    return _HTML


_HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>DataHooks Tracking — Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'DM Sans',sans-serif;background:#08090d;color:#c8ccd4;min-height:100vh}
.grid-bg{position:fixed;inset:0;z-index:0;opacity:.025;background-image:linear-gradient(rgba(255,255,255,.1) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.1) 1px,transparent 1px);background-size:60px 60px}
.wrap{position:relative;z-index:1;max-width:1200px;margin:0 auto;padding:24px 20px}
h1{font-size:22px;font-weight:700;color:#fff;letter-spacing:-.02em}
h2{font-size:15px;font-weight:600;color:#fff;margin-bottom:4px}
.sub{font-size:11px;color:#444;margin-bottom:18px}
.mono{font-family:'JetBrains Mono',monospace;font-size:11px;background:rgba(255,255,255,.04);padding:1px 5px;border-radius:3px;color:#7dd3fc}
.card{background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:18px}
.badge{display:inline-block;padding:2px 8px;border-radius:16px;font-size:10px;font-weight:600}
.badge-ok{background:rgba(16,185,129,.12);color:#34d399}
.badge-off{background:rgba(239,68,68,.12);color:#f87171}
.badge-purple{background:rgba(139,92,246,.12);color:#a78bfa}
.btn{padding:8px 16px;border:none;border-radius:10px;font-size:12px;font-weight:600;cursor:pointer;transition:all .2s;font-family:inherit}
.btn-primary{background:linear-gradient(135deg,#3b82f6,#2563eb);color:#fff}
.btn-ghost{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);color:#888}
.btn-blue{background:rgba(59,130,246,.1);border:1px solid rgba(59,130,246,.2);color:#60a5fa}
.btn-purple{background:rgba(139,92,246,.1);border:1px solid rgba(139,92,246,.2);color:#a78bfa}
.btn-sm{padding:5px 10px;font-size:11px;border-radius:7px;border:none;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06)}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:24px}
.stat{background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:16px 14px}
.stat-label{font-size:10px;color:#444;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px}
.stat-val{font-size:24px;font-weight:700}
.tabs{display:flex;gap:2px;margin-bottom:22px;background:rgba(255,255,255,.02);border-radius:12px;padding:4px;border:1px solid rgba(255,255,255,.05)}
.tab{flex:1;display:flex;align-items:center;justify-content:center;gap:6px;padding:10px 14px;border-radius:10px;border:none;cursor:pointer;font-size:12px;font-weight:600;background:transparent;color:#444;transition:all .2s;font-family:inherit}
.tab.active{background:rgba(59,130,246,.15);color:#60a5fa}
.url-box{display:flex;align-items:center;gap:8px;background:rgba(0,0,0,.3);border-radius:8px;padding:9px 14px;border:1px solid rgba(255,255,255,.05)}
.url-box code{flex:1;font-size:12px;color:#60a5fa;font-family:'JetBrains Mono',monospace;word-break:break-all}
pre.code{background:rgba(0,0,0,.35);border:1px solid rgba(255,255,255,.05);border-radius:10px;padding:14px;overflow:auto;font-size:11px;font-family:'JetBrains Mono',monospace;color:#7dd3fc;line-height:1.7;white-space:pre-wrap;word-break:break-all}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.form-group label{display:block;font-size:10px;color:#444;margin-bottom:4px;text-transform:uppercase;letter-spacing:.05em;font-weight:600}
.form-group input,.form-group select{width:100%;background:rgba(0,0,0,.4);border:1px solid rgba(255,255,255,.08);border-radius:8px;padding:9px 12px;color:#c8ccd4;font-size:13px;outline:none;font-family:inherit}
.form-group input:focus{border-color:#3b82f6}
.modal-bg{position:fixed;inset:0;z-index:9998;background:rgba(0,0,0,.7);backdrop-filter:blur(4px);display:flex;align-items:center;justify-content:center}
.modal{background:#12141a;border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:26px;width:500px;max-height:90vh;overflow:auto;box-shadow:0 24px 80px rgba(0,0,0,.6)}
.toggle{width:34px;height:18px;border-radius:9px;position:relative;cursor:pointer;transition:all .2s}
.toggle .knob{width:14px;height:14px;border-radius:50%;background:#fff;position:absolute;top:2px;transition:left .2s}
.toast{position:fixed;top:20px;right:20px;z-index:9999;padding:12px 20px;border-radius:10px;font-size:13px;font-weight:600;box-shadow:0 8px 32px rgba(0,0,0,.4);animation:slideIn .3s ease}
.toast-ok{background:#0c2d1f;color:#34d399;border:1px solid #166534}
.toast-err{background:#2d0f0f;color:#f87171;border:1px solid #7f1d1d}
.hidden{display:none}
.int-row{background:rgba(255,255,255,.02);border:1px solid rgba(59,130,246,.12);border-radius:12px;padding:14px 18px;margin-bottom:8px;transition:all .2s}
.int-row.inactive{opacity:.45;border-color:rgba(255,255,255,.04)}
.step-num{min-width:18px;height:18px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:700}
.diag-card{background:rgba(255,255,255,.02);border-radius:12px;padding:14px 16px}
.flow-step{padding:6px 12px;border-radius:7px;font-size:11px;font-weight:500;border:1px solid rgba(59,130,246,.12);color:#60a5fa;white-space:nowrap}
@keyframes slideIn{from{transform:translateX(20px);opacity:0}to{transform:translateX(0);opacity:1}}
@media(max-width:768px){.stats{grid-template-columns:repeat(2,1fr)}.form-grid{grid-template-columns:1fr}.tabs{flex-wrap:wrap}}
</style>
</head>
<body>
<div class="grid-bg"></div>
<div class="wrap">

<!-- HEADER -->
<div style="margin-bottom:28px">
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:4px">
    <div style="width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#3b82f6,#8b5cf6);display:flex;align-items:center;justify-content:center;color:#fff">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
    </div>
    <h1>DataHooks Tracking</h1>
    <span class="badge" id="status-badge" style="font-size:11px;padding:3px 10px">...</span>
  </div>
  <p style="font-size:12px;color:#444;margin-left:48px">track.datahooksbr.com — Multi-domínio GA4 + GTM SS + RedTrack</p>
</div>

<!-- STATS -->
<div class="stats">
  <div class="stat"><div class="stat-label">Integrações Ativas</div><div class="stat-val" id="st-active" style="color:#3b82f6">—</div></div>
  <div class="stat"><div class="stat-label">Domínios</div><div class="stat-val" id="st-domains" style="color:#8b5cf6">—</div></div>
  <div class="stat"><div class="stat-label">Database</div><div class="stat-val" id="st-db" style="color:#666">—</div></div>
  <div class="stat"><div class="stat-label">GTM SS</div><div class="stat-val" id="st-gtm" style="color:#666">—</div></div>
</div>

<!-- TABS -->
<div class="tabs">
  <button class="tab active" data-tab="domains" onclick="switchTab('domains')">🌐 Domínios</button>
  <button class="tab" data-tab="webhooks" onclick="switchTab('webhooks')">⚡ Webhooks</button>
  <button class="tab" data-tab="tracker" onclick="switchTab('tracker')">📝 Tracker.js</button>
  <button class="tab" data-tab="diag" onclick="switchTab('diag')">📊 Diagnóstico</button>
  <button class="tab" data-tab="config" onclick="switchTab('config')">⚙️ Config</button>
</div>

<!-- TAB CONTENT -->
<div id="tab-domains"></div>
<div id="tab-webhooks" class="hidden"></div>
<div id="tab-tracker" class="hidden"></div>
<div id="tab-diag" class="hidden"></div>
<div id="tab-config" class="hidden"></div>

<!-- MODAL -->
<div class="modal-bg hidden" id="modal-bg" onclick="closeModal()">
  <div class="modal" onclick="event.stopPropagation()">
    <h2 id="modal-title" style="font-size:17px;margin-bottom:18px">Nova Integração GA4</h2>
    <div class="form-grid">
      <div class="form-group"><label>Nome do Funil</label><input id="f-name" placeholder="Ex: VSL Principal"></div>
      <div class="form-group"><label>Domínio (sem https://)</label><input id="f-domain" placeholder="Ex: vendas.meusite.com"></div>
      <div class="form-group"><label>Path (opcional)</label><input id="f-path" placeholder="Ex: /lp/vsl1"></div>
      <div class="form-group"><label>GA4 Measurement ID</label><input id="f-mid" placeholder="G-XXXXXXXXXX"></div>
      <div class="form-group"><label>GA4 API Secret</label><input id="f-secret" placeholder="Measurement Protocol secret"></div>
      <div class="form-group">
        <label>GTM Server-Side</label>
        <select id="f-gtm"><option value="false">Desabilitado</option><option value="true">Habilitado</option></select>
      </div>
    </div>
    <div style="display:flex;gap:8px;margin-top:20px;justify-content:flex-end">
      <button class="btn btn-ghost" onclick="closeModal()">Cancelar</button>
      <button class="btn btn-primary" onclick="saveIntegration()">Salvar</button>
    </div>
  </div>
</div>

<!-- TOAST -->
<div class="toast hidden" id="toast"></div>

</div>

<script>
var API = '';  // Mesmo domínio
var HOST = location.origin;
var integrations = [];
var editingId = null;
var health = null;

// ═══════ UTILS ═══════
function esc(s){if(!s)return'';var d=document.createElement('div');d.textContent=s;return d.innerHTML}
function toast(msg,ok){var t=document.getElementById('toast');t.textContent=msg;t.className='toast '+(ok?'toast-ok':'toast-err');setTimeout(function(){t.className='toast hidden'},3500)}
function copyText(text,btn){navigator.clipboard.writeText(text).then(function(){var orig=btn.innerHTML;btn.innerHTML='✓ Copiado';btn.style.color='#34d399';setTimeout(function(){btn.innerHTML=orig;btn.style.color=''},2000)})}

function switchTab(id){
  document.querySelectorAll('[data-tab]').forEach(function(t){t.classList.toggle('active',t.dataset.tab===id)});
  ['domains','webhooks','tracker','diag','config'].forEach(function(t){document.getElementById('tab-'+t).classList.toggle('hidden',t!==id)});
  if(id==='diag')renderDiag();
  if(id==='webhooks')renderWebhooks();
  if(id==='tracker')renderTracker();
  if(id==='config')renderConfig();
}

// ═══════ API ═══════
function apiFetch(path,opts){
  opts=opts||{};
  opts.headers=Object.assign({'Content-Type':'application/json'},opts.headers||{});
  return fetch(API+path,opts).then(function(r){if(!r.ok)throw new Error('HTTP '+r.status);return r.json()});
}

// ═══════ LOAD ═══════
function loadAll(){
  apiFetch('/admin/ga4/integrations').then(function(d){integrations=d;renderDomains();updateStats()}).catch(function(e){toast('Erro: '+e.message,false)});
  apiFetch('/diag/health').then(function(d){health=d;updateHealth()}).catch(function(){health=null;updateHealth()});
}

function updateStats(){
  var active=integrations.filter(function(i){return i.is_active}).length;
  var domains=[...new Set(integrations.map(function(i){return i.domain}))].length;
  document.getElementById('st-active').textContent=active;
  document.getElementById('st-domains').textContent=domains;
}

function updateHealth(){
  var b=document.getElementById('status-badge');
  if(!health){b.textContent='OFFLINE';b.className='badge badge-off';return}
  var ok=health.all_ok;
  b.textContent=ok?'ONLINE':'DEGRADED';
  b.className='badge '+(ok?'badge-ok':'badge-off');
  b.style.fontSize='11px';b.style.padding='3px 10px';
  var db=health.db&&health.db.ok;
  var gtm=health.gtm_ss&&health.gtm_ss.ok;
  document.getElementById('st-db').textContent=db?'OK':'OFF';
  document.getElementById('st-db').style.color=db?'#10b981':'#ef4444';
  document.getElementById('st-gtm').textContent=gtm?'OK':'OFF';
  document.getElementById('st-gtm').style.color=gtm?'#10b981':'#ef4444';
}

// ═══════ DOMAINS TAB ═══════
function renderDomains(){
  var c=document.getElementById('tab-domains');
  var html='<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">';
  html+='<div><h2>Integrações GA4 por Domínio</h2><p class="sub">Cada domínio/funil usa suas próprias credenciais GA4</p></div>';
  html+='<button class="btn btn-primary" onclick="openModal()">+ Novo Domínio</button></div>';

  if(!integrations.length){
    html+='<div class="card" style="text-align:center;padding:50px"><p style="color:#444;font-size:13px">Nenhuma integração cadastrada. Usando fallback do .env</p>';
    html+='<button class="btn btn-blue" style="margin-top:12px" onclick="openModal()">Cadastrar primeira integração</button></div>';
  } else {
    integrations.forEach(function(i){
      var cls=i.is_active?'int-row':'int-row inactive';
      html+='<div class="'+cls+'">';
      html+='<div style="display:flex;justify-content:space-between;align-items:flex-start">';
      html+='<div style="flex:1">';
      html+='<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">';
      html+='<span style="font-size:14px;font-weight:600;color:#fff">'+esc(i.name)+'</span>';
      html+='<span class="badge '+(i.is_active?'badge-ok':'badge-off')+'">'+(i.is_active?'ATIVO':'INATIVO')+'</span>';
      if(i.use_gtm_server)html+='<span class="badge badge-purple">GTM SS</span>';
      html+='</div>';
      html+='<div style="display:flex;gap:20px;flex-wrap:wrap;font-size:12px">';
      html+='<span><span style="color:#444">Domínio:</span> <span style="color:#8899aa">'+esc(i.domain)+'</span></span>';
      html+='<span><span style="color:#444">Path:</span> <span style="color:#8899aa">'+(i.page_path||'/*')+'</span></span>';
      html+='<span><span style="color:#444">MID:</span> <span class="mono">'+esc(i.measurement_id)+'</span></span>';
      html+='</div></div>';
      html+='<div style="display:flex;gap:5px;margin-left:12px">';
      html+='<button class="btn-sm" style="color:#60a5fa" onclick="editRow('+i.id+')">✏️</button>';
      html+='<button class="btn-sm" style="color:'+(i.is_active?'#f59e0b':'#34d399')+'" onclick="toggleRow('+i.id+','+!i.is_active+')">'+(i.is_active?'⏸':'▶')+'</button>';
      html+='<button class="btn-sm" style="color:#f87171" onclick="deleteRow('+i.id+')">🗑</button>';
      html+='</div></div></div>';
    });
  }
  c.innerHTML=html;
}

// ═══════ WEBHOOKS TAB ═══════
function renderWebhooks(){
  var c=document.getElementById('tab-webhooks');
  var whs=[
    {name:'CartPanda',emoji:'🛒',color:'#10b981',url:HOST+'/webhook/cartpanda',params:'GET: cid, clickid, order_id, amount_net, amount | JSON: custom.rtkcid',
     steps:['CartPanda → Configurações → Webhooks','Cole o URL acima como webhook','Evento: Pedido Pago','Garanta que o clickid está em custom.rtkcid ou ?cid=XXX']},
    {name:'ClickBank',emoji:'💰',color:'#8b5cf6',url:HOST+'/webhook/clickbank',params:'GET: clickid | JSON: clickid, payout, order_id',
     steps:['ClickBank → Settings → Advanced Tools','Cole como Instant Notification URL','Passe clickid via: ?clickid={clickid}','IPN envia payout e order_id no JSON body']}
  ];
  var html='<h2>Webhooks de Conversão</h2><p class="sub">URLs para receber notificações de venda</p>';
  whs.forEach(function(w){
    html+='<div class="card" style="margin-bottom:14px;padding:22px">';
    html+='<div style="display:flex;align-items:center;gap:8px;margin-bottom:14px"><span style="font-size:22px">'+w.emoji+'</span><h3 style="font-size:15px;font-weight:600;color:'+w.color+'">'+w.name+'</h3></div>';
    html+='<div class="url-box" style="margin-bottom:10px"><code>'+w.url+'</code><button class="btn btn-ghost" style="padding:4px 10px;font-size:11px" onclick="copyText(\''+w.url+'\',this)">📋 Copiar</button></div>';
    html+='<p style="font-size:11px;color:#444;font-family:\'JetBrains Mono\',monospace;margin-bottom:14px">'+w.params+'</p>';
    html+='<div style="border-top:1px solid rgba(255,255,255,.04);padding-top:12px"><p style="font-size:11px;font-weight:600;color:#666;margin-bottom:8px">Setup:</p>';
    w.steps.forEach(function(s,i){
      html+='<div style="display:flex;gap:8px;margin-bottom:5px;font-size:12px;color:#555"><span class="step-num" style="background:'+w.color+'18;color:'+w.color+'">'+(i+1)+'</span>'+esc(s)+'</div>';
    });
    html+='</div></div>';
  });
  // Flow
  html+='<div class="card" style="margin-top:20px;padding:20px"><h3 style="font-size:13px;font-weight:600;color:#fff;margin-bottom:14px">Fluxo de Conversão</h3>';
  html+='<div style="display:flex;align-items:center;justify-content:center;gap:6px;flex-wrap:wrap">';
  ['Visitor na LP','tracker.js → Redis','Compra','Webhook','Resolve GA4','GA4 + GTM + RedTrack'].forEach(function(s,i){
    html+='<span class="flow-step" style="background:rgba(59,130,246,'+(0.04+i*0.025)+')">'+s+'</span>';
    if(i<5)html+='<span style="color:#222">→</span>';
  });
  html+='</div></div>';
  c.innerHTML=html;
}

// ═══════ TRACKER TAB ═══════
function renderTracker(){
  var c=document.getElementById('tab-tracker');
  var snippet='<script>window.GA4_TRACKER_URL = "'+HOST+'";<\/script>\n<script src="'+HOST+'/static/tracker.js" defer><\/script>';
  var vsl='// Tracking de progresso VSL\nwindow.trackVslProgress(25, 45.2);  // 25%\nwindow.trackVslProgress(50, 90.5);  // 50%\nwindow.trackVslProgress(75, 135.8); // 75%\nwindow.trackVslProgress(100, 180);  // 100%';

  var html='<h2>Instalação do Tracker</h2><p class="sub">Cole no HEAD de cada LP/VSL. O tracker detecta o domínio e resolve a conta GA4 certa.</p>';
  html+=codeBlock('1. Snippet (HEAD da LP)',snippet);
  html+=codeBlock('2. VSL Progress (opcional)',vsl);
  html+='<div class="card" style="margin-top:18px;background:rgba(245,158,11,.05);border-color:rgba(245,158,11,.12)">';
  html+='<h4 style="font-size:12px;font-weight:600;color:#f59e0b;margin-bottom:6px">Como funciona o multi-domínio</h4>';
  html+='<p style="font-size:11px;color:#777;line-height:1.7">O tracker.js envia o <span class="mono">page_location</span> completo. O backend extrai domínio+path, busca na tabela <span class="mono">ga4_integrations</span> por match exato → genérico → fallback .env. Cada domínio pode ter sua própria conta GA4.</p></div>';
  c.innerHTML=html;
}

function codeBlock(title,code){
  var id='cb-'+Math.random().toString(36).substr(2,6);
  var h='<div style="margin-bottom:14px">';
  h+='<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px"><span style="font-size:12px;font-weight:600;color:#777">'+title+'</span>';
  h+='<button class="btn btn-ghost" style="padding:4px 10px;font-size:11px" onclick="copyText(document.getElementById(\''+id+'\').textContent,this)">📋 Copiar</button></div>';
  h+='<pre class="code" id="'+id+'">'+esc(code)+'</pre></div>';
  return h;
}

// ═══════ DIAG TAB ═══════
function renderDiag(){
  var c=document.getElementById('tab-diag');
  var html='<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px"><h2>Diagnóstico do Sistema</h2>';
  html+='<button class="btn btn-ghost" onclick="loadAll()">🔄 Atualizar</button></div>';

  if(health){
    var comps=[
      {n:'API',ok:health.api&&health.api.ok,d:'FastAPI rodando'},
      {n:'Postgres',ok:health.db&&health.db.ok,d:health.db&&health.db.ok?'Conectado':(health.db&&health.db.reason||'Erro')},
      {n:'Redis',ok:health.redis&&health.redis.ok,d:health.redis&&health.redis.ok?'Conectado':(health.redis&&health.redis.reason||'Erro')},
      {n:'GTM SS',ok:health.gtm_ss&&health.gtm_ss.ok,d:health.gtm_ss&&health.gtm_ss.ok?(health.gtm_ss.url||'OK'):(health.gtm_ss&&health.gtm_ss.reason||'Não configurado')}
    ];
    html+='<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px">';
    comps.forEach(function(x){
      html+='<div class="diag-card" style="border:1px solid '+(x.ok?'rgba(16,185,129,.15)':'rgba(239,68,68,.15)')+'">';
      html+='<div style="display:flex;align-items:center;gap:6px;margin-bottom:6px"><div style="width:8px;height:8px;border-radius:50%;background:'+(x.ok?'#34d399':'#ef4444')+'"></div>';
      html+='<span style="font-size:13px;font-weight:600;color:#fff">'+x.n+'</span></div>';
      html+='<p style="font-size:11px;color:#555;word-break:break-all">'+esc(x.d)+'</p></div>';
    });
    html+='</div>';

    // Config vars
    if(health.config){
      html+='<div class="card" style="margin-bottom:16px"><h3 style="font-size:13px;font-weight:600;color:#fff;margin-bottom:12px">Variáveis Configuradas</h3>';
      html+='<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">';
      Object.keys(health.config).forEach(function(k){
        var v=health.config[k];
        var ok=typeof v==='string'?!!v:v;
        html+='<div style="display:flex;justify-content:space-between;padding:6px 10px;background:rgba(0,0,0,.2);border-radius:6px;font-size:11px">';
        html+='<span class="mono">'+k+'</span><span style="color:'+(ok?'#34d399':'#ef4444')+';font-weight:600">'+(typeof v==='string'?(v||'vazio'):(v?'OK':'FALTA'))+'</span></div>';
      });
      html+='</div></div>';
    }
  } else {
    html+='<p style="color:#555;padding:20px">Carregando diagnóstico...</p>';
  }

  html+='<div style="display:flex;gap:10px;margin-bottom:16px">';
  html+='<button class="btn btn-blue" style="flex:1;padding:12px" onclick="testGA4()">🧪 Testar GA4 Measurement Protocol</button>';
  html+='<button class="btn btn-purple" style="flex:1;padding:12px" onclick="testGTM()">🧪 Testar GTM Server-Side</button></div>';

  var curlCode='# Health completo\ncurl '+HOST+'/diag/health\n\n# Teste GA4\ncurl -X POST '+HOST+'/diag/ga4/test\n\n# Teste GTM SS\ncurl -X POST '+HOST+'/diag/gtm/test\n\n# Teste CartPanda\ncurl "'+HOST+'/webhook/cartpanda?clickid=TEST123&order_id=ORD-001&amount=97.00"\n\n# Teste ClickBank\ncurl -X POST '+HOST+'/webhook/clickbank \\\n  -H "Content-Type: application/json" \\\n  -d \'{"clickid":"TEST456","order_id":"CB-001","payout":47.00}\'';
  html+='<div class="card">'+codeBlock('Testes via curl',curlCode)+'</div>';
  c.innerHTML=html;
}

function testGA4(){
  toast('Enviando teste GA4...',true);
  apiFetch('/diag/ga4/test',{method:'POST'}).then(function(r){toast(r.ok?'GA4 OK (status '+r.ga4_status+')':'GA4 falhou: status '+r.ga4_status,r.ok)}).catch(function(e){toast('Erro: '+e.message,false)});
}
function testGTM(){
  toast('Enviando teste GTM SS...',true);
  apiFetch('/diag/gtm/test',{method:'POST'}).then(function(r){toast(r.ok?'GTM SS OK (status '+r.status_code+')':'GTM falhou: '+(r.reason||r.status_code),r.ok)}).catch(function(e){toast('Erro: '+e.message,false)});
}

// ═══════ CONFIG TAB ═══════
function renderConfig(){
  var c=document.getElementById('tab-config');
  var vars=[
    {k:'GA4_MEASUREMENT_ID',d:'Fallback global (quando nenhuma integração bate)',ex:'G-XXXXXXXXXX'},
    {k:'GA4_API_SECRET',d:'API Secret do fallback',ex:'xxxxxxxx'},
    {k:'USE_GTM_SERVER',d:'Habilita envio GTM SS',ex:'true'},
    {k:'GTM_SERVER_URL',d:'URL do container GTM SS',ex:'http://host.docker.internal:8081'},
    {k:'REDTRACK_POSTBACK',d:'URL base postback RedTrack',ex:'https://domain.rdtk.io/postback'},
    {k:'GA4_DEBUG',d:'Modo debug (log detalhado)',ex:'false em produção'},
    {k:'DB_HOST',d:'Host Postgres (docker)',ex:'db'},
    {k:'REDIS_HOST',d:'Host Redis',ex:'redis'}
  ];
  var html='<h2>Variáveis de Ambiente (.env)</h2><p class="sub">Configure no arquivo .env na raiz do projeto</p>';
  html+='<div class="card" style="padding:0;overflow:hidden">';
  vars.forEach(function(v){
    html+='<div style="display:grid;grid-template-columns:220px 1fr 180px;padding:10px 18px;border-bottom:1px solid rgba(255,255,255,.03);align-items:center;font-size:12px">';
    html+='<span class="mono">'+v.k+'</span><span style="color:#555">'+v.d+'</span><span style="color:#444;font-family:\'JetBrains Mono\',monospace;font-size:11px">'+v.ex+'</span></div>';
  });
  html+='</div>';
  c.innerHTML=html;
}

// ═══════ MODAL / CRUD ═══════
function openModal(item){
  editingId=item?item.id:null;
  document.getElementById('modal-title').textContent=item?'Editar: '+item.name:'Nova Integração GA4';
  document.getElementById('f-name').value=item?item.name:'';
  document.getElementById('f-domain').value=item?item.domain:'';
  document.getElementById('f-path').value=item?item.page_path||'':'';
  document.getElementById('f-mid').value=item?item.measurement_id:'';
  document.getElementById('f-secret').value=item?item.api_secret:'';
  document.getElementById('f-gtm').value=item&&item.use_gtm_server?'true':'false';
  document.getElementById('modal-bg').classList.remove('hidden');
}
function closeModal(){document.getElementById('modal-bg').classList.add('hidden');editingId=null}

function saveIntegration(){
  var body={
    name:document.getElementById('f-name').value.trim(),
    domain:document.getElementById('f-domain').value.trim(),
    page_path:document.getElementById('f-path').value.trim(),
    measurement_id:document.getElementById('f-mid').value.trim(),
    api_secret:document.getElementById('f-secret').value.trim(),
    use_gtm_server:document.getElementById('f-gtm').value==='true'
  };
  if(!body.name||!body.domain||!body.measurement_id||!body.api_secret){toast('Preencha nome, domínio, MID e API Secret',false);return}
  var method=editingId?'PUT':'POST';
  var url=editingId?'/admin/ga4/integrations/'+editingId:'/admin/ga4/integrations';
  apiFetch(url,{method:method,body:JSON.stringify(body)}).then(function(){
    toast(editingId?'Atualizado!':'Criado!',true);closeModal();loadAll();
  }).catch(function(e){toast('Erro: '+e.message,false)});
}

function editRow(id){
  var item=integrations.find(function(i){return i.id===id});
  if(item)openModal(item);
}
function toggleRow(id,newState){
  apiFetch('/admin/ga4/integrations/'+id,{method:'PUT',body:JSON.stringify({is_active:newState})}).then(function(){
    toast(newState?'Ativado!':'Desativado!',true);loadAll();
  }).catch(function(e){toast('Erro: '+e.message,false)});
}
function deleteRow(id){
  if(!confirm('Excluir esta integração?'))return;
  apiFetch('/admin/ga4/integrations/'+id,{method:'DELETE'}).then(function(){
    toast('Excluído!',true);loadAll();
  }).catch(function(e){toast('Erro: '+e.message,false)});
}

// ═══════ INIT ═══════
loadAll();
</script>
</body>
</html>"""
