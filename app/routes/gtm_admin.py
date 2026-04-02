"""
Rotas administrativas para GTM API.
Endpoints para gerenciar workspace, tags, triggers, variables, versioning e publish.

Todas as operações requerem:
  - GTM_SERVICE_ACCOUNT_KEY configurado no .env
  - GTM_ACCOUNT_ID e GTM_CONTAINER_ID configurados no .env
  - Permissões da Service Account no container GTM

Uso: POST /admin/gtm/provision para setup automático completo.
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.services import gtm_api

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/gtm", tags=["GTM Admin"])


# ── Request Models ───────────────────────────────────────────────

class WorkspaceRequest(BaseModel):
    name: str
    description: str = ""


class TriggerRequest(BaseModel):
    workspace_id: str
    body: Dict[str, Any]


class VariableRequest(BaseModel):
    workspace_id: str
    body: Dict[str, Any]


class TagRequest(BaseModel):
    workspace_id: str
    body: Dict[str, Any]


class VersionRequest(BaseModel):
    workspace_id: str
    name: str
    notes: str = ""


class PublishRequest(BaseModel):
    version_id: str


class ProvisionRequest(BaseModel):
    measurement_id: str
    workspace_name: str = "GA4-SS-Setup"
    auto_publish: bool = False


# ── Workspace ────────────────────────────────────────────────────

@router.post("/workspace")
def create_workspace(req: WorkspaceRequest):
    try:
        return gtm_api.create_workspace(req.name, req.description)
    except Exception as e:
        logger.error("Erro ao criar workspace: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces")
def list_workspaces():
    try:
        return gtm_api.list_workspaces()
    except Exception as e:
        logger.error("Erro ao listar workspaces: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Triggers ─────────────────────────────────────────────────────

@router.post("/trigger")
def create_trigger(req: TriggerRequest):
    try:
        return gtm_api.create_trigger(req.workspace_id, req.body)
    except Exception as e:
        logger.error("Erro ao criar trigger: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/triggers/{workspace_id}")
def list_triggers(workspace_id: str):
    try:
        return gtm_api.list_triggers(workspace_id)
    except Exception as e:
        logger.error("Erro ao listar triggers: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Variables ────────────────────────────────────────────────────

@router.post("/variable")
def create_variable(req: VariableRequest):
    try:
        return gtm_api.create_variable(req.workspace_id, req.body)
    except Exception as e:
        logger.error("Erro ao criar variable: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/variables/{workspace_id}")
def list_variables(workspace_id: str):
    try:
        return gtm_api.list_variables(workspace_id)
    except Exception as e:
        logger.error("Erro ao listar variables: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Tags ─────────────────────────────────────────────────────────

@router.post("/tag")
def create_tag(req: TagRequest):
    try:
        return gtm_api.create_tag(req.workspace_id, req.body)
    except Exception as e:
        logger.error("Erro ao criar tag: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags/{workspace_id}")
def list_tags(workspace_id: str):
    try:
        return gtm_api.list_tags(workspace_id)
    except Exception as e:
        logger.error("Erro ao listar tags: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Versioning & Publish ────────────────────────────────────────

@router.post("/version")
def create_version(req: VersionRequest):
    try:
        return gtm_api.create_version(req.workspace_id, req.name, req.notes)
    except Exception as e:
        logger.error("Erro ao criar version: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/publish")
def publish_version(req: PublishRequest):
    try:
        return gtm_api.publish_version(req.version_id)
    except Exception as e:
        logger.error("Erro ao publicar version: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Provisioning automático ─────────────────────────────────────

@router.post("/provision")
def provision_ga4_baseline(req: ProvisionRequest):
    """
    Provisiona setup completo de GA4 Server-Side:
    workspace + trigger + tag + version.
    Se auto_publish=true, publica a version automaticamente.
    """
    try:
        result = gtm_api.provision_ga4_baseline(
            measurement_id=req.measurement_id,
            workspace_name=req.workspace_name,
        )

        if req.auto_publish:
            version_data = result.get("version", {})
            cv = version_data.get("containerVersion", {})
            vid = cv.get("containerVersionId")
            if vid:
                publish_result = gtm_api.publish_version(vid)
                result["publish"] = publish_result
                logger.info("Version %s publicada automaticamente", vid)
            else:
                result["publish_error"] = "containerVersionId não encontrado na version"

        return result
    except Exception as e:
        logger.error("Erro ao provisionar GA4 baseline: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
