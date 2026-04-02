# RedTrack · GA4 · GTM — Multi-Domain Tracking System

Sistema de tracking server-side que integra **Google Analytics 4**, **GTM Server-Side**, e **RedTrack** com suporte a múltiplos domínios/funis.

## Arquitetura

```
Visitor (LP/VSL)
    │
    │  tracker.js (page_view, scroll, cta_click, vsl_progress)
    ▼
┌──────────────────────────┐
│  FastAPI Backend (:8000)  │
│                          │
│  /ga4/event ──────────── │──► Redis (visitor store, 30 dias)
│                          │
│  /webhook/cartpanda ──── │──► Postgres (conversions + dedup)
│  /webhook/clickbank ──── │    │
│                          │    ├──► GA4 Measurement Protocol
│  /admin/ga4/ ─────────── │    ├──► GTM Server-Side (/g/collect)
│  /admin/gtm/ ─────────── │    └──► RedTrack Postback (via RQ)
│  /diag/ ──────────────── │
└──────────────────────────┘
```

## Deploy Rápido

```bash
# 1. Configure
cp .env.example .env
# Edite .env com suas credenciais reais

# 2. Suba
docker-compose up -d --build

# 3. Verifique
curl http://localhost:8000/diag/health
```

## Endpoints

### Webhooks
| Endpoint | Descrição |
|----------|-----------|
| `GET/POST /webhook/cartpanda` | Recebe notificação de venda CartPanda |
| `GET/POST /webhook/clickbank` | Recebe IPN do ClickBank |

### Tracking
| Endpoint | Descrição |
|----------|-----------|
| `POST /ga4/event` | Recebe eventos do tracker.js |
| `GET /static/tracker.js` | Script de tracking para LPs |

### Admin
| Endpoint | Descrição |
|----------|-----------|
| `GET /admin/ga4/` | Interface HTML para gerenciar integrações GA4 |
| `GET /admin/ga4/integrations` | API: lista integrações |
| `POST /admin/ga4/integrations` | API: cria integração |
| `PUT /admin/ga4/integrations/{id}` | API: atualiza integração |
| `DELETE /admin/ga4/integrations/{id}` | API: remove integração |

### Diagnósticos
| Endpoint | Descrição |
|----------|-----------|
| `GET /diag/health` | Status de todos os componentes |
| `GET /diag/gtm` | Testa conexão com GTM SS |
| `POST /diag/gtm/test` | Envia evento de teste para GTM SS |
| `POST /diag/ga4/test` | Envia evento de teste para GA4 |
| `GET /diag/redis` | Testa conexão com Redis |
| `GET /diag/db` | Testa conexão com Postgres |

## Multi-Domínio (GA4)

O sistema resolve qual conta GA4 usar baseado no domínio + path da página:

1. **Match exato**: domínio + page_path → usa credenciais específicas
2. **Match genérico**: domínio + path vazio → usa credenciais do domínio
3. **Fallback**: nenhum match → usa `GA4_MEASUREMENT_ID` do `.env`

Cadastre integrações via `GET /admin/ga4/` ou via API.

## GTM Server-Side

O backend envia eventos no formato `/g/collect` (protocolo gtag v2), que é o formato nativo que o GA4 Client do GTM SS reconhece.

### Configuração

1. Crie um container Server no [GTM](https://tagmanager.google.com/)
2. Copie o `CONTAINER_CONFIG` (Admin → Install Tag Manager)
3. Cole no `.env` como `GTM_CONTAINER_CONFIG`
4. Configure `USE_GTM_SERVER=true` e `GTM_SERVER_URL=http://gtm-server:8080`
5. Teste: `curl -X POST http://localhost:8000/diag/gtm/test`

### Verificação

```bash
# Health check do GTM SS
curl http://localhost:8000/diag/gtm

# Evento de teste
curl -X POST http://localhost:8000/diag/gtm/test
```

## Instalação do Tracker

Adicione em cada LP/VSL:

```html
<script>window.GA4_TRACKER_URL = "https://tracking.seudominio.com";</script>
<script src="https://tracking.seudominio.com/static/tracker.js" defer></script>
```

O tracker captura automaticamente: `page_view`, `scroll_depth` (25/50/75/90%), `cta_click`.

Para VSL, chame manualmente:
```javascript
window.trackVslProgress(50, 90.5); // 50% assistido, 90.5 segundos
```

## Webhooks

### CartPanda
Configure em: CartPanda → Configurações → Webhooks
```
URL: https://tracking.seudominio.com/webhook/cartpanda
Evento: Pedido Pago
```
O click_id do RedTrack deve estar no campo `custom.rtkcid` ou na query string `?clickid=XXX`.

### ClickBank
Configure em: ClickBank → Settings → Advanced Tools → Instant Notification URL
```
URL: https://tracking.seudominio.com/webhook/clickbank?clickid={clickid}
```

## Variáveis de Ambiente

Veja `.env.example` para a lista completa com descrições.
