"""
Configuração central — todas as variáveis de ambiente.
Valores carregados do .env via python-dotenv.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Database (Postgres) ─────────────────────────────────────────
DB_NAME = os.getenv("DB_NAME", "tracking")
DB_USER = os.getenv("DB_USER", "tracker")
DB_PASS = os.getenv("DB_PASS", "adminforte")
DB_HOST = os.getenv("DB_HOST", "db")

# ── Redis ────────────────────────────────────────────────────────
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# ── RedTrack ─────────────────────────────────────────────────────
REDTRACK_POSTBACK = os.getenv("REDTRACK_POSTBACK", "")

# ── GA4 (fallback global — usado quando nenhuma integração bate) ─
GA4_MEASUREMENT_ID = os.getenv("GA4_MEASUREMENT_ID", "")
GA4_API_SECRET = os.getenv("GA4_API_SECRET", "")
GA4_DEBUG = os.getenv("GA4_DEBUG", "false").lower() in ("true", "1", "yes")

# ── GTM Server-Side ─────────────────────────────────────────────
USE_GTM_SERVER = os.getenv("USE_GTM_SERVER", "false").lower() in ("true", "1", "yes")
GTM_SERVER_URL = os.getenv("GTM_SERVER_URL", "").rstrip("/")

# ── GTM API Automation (Service Account) ─────────────────────────
GTM_SERVICE_ACCOUNT_KEY = os.getenv("GTM_SERVICE_ACCOUNT_KEY", "")
GTM_ACCOUNT_ID = os.getenv("GTM_ACCOUNT_ID", "")
GTM_CONTAINER_ID = os.getenv("GTM_CONTAINER_ID", "")
