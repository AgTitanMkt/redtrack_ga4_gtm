"""
Webhook CartPanda — Recebe notificações de venda.
Salva conversão, envia postback RedTrack (via fila), envia GA4 + GTM SS.
"""
import logging
from redis import Redis
from rq import Queue
from fastapi import APIRouter, Request

from app.services.conversions import save_conversion, log_delivery
from app.services import ga4, visitor_store
from app.services.ga4_destinations import resolve_credentials

logger = logging.getLogger(__name__)

router = APIRouter()

redis_conn = Redis(host="redis", port=6379)
q = Queue("postbacks", connection=redis_conn)


@router.get("/cartpanda")
@router.post("/cartpanda")
async def webhook(request: Request):
    logger.info("═══ CARTPANDA WEBHOOK ═══")

    # Tenta ler JSON body
    try:
        data = await request.json()
    except Exception:
        data = {}

    params = dict(request.query_params)

    # ── Extrai campos ────────────────────────────────────────────
    click_id = (
        params.get("cid")
        or params.get("clickid")
        or data.get("custom", {}).get("rtkcid") if isinstance(data.get("custom"), dict) else None
        or data.get("clickid")
    )

    order_id = params.get("order_id") or data.get("id") or data.get("order_id")

    if not order_id:
        logger.warning("CartPanda: sem order_id")
        return {"ok": False, "reason": "no_order_id"}

    event_id = f"purchase_{order_id}"
    dedupe_key = f"cartpanda:{order_id}"

    payout = float(
        params.get("amount_net")
        or params.get("amount_affiliate")
        or params.get("total_price")
        or params.get("amount")
        or data.get("total")
        or 0
    )

    logger.info("CartPanda | order=%s | click=%s | payout=%.2f", order_id, click_id, payout)

    # ── Salva conversão ──────────────────────────────────────────
    ok = save_conversion("cartpanda", event_id, order_id, click_id, payout, data or params)

    if not ok:
        logger.warning("CartPanda: save falhou (duplicado?) order=%s", order_id)
        return {"ok": False, "reason": "save_failed_or_duplicate"}

    # ── RedTrack postback (via fila) ─────────────────────────────
    if click_id:
        q.enqueue(
            "app.services.redtrack.send_postback",
            click_id, payout, "Purchase", order_id, dedupe_key,
        )
        logger.info("CartPanda: postback enfileirado para click=%s", click_id)
    else:
        logger.info("CartPanda: sem click_id, pulando RedTrack")

    # ── GA4 + GTM SS ─────────────────────────────────────────────
    _send_ga4_purchase(click_id, order_id, event_id, dedupe_key, payout, "CartPanda Purchase")

    return {"ok": True}


def _send_ga4_purchase(click_id, order_id, event_id, dedupe_key, payout, item_name):
    """Envia purchase para GA4/GTM SS se o visitor existir no Redis."""
    try:
        visitor = visitor_store.get_visitor(click_id) if click_id else None
        if not visitor:
            logger.info("GA4: visitor '%s' não encontrado no Redis, pulando", click_id)
            return

        ga4_params = {
            "transaction_id": str(order_id),
            "event_id": event_id,
            "value": payout,
            "currency": "USD",
            "items": [{"item_id": str(order_id), "item_name": item_name, "price": payout, "quantity": 1}],
        }

        # Copia UTMs e gclid do visitor
        for f in ("utm_source", "utm_medium", "utm_campaign", "gclid", "page_location"):
            v = visitor.get(f)
            if v:
                ga4_params[f] = v

        creds = resolve_credentials(visitor.get("page_location"))

        ga4_status, gtm_status = ga4.send_event(
            client_id=visitor.get("client_id", "unknown"),
            session_id=visitor.get("session_id", "0"),
            event_name="purchase",
            params=ga4_params,
            measurement_id=creds.measurement_id,
            api_secret=creds.api_secret,
            use_gtm_server=creds.use_gtm_server,
            creds_source=creds.source,
        )

        logger.info(
            "GA4 purchase | order=%s | ga4=%s | gtm=%s | creds=%s",
            order_id, ga4_status, gtm_status, creds.source,
        )

        # Registra delivery
        try:
            log_delivery(dedupe_key, "ga4", ga4_status, "purchase")
            if gtm_status is not None:
                log_delivery(dedupe_key, "gtm_server", gtm_status, "purchase")
        except Exception:
            pass

    except Exception as e:
        logger.error("GA4 purchase erro (não bloqueia RedTrack): %s", e)
