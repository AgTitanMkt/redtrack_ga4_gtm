"""
Conversions — Persistência e dedup de conversões.
Tabelas: conversions (dedup por source+event_id), conversion_logs (dedup por dedupe_key+destination).
"""
import json
import logging
from app.db.connection import get_conn

logger = logging.getLogger(__name__)


def save_conversion(source: str, event_id: str, order_id: str,
                    click_id: str, payout: float, payload: dict) -> bool:
    """
    Salva conversão no banco. Retorna False se duplicada ou erro.
    Dedup: UNIQUE(source, event_id).
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO conversions(source, event_id, order_id, click_id, payout, payload)
            VALUES(%s, %s, %s, %s, %s, %s)
        """, (source, event_id, order_id, click_id, payout, json.dumps(payload)))
        conn.commit()
        logger.info("Conversão salva | source=%s | order=%s | payout=%.2f", source, order_id, payout)
        return True
    except Exception as e:
        conn.rollback()
        logger.warning("Conversão duplicada ou erro | source=%s | order=%s | %s", source, order_id, e)
        return False
    finally:
        conn.close()


def log_delivery(dedupe_key: str, destination: str, status_code: int,
                 event_name: str = None, payload: dict = None) -> bool:
    """
    Registra envio de evento para um destino (redtrack, ga4, gtm_server).
    Dedup: UNIQUE(dedupe_key, destination).
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO conversion_logs(dedupe_key, destination, status_code, event_name, payload)
            VALUES(%s, %s, %s, %s, %s)
        """, (dedupe_key, destination, status_code, event_name,
              json.dumps(payload) if payload else None))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.debug("log_delivery dedup (%s/%s): %s", dedupe_key, destination, e)
        return False
    finally:
        conn.close()


def is_delivered(dedupe_key: str, destination: str) -> bool:
    """Verifica se um evento já foi enviado para determinado destino."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT 1 FROM conversion_logs WHERE dedupe_key = %s AND destination = %s LIMIT 1",
            (dedupe_key, destination),
        )
        return cur.fetchone() is not None
    except Exception as e:
        logger.error("is_delivered erro: %s", e)
        return False
    finally:
        conn.close()
