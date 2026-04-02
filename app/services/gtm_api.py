"""
GTM API Automation — Google Tag Manager API v2

Gerenciamento programático de workspace, tags, triggers, variables, versioning e publish.
Usa Service Account para autenticação (credenciais via env GTM_SERVICE_ACCOUNT_KEY).

Documentação GTM API v2:
  https://developers.google.com/tag-platform/tag-manager/api/v2

IMPORTANTE:
  - As operações de escrita (create/update) operam dentro de um Workspace.
  - Para publicar, crie uma Version a partir do workspace e depois publique.
  - Os tipos de tag/trigger são específicos do tipo de container (Web vs Server).
  - Para Server-Side, tipos comuns: sgtmgaaw (GA4), sgtm_http (HTTP Request).
"""
import logging
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/tagmanager.edit.containers",
    "https://www.googleapis.com/auth/tagmanager.publish",
]

_service = None


def _get_service():
    """Cria e cacheia o cliente da GTM API v2."""
    global _service
    if _service is not None:
        return _service

    key_path = os.getenv("GTM_SERVICE_ACCOUNT_KEY", "")
    if not key_path:
        raise RuntimeError(
            "GTM_SERVICE_ACCOUNT_KEY não configurado. "
            "Defina o caminho do JSON da Service Account no .env"
        )

    credentials = service_account.Credentials.from_service_account_file(
        key_path, scopes=SCOPES
    )
    _service = build("tagmanager", "v2", credentials=credentials)
    logger.info("GTM API v2 service inicializado")
    return _service


def _container_path() -> str:
    """Monta o path do container: accounts/{id}/containers/{id}"""
    account_id = os.getenv("GTM_ACCOUNT_ID", "")
    container_id = os.getenv("GTM_CONTAINER_ID", "")
    if not account_id or not container_id:
        raise RuntimeError("GTM_ACCOUNT_ID e GTM_CONTAINER_ID são obrigatórios")
    return f"accounts/{account_id}/containers/{container_id}"


# ═══════════════════════════════════════════════════════════════════
#  WORKSPACE
# ═══════════════════════════════════════════════════════════════════

def create_workspace(name: str, description: str = "") -> dict:
    """Cria um novo workspace no container."""
    svc = _get_service()
    body = {"name": name, "description": description}
    result = (
        svc.accounts().containers().workspaces()
        .create(parent=_container_path(), body=body)
        .execute()
    )
    logger.info("Workspace criado: %s (id=%s)", result["name"], result["workspaceId"])
    return result


def list_workspaces() -> list:
    """Lista workspaces do container."""
    svc = _get_service()
    result = (
        svc.accounts().containers().workspaces()
        .list(parent=_container_path())
        .execute()
    )
    return result.get("workspace", [])


# ═══════════════════════════════════════════════════════════════════
#  TRIGGERS
# ═══════════════════════════════════════════════════════════════════

def create_trigger(workspace_id: str, trigger_body: dict) -> dict:
    """
    Cria trigger no workspace.
    Exemplo trigger_body para Server-Side (all events):
    {
        "name": "All Events",
        "type": "customEvent",
        "customEventFilter": [{
            "type": "matchRegex",
            "parameter": [
                {"type": "template", "key": "arg0", "value": "{{_event}}"},
                {"type": "template", "key": "arg1", "value": ".*"}
            ]
        }]
    }
    """
    svc = _get_service()
    ws_path = f"{_container_path()}/workspaces/{workspace_id}"
    result = (
        svc.accounts().containers().workspaces().triggers()
        .create(parent=ws_path, body=trigger_body)
        .execute()
    )
    logger.info("Trigger criado: %s (id=%s)", result["name"], result["triggerId"])
    return result


def list_triggers(workspace_id: str) -> list:
    svc = _get_service()
    ws_path = f"{_container_path()}/workspaces/{workspace_id}"
    result = (
        svc.accounts().containers().workspaces().triggers()
        .list(parent=ws_path)
        .execute()
    )
    return result.get("trigger", [])


# ═══════════════════════════════════════════════════════════════════
#  VARIABLES
# ═══════════════════════════════════════════════════════════════════

def create_variable(workspace_id: str, variable_body: dict) -> dict:
    """
    Cria variable no workspace.
    Exemplo variable_body para Event Data:
    {
        "name": "Event Data - transaction_id",
        "type": "v",
        "parameter": [{"type": "template", "key": "name", "value": "transaction_id"}]
    }
    """
    svc = _get_service()
    ws_path = f"{_container_path()}/workspaces/{workspace_id}"
    result = (
        svc.accounts().containers().workspaces().variables()
        .create(parent=ws_path, body=variable_body)
        .execute()
    )
    logger.info("Variable criada: %s (id=%s)", result["name"], result["variableId"])
    return result


