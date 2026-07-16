import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from civicsignal_api.auth_dependencies import AuthContext, csrf_protected, require
from civicsignal_api.db.dependencies import get_session
from civicsignal_api.models.auth import AuditEvent
from civicsignal_api.models.governance import GovernedResource, ResourceRevision, WorkflowState
from civicsignal_api.policy import Permission, permissions_for
from civicsignal_api.schemas.governance import (
    DraftContent,
    DraftCreate,
    DraftUpdate,
    GovernedResourceView,
    TransitionRequest,
)
from civicsignal_api.services.governance import current_revision, transition

router = APIRouter(prefix="/api/v1/admin/resources", tags=["resource governance"])
Database = Annotated[AsyncSession, Depends(get_session)]
CsrfAuth = Annotated[AuthContext, Depends(csrf_protected)]
Viewer = Annotated[AuthContext, Depends(require(Permission.RESOURCE_VIEW))]
Creator = Annotated[AuthContext, Depends(require(Permission.RESOURCE_DRAFT_CREATE))]
Editor = Annotated[AuthContext, Depends(require(Permission.RESOURCE_DRAFT_EDIT))]
Submitter = Annotated[AuthContext, Depends(require(Permission.RESOURCE_SUBMIT))]
Reviewer = Annotated[AuthContext, Depends(require(Permission.RESOURCE_REVIEW))]
Verifier = Annotated[AuthContext, Depends(require(Permission.RESOURCE_VERIFY))]
Publisher = Annotated[AuthContext, Depends(require(Permission.RESOURCE_PUBLISH))]
Archiver = Annotated[AuthContext, Depends(require(Permission.RESOURCE_ARCHIVE))]


async def load(db: AsyncSession, resource_id: uuid.UUID) -> GovernedResource:
    resource = await db.get(GovernedResource, resource_id)
    if resource is None:
        raise HTTPException(404, "Governed resource not found")
    return resource


async def view(db: AsyncSession, resource: GovernedResource) -> GovernedResourceView:
    await db.refresh(resource)
    revision = await current_revision(db, resource)
    return GovernedResourceView(
        id=resource.id,
        state=resource.state.value,
        revision=revision.number,
        content=DraftContent.model_validate(revision.content),
        owner_id=resource.owner_id,
        assigned_reviewer_id=resource.assigned_reviewer_id,
        public_service_id=resource.public_service_id,
        created_at=resource.created_at,
        updated_at=resource.updated_at,
    )


@router.get("", response_model=list[GovernedResourceView])
async def list_resources(
    db: Database, auth: Viewer, state: WorkflowState | None = None
) -> list[GovernedResourceView]:
    query = select(GovernedResource).order_by(GovernedResource.updated_at.desc()).limit(100)
    if state:
        query = query.where(GovernedResource.state == state)
    return [await view(db, item) for item in await db.scalars(query)]


@router.get("/{resource_id}", response_model=GovernedResourceView)
async def get_resource(resource_id: uuid.UUID, db: Database, auth: Viewer) -> GovernedResourceView:
    return await view(db, await load(db, resource_id))


@router.post("", response_model=GovernedResourceView, status_code=201)
async def create_draft(
    payload: DraftCreate, db: Database, csrf: CsrfAuth, auth: Creator
) -> GovernedResourceView:
    resource = GovernedResource(state=WorkflowState.DRAFT, owner_id=auth.account.id)
    db.add(resource)
    await db.flush()
    revision = ResourceRevision(
        resource_id=resource.id,
        number=1,
        content=payload.content.model_dump(mode="json"),
        created_by_id=auth.account.id,
    )
    db.add(revision)
    await db.flush()
    resource.current_revision_id = revision.id
    db.add(
        AuditEvent(
            actor_id=auth.account.id,
            action="resource.draft.create",
            subject_type="governed_resource",
            subject_id=str(resource.id),
            summary="Resource draft created at revision 1",
        )
    )
    await db.commit()
    await db.refresh(resource)
    return await view(db, resource)


