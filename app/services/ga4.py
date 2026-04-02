"""
GA4 Service — Measurement Protocol + GTM Server-Side

Envia eventos para Google Analytics 4 via Measurement Protocol.
Opcionalmente replica para GTM Server-Side via /g/collect (formato gtag v2),
que é o formato nativo que o GA4 Client do GTM SS reconhece.

═══════════════════════════════════════════════════════════════════
 Por que /g/collect e não JSON puro?
═══════════════════════════════════════════════════════════════════
 O container GTM Server-Side usa "Clients" para capturar requests.
 O GA4 Client (pré-instalado) só reconhece requests no formato
 que o gtag.js envia — endpoint /g/collect com parâmetros
 codificados em query string + body URL-encoded.

 Um POST de JSON puro na raiz do GTM SS é IGNORADO silenciosamente
 (nenhum Client "claims" o request → retorna 200 mas não processa).

 Formato que o GA4 Client espera:
   POST /g/collect?v=2&tid=G-XXXXX&cid=CLIENT_ID&_p=RANDOM
   Body: en=event_name&sid=SESSION_ID&ep.param=value&epn.num=123
═══════════════════════════════════════════════════════════════════
"""
import os
import random
import logging
from urllib.parse import urlencode
from typing import Optional

import requests as http_requests

logger = logging.getLogger(__name__)

# ── Credenciais globais (fallback do .env) ───────────────────────
GA4_MEASUREMENT_ID = os.getenv("GA4_MEASUREMENT_ID", "")
GA4_API_SECRET = os.getenv("GA4_API_SECRET", "")
GA4_DEBUG = os.getenv("GA4_DEBUG", "false").lower() in ("true", "1", "yes")

# ── GTM Server-Side ─────────────────────────────────────────────
USE_GTM_SERVER = os.getenv("USE_GTM_SERVER", "false").lower() in ("true", "1", "yes")
GTM_SERVER_URL = os.getenv("GTM_SERVER_URL", "").rstrip("/")

# ── URLs Measurement Protocol ───────────────────────────────────
_URL_PROD = "https://www.google-analytics.com/mp/collect"
_URL_DEBUG = "https://www.google-analytics.com/debug/mp/collect"


def _ga4_url(measurement_id: str = None, api_secret: str = None) -> str:
    mid = measurement_id or GA4_MEASUREMENT_ID
    secret = api_secret or GA4_API_SECRET
    base = _URL_DEBUG if GA4_DEBUG else _URL_PROD
    return f"{base}?measurement_id={mid}&api_secret={secret}"


# ═══════════════════════════════════════════════════════════════════
#  GTM SERVER-SIDE — Formato /g/collect (gtag v2)
# ═══════════════════════════════════════════════════════════════════

def _build_gtm_request(
    client_id: str,
    session_id: str,
    event_name: str,
    params: dict,
    measurement_id: str,
) -> tuple[str, str]:
    """
    Converte payload Measurement Protocol → formato /g/collect
    que o GA4 Client nativo do GTM Server-Side reconhece.

    Retorna (url_com_query, body_urlencoded).

    Mapeamento:
      Strings  → ep.nome=valor  (event parameter string)
      Números  → epn.nome=valor (event parameter numeric)
      Listas   → ignorados

    Parâmetros reservados gtag v2:
      v=2, tid, cid, _p, en, sid, _et, _s, _ee
    """
    # ── Query params (identificação) ─────────────────────────────
    query = {
        "v": "2",
        "tid": measurement_id,
        "cid": client_id,
        "_p": str(random.randint(100000000, 999999999)),
    }
    url = f"{GTM_SERVER_URL}/g/collect?{urlencode(query)}"

    # ── Body URL-encoded (dados do evento) ───────────────────────
    body_params = {
        "en": event_name,
        "sid": session_id,
        "_et": params.get("engagement_time_msec", "100"),
        "_s": "1",
        "_ee": "1",  # sinaliza que é um evento engajado
    }

    # Params que já foram mapeados acima → não duplicar com prefixo ep./epn.
    _SKIP_KEYS = {"session_id", "engagement_time_msec"}

    for key, val in params.items():
        if key in _SKIP_KEYS or key == "items" or val is None:
            continue

        if isinstance(val, bool):
            body_params[f"ep.{key}"] = "true" if val else "false"
        elif isinstance(val, (int, float)):
            body_params[f"epn.{key}"] = str(val)
        elif isinstance(val, str):
            body_params[f"ep.{key}"] = val

    # ── E-commerce items ─────────────────────────────────────────
    # Formato gtag: pr1=idPROD~nmNome~pr97.00~qt1
    items = params.get("items")
    if items and isinstance(items, list):
        for idx, item in enumerate(items, 1):
            parts = []
            if item.get("item_id"):
                parts.append(f"id{item['item_id']}")
            if item.get("item_name"):
                parts.append(f"nm{item['item_name']}")
            if item.get("price") is not None:
                parts.append(f"pr{item['price']}")
            if item.get("quantity") is not None:
                parts.append(f"qt{item['quantity']}")
            if item.get("item_category"):
                parts.append(f"ca{item['item_category']}")
            if parts:
                body_params[f"pr{idx}"] = "~".join(parts)

    # ── Transaction-level e-commerce ─────────────────────────────
    # transaction_id e value vão como ep/epn normais (já tratados acima)
    # currency precisa de mapeamento especial no gtag v2
    currency = params.get("currency")
    if currency:
        body_params["cu"] = currency

    return url, urlencode(body_params)


