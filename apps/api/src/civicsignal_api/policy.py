from enum import StrEnum

from civicsignal_api.models.auth import AdminAccount, RoleName


class Permission(StrEnum):
    RESOURCE_VIEW = "resource.view"
    RESOURCE_DRAFT_CREATE = "resource.draft.create"
    RESOURCE_DRAFT_EDIT = "resource.draft.edit"
    RESOURCE_SUBMIT = "resource.submit"
    RESOURCE_REVIEW = "resource.review"
    RESOURCE_VERIFY = "resource.verify"
    RESOURCE_PUBLISH = "resource.publish"
    RESOURCE_ARCHIVE = "resource.archive"
    IMPORT_CREATE = "import.create"
    EXPORT_CREATE = "export.create"
    AUDIT_VIEW = "audit.view"
    ADMIN_MANAGE = "admin.manage"
    ACCOUNT_VIEW = "account.view"
    ACCOUNT_CREATE = "account.create"
    ACCOUNT_UPDATE = "account.update"
    ACCOUNT_DISABLE = "account.disable"
    ACCOUNT_ASSIGN_ROLES = "account.assign_roles"
    SESSION_VIEW_ALL = "session.view_all"
    SESSION_REVOKE_ALL = "session.revoke_all"
    CORRECTION_VIEW = "correction.view"
    CORRECTION_VIEW_CONTACT = "correction.view_contact"
    CORRECTION_CLAIM = "correction.claim"
    CORRECTION_ASSIGN = "correction.assign"
    CORRECTION_TRIAGE = "correction.triage"
    CORRECTION_MARK_DUPLICATE = "correction.mark_duplicate"
    CORRECTION_MARK_ABUSE = "correction.mark_abuse"
    CORRECTION_DISMISS = "correction.dismiss"
    CORRECTION_RESOLVE = "correction.resolve"
    CORRECTION_REOPEN = "correction.reopen"
    CORRECTION_REQUEST_REVERIFICATION = "correction.request_reverification"
    REVERIFICATION_VIEW = "reverification.view"
    REVERIFICATION_OPERATE = "reverification.operate"
    REVERIFICATION_ASSIGN = "reverification.assign"


ROLE_PERMISSIONS: dict[RoleName, frozenset[Permission]] = {
    RoleName.VIEWER: frozenset({Permission.RESOURCE_VIEW, Permission.AUDIT_VIEW}),
    RoleName.CONTRIBUTOR: frozenset(
        {
            Permission.RESOURCE_VIEW,
            Permission.RESOURCE_DRAFT_CREATE,
            Permission.RESOURCE_DRAFT_EDIT,
            Permission.RESOURCE_SUBMIT,
            Permission.IMPORT_CREATE,
        }
    ),
    RoleName.REVIEWER: frozenset(
        {
            Permission.RESOURCE_VIEW,
            Permission.RESOURCE_REVIEW,
            Permission.CORRECTION_VIEW,
            Permission.CORRECTION_CLAIM,
            Permission.CORRECTION_TRIAGE,
            Permission.CORRECTION_MARK_DUPLICATE,
            Permission.CORRECTION_DISMISS,
            Permission.CORRECTION_REQUEST_REVERIFICATION,
            Permission.REVERIFICATION_VIEW,
        }
    ),
    RoleName.VERIFIER: frozenset(
        {
            Permission.RESOURCE_VIEW,
            Permission.RESOURCE_VERIFY,
            Permission.RESOURCE_PUBLISH,
            Permission.RESOURCE_ARCHIVE,
            Permission.CORRECTION_VIEW,
            Permission.CORRECTION_RESOLVE,
            Permission.REVERIFICATION_VIEW,
            Permission.REVERIFICATION_OPERATE,
        }
    ),
    RoleName.ADMINISTRATOR: frozenset(Permission),
}


def permissions_for(account: AdminAccount) -> set[Permission]:
    return {permission for role in account.roles for permission in ROLE_PERMISSIONS[role.name]}
