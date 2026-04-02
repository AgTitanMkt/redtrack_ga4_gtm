"""
Visitor Store — Redis
Armazena vínculo visitor_key → client_id/session_id/utms/gclid
TTL: 30 dias

Reutiliza o Redis já existente no docker-compose (host="redis", db=1).
db=0 é usado pelo RQ (fila de postbacks), db=1 é para visitors.
"""
import json
import os
import logging
from typing import Optional

from redis import Redis, ConnectionError as RedisConnectionError

logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
TTL_SECONDS = 30 * 24 * 60 * 60  # 30 dias

_client: Optional[Redis] = None


def _get_redis() -> Redis:
    global _client
    if _client is None:
        _client = Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=1,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )
    return _client


def save_visitor(visitor_key: str, payload: dict) -> bool:
    """Salva dados do visitor no Redis com TTL de 30 dias."""
    try:
        r = _get_redis()
        key = f"ga4:visitor:{visitor_key}"
        r.set(key, json.dumps(payload), ex=TTL_SECONDS)
        logger.info("Visitor salvo: %s", visitor_key)
        return True
    except (RedisConnectionError, Exception) as e:
        logger.error("Erro ao salvar visitor '%s': %s", visitor_key, e)
        return False


def get_visitor(visitor_key: str) -> Optional[dict]:
    """Busca visitor no Redis pelo visitor_key."""
    if not visitor_key:
        return None
    try:
        r = _get_redis()
        key = f"ga4:visitor:{visitor_key}"
        data = r.get(key)
        if data is None:
            return None
        return json.loads(data)
    except (RedisConnectionError, Exception) as e:
        logger.error("Erro ao buscar visitor '%s': %s", visitor_key, e)
        return None
