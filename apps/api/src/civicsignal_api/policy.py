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
    RoleName.REVIEWER: frozenset({Permission.RESOURCE_VIEW, Permission.RESOURCE_REVIEW}),
    RoleName.VERIFIER: frozenset(
        {
            Permission.RESOURCE_VIEW,
            Permission.RESOURCE_VERIFY,
            Permission.RESOURCE_PUBLISH,
            Permission.RESOURCE_ARCHIVE,
        }
    ),
    RoleName.ADMINISTRATOR: frozenset(Permission),
}


def permissions_for(account: AdminAccount) -> set[Permission]:
    return {permission for role in account.roles for permission in ROLE_PERMISSIONS[role.name]}
