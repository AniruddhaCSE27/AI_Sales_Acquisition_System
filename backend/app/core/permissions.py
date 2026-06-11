from __future__ import annotations

from enum import Enum

from fastapi import HTTPException

from app.models import Role, User


class EnterpriseRole(str, Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    AGENT = "AGENT"


ROLE_ALIASES: dict[EnterpriseRole, set[Role]] = {
    EnterpriseRole.ADMIN: {Role.super_admin, Role.admin},
    EnterpriseRole.MANAGER: {Role.manager},
    EnterpriseRole.AGENT: {Role.agent, Role.telecaller, Role.counsellor},
}


def enterprise_role_for(user: User) -> EnterpriseRole:
    for enterprise_role, roles in ROLE_ALIASES.items():
        if user.role in roles:
            return enterprise_role
    return EnterpriseRole.AGENT


def ensure_permission(user: User, *allowed: EnterpriseRole) -> None:
    if enterprise_role_for(user) == EnterpriseRole.ADMIN:
        return
    if enterprise_role_for(user) not in allowed:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
