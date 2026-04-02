"""
Rotas de diagnóstico — Health checks e testes de conectividade.
Permite verificar se cada componente está funcionando antes de ir para produção.

Endpoints:
  GET  /diag/health       → Status geral de todos os componentes
  GET  /diag/gtm          → Testa conectividade com GTM Server-Side
  POST /diag/gtm/test     → Envia evento de teste para GTM SS
  POST /diag/ga4/test     → Envia evento de teste para GA4 MP
  GET  /diag/redis        → Testa conectividade com Redis
  GET  /diag/db           → Testa conectividade com Postgres
"""
import os
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/diag", tags=["Diagnostics"])


@router.get("/health")
def full_health():
    """Status geral de todos os componentes."""
    results = {
        "api": {"ok": True},
        "db": _check_db(),
        "redis": _check_redis(),
        "gtm_ss": _check_gtm(),
        "config": {
            "GA4_MEASUREMENT_ID": bool(os.getenv("GA4_MEASUREMENT_ID")),
            "GA4_API_SECRET": bool(os.getenv("GA4_API_SECRET")),
            "REDTRACK_POSTBACK": bool(os.getenv("REDTRACK_POSTBACK")),
            "GTM_SERVER_URL": os.getenv("GTM_SERVER_URL", ""),
            "USE_GTM_SERVER": os.getenv("USE_GTM_SERVER", "false"),
        },
    }
    results["all_ok"] = all(
        results[k].get("ok", False) for k in ("api", "db", "redis")
    )
    return results


@router.get("/gtm")
def gtm_check():
    """Testa conectividade com o container GTM Server-Side."""
    return _check_gtm()


@router.post("/gtm/test")
def gtm_test_event():
    """Envia um evento page_view de teste para o GTM Server-Side."""
    from app.services.ga4 import _forward_to_gtm, GTM_SERVER_URL, GA4_MEASUREMENT_ID

    if not GTM_SERVER_URL:
        return {"ok": False, "reason": "GTM_SERVER_URL não configurado"}

    mid = GA4_MEASUREMENT_ID or "G-DEBUGTEST"

    status = _forward_to_gtm(
        client_id="diag_test_client.1234567890",
        session_id="9999999999",
        event_name="page_view",
        params={
            "page_location": "https://test.example.com/diag",
            "page_title": "Diagnostic Test Page",
            "engagement_time_msec": "100",
        },
        measurement_id=mid,
        use_gtm=True,
    )

    return {
        "ok": status is not None and status < 300,
        "status_code": status,
        "measurement_id_used": mid,
        "gtm_url": GTM_SERVER_URL,
        "note": "Verifique no GTM Preview se o evento page_view apareceu.",
    }


@router.post("/ga4/test")
def ga4_test_event():
    """Envia um evento page_view de teste para GA4 via Measurement Protocol."""
    from app.services.ga4 import send_event, GA4_MEASUREMENT_ID, GA4_API_SECRET

    if not GA4_MEASUREMENT_ID or not GA4_API_SECRET:
        return {
            "ok": False,
            "reason": "GA4_MEASUREMENT_ID ou GA4_API_SECRET não configurados no .env",
        }

    ga4_status, gtm_status = send_event(
        client_id="diag_test_client.1234567890",
        session_id="9999999999",
        event_name="page_view",
        params={
            "page_location": "https://test.example.com/diag",
            "page_title": "Diagnostic Test Page",
        },
    )

    return {
        "ok": ga4_status < 300,
        "ga4_status": ga4_status,
        "gtm_status": gtm_status,
        "measurement_id": GA4_MEASUREMENT_ID,
        "note": "Verifique no GA4 DebugView se o evento page_view apareceu. "
                "Pode levar até 24h para aparecer nos relatórios normais.",
    }


@router.get("/redis")
def redis_check():
    """Testa conectividade com Redis."""
    return _check_redis()


@router.get("/db")
def db_check():
    """Testa conectividade com Postgres."""
    return _check_db()


# ── Helpers ──────────────────────────────────────────────────────

def _check_db() -> dict:
    try:
        from app.db.connection import get_conn
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        conn.close()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


def _check_redis() -> dict:
    try:
        from redis import Redis
        r = Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            socket_timeout=3,
        )
        r.ping()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


def _check_gtm() -> dict:
    try:
        from app.services.ga4 import gtm_health_check
        return gtm_health_check()
    except Exception as e:
        return {"ok": False, "reason": str(e)}
