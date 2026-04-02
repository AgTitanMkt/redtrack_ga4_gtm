"""
Rotas de tracking Google (GA4).
Endpoint /ga4/event — recebe eventos comportamentais e de conversão da LP/VSL.
"""
import logging
from fastapi import APIRouter

from app.schemas.events import EventRequest, EventResponse
from app.services import ga4, visitor_store
from app.services.ga4_destinations import resolve_credentials

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ga4", tags=["GA4 Tracking"])

# Campos salvos no Redis como contexto do visitor
_VISITOR_FIELDS = (
    "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "gclid",
)

# Campos enviados ao GA4
_GA4_FIELDS = (
    "page_location", "page_title",
    "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "gclid",
    "percent_scrolled",
    "button_text", "link_url",
    "video_percent", "video_current_time",
)


@router.post("/event", response_model=EventResponse)
def receive_event(req: EventRequest):
    """Recebe eventos comportamentais: page_view, scroll_depth, cta_click, vsl_progress."""

    # Salva visitor no Redis
    visitor_payload = {
        "client_id": req.client_id,
        "session_id": req.session_id,
        "page_location": req.data.page_location,
        "page_title": req.data.page_title,
    }
    for f in _VISITOR_FIELDS:
        visitor_payload[f] = getattr(req.data, f, None)

    visitor_store.save_visitor(req.visitor_key, visitor_payload)

    # Monta params do GA4
    ga4_params = {}
    for f in _GA4_FIELDS:
        val = getattr(req.data, f, None)
        if val is not None:
            ga4_params[f] = val

    # Extras dinâmicos
    if req.data.extra:
        ga4_params.update(req.data.extra)

    # Resolve credenciais GA4 por page_location (DB match → fallback .env)
    creds = resolve_credentials(req.data.page_location)

    # Envia para GA4 (+ GTM SS se habilitado)
    ga4_status, gtm_status = ga4.send_event(
        client_id=req.client_id,
        session_id=req.session_id,
        event_name=req.event,
        params=ga4_params,
        measurement_id=creds.measurement_id,
        api_secret=creds.api_secret,
        use_gtm_server=creds.use_gtm_server,
        creds_source=creds.source,
    )

    return EventResponse(
        status="ok",
        message=f"Evento '{req.event}' enviado para GA4",
        ga4_status=ga4_status,
        gtm_status=gtm_status,
    )