def _forward_to_gtm(
    client_id: str,
    session_id: str,
    event_name: str,
    params: dict,
    measurement_id: str,
    use_gtm: bool = None,
) -> Optional[int]:
    """
    Encaminha evento para GTM Server-Side no formato /g/collect.
    Retorna status_code ou None se GTM SS desabilitado/não configurado.
    """
    should_send = use_gtm if use_gtm is not None else USE_GTM_SERVER
    if not should_send or not GTM_SERVER_URL:
        return None

    try:
        url, body = _build_gtm_request(
            client_id=client_id,
            session_id=session_id,
            event_name=event_name,
            params=params,
            measurement_id=measurement_id,
        )

        resp = http_requests.post(
            url,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )

        logger.info(
            "GTM SS | event=%s | mid=%s | status=%s | url=%s",
            event_name, measurement_id, resp.status_code, url,
        )

        if resp.status_code >= 400:
            logger.warning(
                "GTM SS resposta inesperada | status=%s | body=%s",
                resp.status_code, resp.text[:300] if resp.text else "",
            )

        return resp.status_code

    except http_requests.RequestException as e:
        logger.error("GTM SS erro de conexão: %s", e)
        return 500


# ═══════════════════════════════════════════════════════════════════
#  SEND EVENT — Ponto de entrada principal
# ═══════════════════════════════════════════════════════════════════

def send_event(
    client_id: str,
    session_id: str,
    event_name: str,
    params: dict,
    *,
    measurement_id: str = None,
    api_secret: str = None,
    use_gtm_server: bool = None,
    creds_source: str = None,
) -> tuple[int, Optional[int]]:
    """
    Envia evento para GA4 Measurement Protocol + GTM Server-Side.
    Retorna (ga4_status, gtm_status_ou_None).
    """
    # Params obrigatórios GA4
    params["session_id"] = session_id
    params.setdefault("engagement_time_msec", "100")

    payload = {
        "client_id": client_id,
        "events": [{"name": event_name, "params": params}],
    }

    mid = measurement_id or GA4_MEASUREMENT_ID
    src = creds_source or ("override" if measurement_id else "env")
    logger.info("GA4 send | creds=%s | mid=%s | event=%s", src, mid, event_name)

    # ── 1. GA4 Measurement Protocol ─────────────────────────────
    ga4_status = 500
    try:
        resp = http_requests.post(
            _ga4_url(measurement_id, api_secret), json=payload, timeout=10
        )
        ga4_status = resp.status_code
        logger.info(
            "GA4 %s | event=%s | client=%s | mid=%s | status=%s | body=%s",
            "DEBUG" if GA4_DEBUG else "PROD",
            event_name, client_id, mid,
            resp.status_code,
            resp.text[:500] if resp.text else "",
        )
    except http_requests.RequestException as e:
        logger.error("GA4 MP erro: %s", e)

    # ── 2. GTM Server-Side (/g/collect) ─────────────────────────
    gtm_status = _forward_to_gtm(
        client_id=client_id,
        session_id=session_id,
        event_name=event_name,
        params=params,
        measurement_id=mid,
        use_gtm=use_gtm_server,
    )

    return ga4_status, gtm_status


# ═══════════════════════════════════════════════════════════════════
#  HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════

def gtm_health_check() -> dict:
    """Verifica se o container GTM Server-Side está respondendo."""
    if not GTM_SERVER_URL:
        return {"ok": False, "reason": "GTM_SERVER_URL não configurado", "url": ""}

    try:
        resp = http_requests.get(f"{GTM_SERVER_URL}/healthz", timeout=5)
        return {
            "ok": resp.status_code < 500,
            "status_code": resp.status_code,
            "url": GTM_SERVER_URL,
        }
    except http_requests.RequestException as e:
        return {"ok": False, "reason": str(e), "url": GTM_SERVER_URL}
