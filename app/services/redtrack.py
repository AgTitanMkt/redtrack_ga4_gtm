"""
RedTrack Postback Service — Envia conversões para RedTrack.
Executado pelo worker RQ (fila "postbacks").
"""
import os
import logging
import requests

logger = logging.getLogger(__name__)

POSTBACK_URL = os.getenv("REDTRACK_POSTBACK", "")


def send_postback(click_id: str, payout: float, event_type: str = "Purchase",
                  order_id: str = "", dedupe_key: str = None):
    """
    Envia postback para RedTrack.

    Chamado pelo worker RQ — não bloqueia o webhook.
    Se dedupe_key for fornecido, registra no conversion_logs.
    """
    if not POSTBACK_URL:
        logger.error("REDTRACK_POSTBACK não configurado no .env — postback não enviado")
        return

    url = (
        f"{POSTBACK_URL}"
        f"?clickid={click_id}"
        f"&sum={payout}"
        f"&currency=USD"
        f"&eventid={order_id}"
        f"&rdtk_event_id={order_id}"
    )

    logger.info("RedTrack postback | click=%s | payout=%.2f | url=%s", click_id, payout, url)

    status_code = 0
    try:
        r = requests.get(url, timeout=10)
        status_code = r.status_code
        logger.info("RedTrack resposta | status=%s | body=%s", r.status_code, r.text[:200] if r.text else "")
    except requests.RequestException as e:
        logger.error("RedTrack erro de conexão: %s", e)
        status_code = 500

    # Registra delivery no conversion_logs
    if dedupe_key:
        try:
            from app.services.conversions import log_delivery
            log_delivery(dedupe_key, "redtrack", status_code, "purchase")
        except Exception as e:
            logger.warning("Erro ao logar delivery RedTrack: %s", e)
