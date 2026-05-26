from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import require_roles
from app.db.session import get_db
from app.models import Role, User
from app.schemas import UserRead

router = APIRouter()


@router.get("/", response_model=list[UserRead], dependencies=[Depends(require_roles(Role.manager))])
def list_users(role: Role | None = None, db: Session = Depends(get_db)):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.order_by(User.created_at.desc()).all()

