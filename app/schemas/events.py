from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class EventData(BaseModel):
    page_location: Optional[str] = None
    page_title: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None
    gclid: Optional[str] = None
    # scroll_depth
    percent_scrolled: Optional[int] = None
    # cta_click
    button_text: Optional[str] = None
    link_url: Optional[str] = None
    # vsl_progress
    video_percent: Optional[int] = None
    video_current_time: Optional[float] = None
    # Params dinâmicos extras
    extra: Optional[Dict[str, Any]] = None


class EventRequest(BaseModel):
    event: str = Field(..., description="Nome do evento (page_view, scroll_depth, cta_click, vsl_progress)")
    client_id: str = Field(..., description="Client ID do GA4 (UUID)")
    session_id: str = Field(..., description="Session ID (timestamp)")
    visitor_key: str = Field(..., description="Click ID, Sub ID ou TID do tracker")
    data: EventData = Field(default_factory=EventData)


class EventResponse(BaseModel):
    status: str
    message: str
    ga4_status: Optional[int] = None
    gtm_status: Optional[int] = None