@router.put("/{resource_id}", response_model=GovernedResourceView)
async def update_draft(
    resource_id: uuid.UUID, payload: DraftUpdate, db: Database, csrf: CsrfAuth, auth: Editor
) -> GovernedResourceView:
    resource = await load(db, resource_id)
    revision = await current_revision(db, resource)
    if resource.state not in {WorkflowState.DRAFT, WorkflowState.CHANGES_REQUESTED}:
        raise HTTPException(409, "Resource is not editable")
    if revision.number != payload.expected_revision:
        raise HTTPException(409, "Resource changed; reload before saving")
    if resource.owner_id != auth.account.id and Permission.ADMIN_MANAGE not in permissions_for(
        auth.account
    ):
        raise HTTPException(403, "Only the draft owner may edit")
    number = (
        int(
            await db.scalar(
                select(func.max(ResourceRevision.number)).where(
                    ResourceRevision.resource_id == resource.id
                )
            )
            or 0
        )
        + 1
    )
    updated = ResourceRevision(
        resource_id=resource.id,
        number=number,
        content=payload.content.model_dump(mode="json"),
        created_by_id=auth.account.id,
    )
    db.add(updated)
    await db.flush()
    resource.current_revision_id = updated.id
    db.add(
        AuditEvent(
            actor_id=auth.account.id,
            action="resource.draft.edit",
            subject_type="governed_resource",
            subject_id=str(resource.id),
            summary=f"Draft revision {number} created",
        )
    )
    await db.commit()
    return await view(db, resource)


@router.post("/{resource_id}/claim", response_model=GovernedResourceView)
async def claim(
    resource_id: uuid.UUID, db: Database, csrf: CsrfAuth, auth: Reviewer
) -> GovernedResourceView:
    resource = await load(db, resource_id)
    if resource.state != WorkflowState.SUBMITTED:
        raise HTTPException(409, "Only submitted resources may be claimed")
    if resource.assigned_reviewer_id and resource.assigned_reviewer_id != auth.account.id:
        raise HTTPException(409, "Resource is already assigned")
    resource.assigned_reviewer_id = auth.account.id
    db.add(
        AuditEvent(
            actor_id=auth.account.id,
            action="resource.review.claim",
            subject_type="governed_resource",
            subject_id=str(resource.id),
            summary="Review claimed",
        )
    )
    await db.commit()
    return await view(db, resource)


async def do_transition(
    resource_id: uuid.UUID,
    payload: TransitionRequest,
    action: str,
    db: AsyncSession,
    auth: AuthContext,
) -> GovernedResourceView:
    resource = await load(db, resource_id)
    await transition(
        db,
        resource,
        auth.account,
        action,
        payload.expected_revision,
        payload.reason,
        payload.evidence,
        payload.next_due_at,
    )
    return await view(db, resource)


@router.post("/{resource_id}/submit", response_model=GovernedResourceView)
async def submit(
    resource_id: uuid.UUID,
    payload: TransitionRequest,
    db: Database,
    csrf: CsrfAuth,
    auth: Submitter,
) -> GovernedResourceView:
    return await do_transition(resource_id, payload, "submit", db, auth)


@router.post("/{resource_id}/request-changes", response_model=GovernedResourceView)
async def request_changes(
    resource_id: uuid.UUID, payload: TransitionRequest, db: Database, csrf: CsrfAuth, auth: Reviewer
) -> GovernedResourceView:
    return await do_transition(resource_id, payload, "request_changes", db, auth)


@router.post("/{resource_id}/reject", response_model=GovernedResourceView)
async def reject(
    resource_id: uuid.UUID, payload: TransitionRequest, db: Database, csrf: CsrfAuth, auth: Reviewer
) -> GovernedResourceView:
    return await do_transition(resource_id, payload, "reject", db, auth)


@router.post("/{resource_id}/advance", response_model=GovernedResourceView)
async def advance(
    resource_id: uuid.UUID, payload: TransitionRequest, db: Database, csrf: CsrfAuth, auth: Reviewer
) -> GovernedResourceView:
    return await do_transition(resource_id, payload, "advance", db, auth)


@router.post("/{resource_id}/verify", response_model=GovernedResourceView)
async def verify(
    resource_id: uuid.UUID, payload: TransitionRequest, db: Database, csrf: CsrfAuth, auth: Verifier
) -> GovernedResourceView:
    return await do_transition(resource_id, payload, "verify", db, auth)


@router.post("/{resource_id}/publish", response_model=GovernedResourceView)
async def publish(
    resource_id: uuid.UUID,
    payload: TransitionRequest,
    db: Database,
    csrf: CsrfAuth,
    auth: Publisher,
) -> GovernedResourceView:
    return await do_transition(resource_id, payload, "publish", db, auth)


@router.post("/{resource_id}/reverify", response_model=GovernedResourceView)
async def reverify(
    resource_id: uuid.UUID, payload: TransitionRequest, db: Database, csrf: CsrfAuth, auth: Reviewer
) -> GovernedResourceView:
    return await do_transition(resource_id, payload, "request_reverification", db, auth)


@router.post("/{resource_id}/archive", response_model=GovernedResourceView)
async def archive(
    resource_id: uuid.UUID, payload: TransitionRequest, db: Database, csrf: CsrfAuth, auth: Archiver
) -> GovernedResourceView:
    return await do_transition(resource_id, payload, "archive", db, auth)
