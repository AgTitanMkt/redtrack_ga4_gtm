"""
RQ Worker — Processa fila "postbacks" (envio para RedTrack).
Roda como container separado no docker-compose.
"""
import os
import logging
from redis import Redis
from rq import Worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

redis_conn = Redis(host=REDIS_HOST, port=REDIS_PORT)

logger.info("Worker iniciando | redis=%s:%s | fila=postbacks", REDIS_HOST, REDIS_PORT)

worker = Worker(["postbacks"], connection=redis_conn)
worker.work()
