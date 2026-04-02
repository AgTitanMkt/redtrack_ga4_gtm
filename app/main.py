import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes.cartpanda import router as cartpanda_router
from app.routes import clickbank
from app.routes.events import router as ga4_router
from app.routes.gtm_admin import router as gtm_admin_router
from app.routes.ga4_admin import router as ga4_admin_router
from app.routes.diagnostics import router as diagnostics_router
from app.routes.dashboard import router as dashboard_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="RedTrack · GA4 · GTM — Tracking API",
    description="Multi-domain tracking system with GA4 Measurement Protocol, GTM Server-Side, and RedTrack postbacks.",
    version="2.0.0",
)

# CORS — necessário para o tracker.js enviar eventos de qualquer LP
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Cria tabelas no Postgres se não existirem."""
    try:
        from app.db.models import init_db
        init_db()
        logger.info("DB init concluído")
    except Exception as e:
        logger.warning("DB init falhou (tabelas podem já existir ou DB não pronto): %s", e)


@app.get("/")
def health():
    return {"status": "running", "version": "2.0.0"}


# ── Rotas de webhook (CartPanda + ClickBank) ────────────────────
app.include_router(cartpanda_router, prefix="/webhook")
app.include_router(clickbank.router, prefix="/webhook")

# ── GA4 tracking → /ga4/event ───────────────────────────────────
app.include_router(ga4_router)

# ── Admin GTM API → /admin/gtm/* ────────────────────────────────
app.include_router(gtm_admin_router)

# ── Admin GA4 Integrations → /admin/ga4/* ────────────────────────
app.include_router(ga4_admin_router)

# ── Diagnósticos → /diag/* ──────────────────────────────────────
app.include_router(diagnostics_router)

# ── Dashboard Master → /dashboard/ ─────────────────────────────
app.include_router(dashboard_router)

# ── Static files (tracker.js) ───────────────────────────────────
static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
