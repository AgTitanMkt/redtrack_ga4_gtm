"""
DDL para tabelas de tracking/conversões.
Execute init_db() no startup da aplicação para garantir que as tabelas existem.
Seguro para rodar múltiplas vezes (CREATE IF NOT EXISTS).
"""
import logging
from app.db.connection import get_conn

logger = logging.getLogger(__name__)

# Tabela principal de conversões — dedup por (source, event_id)
_CONVERSIONS_DDL = """
CREATE TABLE IF NOT EXISTS conversions (
    id          SERIAL PRIMARY KEY,
    source      VARCHAR(50)    NOT NULL,
    event_id    VARCHAR(255)   NOT NULL,
    order_id    VARCHAR(255)   NOT NULL,
    click_id    VARCHAR(255),
    payout      NUMERIC(12,2)  DEFAULT 0,
    payload     JSONB,
    created_at  TIMESTAMP      DEFAULT NOW(),
    UNIQUE(source, event_id)
);
"""

# Log de envio por destino — dedup por (dedupe_key, destination)
# Permite verificar se um evento já foi enviado para GA4, GTM, RedTrack etc.
_CONVERSION_LOGS_DDL = """
CREATE TABLE IF NOT EXISTS conversion_logs (
    id          SERIAL PRIMARY KEY,
    dedupe_key  VARCHAR(255)   NOT NULL,
    destination VARCHAR(50)    NOT NULL,
    status_code INT,
    event_name  VARCHAR(100),
    payload     JSONB,
    created_at  TIMESTAMP      DEFAULT NOW(),
    UNIQUE(dedupe_key, destination)
);
"""

# Integrações GA4 por domínio/página — permite credenciais diferentes por funil
# Se não houver match, o sistema usa GA4_MEASUREMENT_ID/GA4_API_SECRET do .env
_GA4_INTEGRATIONS_DDL = """
CREATE TABLE IF NOT EXISTS ga4_integrations (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255)   NOT NULL,
    domain          VARCHAR(255)   NOT NULL,
    page_path       VARCHAR(500)   DEFAULT '',
    measurement_id  VARCHAR(50)    NOT NULL,
    api_secret      VARCHAR(100)   NOT NULL,
    use_gtm_server  BOOLEAN        DEFAULT false,
    is_active       BOOLEAN        DEFAULT true,
    created_at      TIMESTAMP      DEFAULT NOW(),
    updated_at      TIMESTAMP      DEFAULT NOW(),
    UNIQUE(domain, page_path)
);
"""

# Índices para queries comuns
_INDEXES_DDL = """
CREATE INDEX IF NOT EXISTS idx_conversions_source_order
    ON conversions(source, order_id);
CREATE INDEX IF NOT EXISTS idx_conversion_logs_dedupe
    ON conversion_logs(dedupe_key);
CREATE INDEX IF NOT EXISTS idx_ga4_integrations_domain
    ON ga4_integrations(domain, is_active);
"""


def init_db():
    """Cria tabelas e índices se não existirem. Idempotente."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(_CONVERSIONS_DDL)
        cur.execute(_CONVERSION_LOGS_DDL)
        cur.execute(_GA4_INTEGRATIONS_DDL)
        cur.execute(_INDEXES_DDL)
        conn.commit()
        logger.info("DB init: tabelas e índices verificados/criados")
    except Exception as e:
        conn.rollback()
        logger.error("DB init erro: %s", e)
        raise
    finally:
        conn.close()