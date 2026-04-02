"""
GA4 Destinations — Resolução de credenciais GA4 por domínio/página.

Ordem de resolução:
  1. Busca no Postgres por (domain, page_path) exato
  2. Busca por (domain, '') — credencial genérica do domínio
  3. Fallback: GA4_MEASUREMENT_ID + GA4_API_SECRET do .env

Se a tabela ga4_integrations estiver vazia ou o DB falhar,
o sistema SEMPRE cai no fallback do .env. Zero risco de quebra.
"""
import os
import logging
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from app.db.connection import get_conn

logger = logging.getLogger(__name__)

# Fallback global do .env — é o default quando não há match no banco
_ENV_MEASUREMENT_ID = os.getenv("GA4_MEASUREMENT_ID", "")
_ENV_API_SECRET = os.getenv("GA4_API_SECRET", "")
_ENV_USE_GTM = os.getenv("USE_GTM_SERVER", "false").lower() in ("true", "1", "yes")


@dataclass
class GA4Credentials:
    measurement_id: str
    api_secret: str
    use_gtm_server: bool
    source: str  # "db:<name>" ou "env"


def _env_fallback() -> GA4Credentials:
    """Retorna credenciais do .env como fallback."""
    return GA4Credentials(
        measurement_id=_ENV_MEASUREMENT_ID,
        api_secret=_ENV_API_SECRET,
        use_gtm_server=_ENV_USE_GTM,
        source="env",
    )


def resolve_credentials(page_location: Optional[str] = None) -> GA4Credentials:
    """
    Resolve credenciais GA4 para um dado page_location.
    Tenta no DB primeiro; se falhar ou não encontrar, usa .env.
    """
    if not page_location:
        logger.debug("GA4 creds: sem page_location → fallback .env")
        return _env_fallback()

    try:
        parsed = urlparse(page_location)
        domain = parsed.netloc.lower()  # ex: "meusite.com"
        path = parsed.path.rstrip("/") or ""  # ex: "/lp/vsl1"
    except Exception:
        logger.debug("GA4 creds: page_location inválida → fallback .env")
        return _env_fallback()

    if not domain:
        return _env_fallback()

    # Tenta buscar no DB: primeiro match exato (domain + path), depois genérico (domain + '')
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT name, measurement_id, api_secret, use_gtm_server
            FROM ga4_integrations
            WHERE domain = %s AND is_active = true
            ORDER BY
                CASE WHEN page_path = %s THEN 0
                     WHEN page_path = '' THEN 1
                     ELSE 2
                END
            LIMIT 1
        """, (domain, path))
        row = cur.fetchone()
        if row:
            creds = GA4Credentials(
                measurement_id=row[1],
                api_secret=row[2],
                use_gtm_server=row[3],
                source=f"db:{row[0]}",
            )
            logger.info("GA4 creds: usando integração '%s' para %s%s", row[0], domain, path)
            return creds
    except Exception as e:
        # DB falhou — cai no fallback silenciosamente
        logger.warning("GA4 creds: erro DB, usando fallback .env: %s", e)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

    logger.debug("GA4 creds: sem match no DB para %s%s → fallback .env", domain, path)
    return _env_fallback()


# ═══════════════════════════════════════════════════════════════════
#  CRUD — usado pelo admin
# ═══════════════════════════════════════════════════════════════════

def list_integrations() -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, name, domain, page_path, measurement_id, api_secret,
                   use_gtm_server, is_active, created_at, updated_at
            FROM ga4_integrations
            ORDER BY domain, page_path
        """)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def get_integration(integration_id: int) -> Optional[dict]:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, name, domain, page_path, measurement_id, api_secret,
                   use_gtm_server, is_active, created_at, updated_at
            FROM ga4_integrations WHERE id = %s
        """, (integration_id,))
        row = cur.fetchone()
        if not row:
            return None
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))
    finally:
        conn.close()


def create_integration(name: str, domain: str, page_path: str,
                       measurement_id: str, api_secret: str,
                       use_gtm_server: bool = False) -> dict:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO ga4_integrations(name, domain, page_path, measurement_id, api_secret, use_gtm_server)
            VALUES(%s, %s, %s, %s, %s, %s)
            RETURNING id, name, domain, page_path, measurement_id, api_secret,
                      use_gtm_server, is_active, created_at, updated_at
        """, (name, domain.lower(), page_path.strip(), measurement_id, api_secret, use_gtm_server))
        row = cur.fetchone()
        conn.commit()
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_integration(integration_id: int, **fields) -> Optional[dict]:
    allowed = {"name", "domain", "page_path", "measurement_id", "api_secret",
               "use_gtm_server", "is_active"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return get_integration(integration_id)

    if "domain" in updates:
        updates["domain"] = updates["domain"].lower()

    set_clause = ", ".join(f"{k} = %s" for k in updates)
    set_clause += ", updated_at = NOW()"
    values = list(updates.values()) + [integration_id]

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(f"""
            UPDATE ga4_integrations SET {set_clause}
            WHERE id = %s
            RETURNING id, name, domain, page_path, measurement_id, api_secret,
                      use_gtm_server, is_active, created_at, updated_at
        """, values)
        row = cur.fetchone()
        conn.commit()
        if not row:
            return None
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def delete_integration(integration_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM ga4_integrations WHERE id = %s", (integration_id,))
        deleted = cur.rowcount > 0
        conn.commit()
        return deleted
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