def list_variables(workspace_id: str) -> list:
    svc = _get_service()
    ws_path = f"{_container_path()}/workspaces/{workspace_id}"
    result = (
        svc.accounts().containers().workspaces().variables()
        .list(parent=ws_path)
        .execute()
    )
    return result.get("variable", [])


# ═══════════════════════════════════════════════════════════════════
#  TAGS
# ═══════════════════════════════════════════════════════════════════

def create_tag(workspace_id: str, tag_body: dict) -> dict:
    """
    Cria tag no workspace.
    Exemplo tag_body para GA4 Server-Side:
    {
        "name": "GA4 - Forward Events",
        "type": "sgtmgaaw",
        "parameter": [
            {"type": "template", "key": "measurementId", "value": "G-XXXXXXXXXX"},
            {"type": "boolean", "key": "sendToAllProperties", "value": "false"}
        ],
        "firingTriggerId": ["<trigger_id>"]
    }
    """
    svc = _get_service()
    ws_path = f"{_container_path()}/workspaces/{workspace_id}"
    result = (
        svc.accounts().containers().workspaces().tags()
        .create(parent=ws_path, body=tag_body)
        .execute()
    )
    logger.info("Tag criada: %s (id=%s)", result["name"], result["tagId"])
    return result


def list_tags(workspace_id: str) -> list:
    svc = _get_service()
    ws_path = f"{_container_path()}/workspaces/{workspace_id}"
    result = (
        svc.accounts().containers().workspaces().tags()
        .list(parent=ws_path)
        .execute()
    )
    return result.get("tag", [])


# ═══════════════════════════════════════════════════════════════════
#  VERSIONING & PUBLISH
# ═══════════════════════════════════════════════════════════════════

def create_version(workspace_id: str, name: str, notes: str = "") -> dict:
    """Cria uma version a partir do workspace (snapshot)."""
    svc = _get_service()
    ws_path = f"{_container_path()}/workspaces/{workspace_id}"
    body = {"name": name, "notes": notes}
    result = (
        svc.accounts().containers().workspaces()
        .create_version(path=ws_path, body=body)
        .execute()
    )
    version_id = result.get("containerVersion", {}).get("containerVersionId", "?")
    logger.info("Version criada: %s (id=%s)", name, version_id)
    return result


def publish_version(version_id: str) -> dict:
    """Publica uma version específica (torna live)."""
    svc = _get_service()
    version_path = f"{_container_path()}/versions/{version_id}"
    result = (
        svc.accounts().containers().versions()
        .publish(path=version_path)
        .execute()
    )
    logger.info("Version publicada: %s", version_id)
    return result


# ═══════════════════════════════════════════════════════════════════
#  PROVISIONING — Seeds para GA4 Server-Side
# ═══════════════════════════════════════════════════════════════════

def provision_ga4_baseline(measurement_id: str,
                           workspace_name: str = "GA4-SS-Setup") -> dict:
    """
    Provisiona setup completo de GA4 Server-Side no container:
      1. Workspace
      2. Trigger "All Events" (Custom Event .*)
      3. Tag GA4 (forward de todos os eventos para a propriedade)
      4. Version (snapshot pronto para publicar)

    O trigger usa CustomEvent com regex .* para capturar todos os eventos
    recebidos pelo Client do container (page_view, purchase, etc.).

    A tag GA4 (sgtmgaaw) reenvia os eventos para a propriedade GA4
    identificada pelo measurement_id.

    Retorna dict com todos os recursos criados.
    Para publicar: chame publish_version(results["version"]["containerVersion"]["containerVersionId"])
    """
    results = {}

    # 1. Workspace
    ws = create_workspace(workspace_name, "GA4 Server-Side auto-provisioned")
    ws_id = ws["workspaceId"]
    results["workspace"] = ws

    # 2. Trigger — captura todos os eventos
    trigger = create_trigger(ws_id, {
        "name": "All Events - Server Side",
        "type": "customEvent",
        "customEventFilter": [{
            "type": "matchRegex",
            "parameter": [
                {"type": "template", "key": "arg0", "value": "{{_event}}"},
                {"type": "template", "key": "arg1", "value": ".*"},
            ],
        }],
    })
    results["trigger"] = trigger

    # 3. Tag GA4 — forward de eventos para GA4
    tag = create_tag(ws_id, {
        "name": "GA4 - Forward Events",
        "type": "sgtmgaaw",
        "parameter": [
            {"type": "template", "key": "measurementId", "value": measurement_id},
            {"type": "boolean", "key": "sendToAllProperties", "value": "false"},
        ],
        "firingTriggerId": [trigger["triggerId"]],
    })
    results["tag"] = tag

    # 4. Version
    version = create_version(
        ws_id,
        f"v-{workspace_name}",
        "Auto-generated GA4 Server-Side baseline",
    )
    results["version"] = version

    logger.info("GA4 baseline provisionado com sucesso no workspace %s", ws_id)
    return results
