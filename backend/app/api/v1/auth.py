from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.api.deps import current_user
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, hash_password, hash_token, verify_password
from app.db.session import get_db
from app.models import AuditLog, RefreshToken, User
from app.schemas import LoginRequest, Token, UserCreate, UserRead

router = APIRouter()


@router.post("/register", response_model=UserRead)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(name=payload.name, email=payload.email, hashed_password=hash_password(payload.password), role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")
    refresh = create_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=hash_token(refresh), expires_at=datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)))
    db.add(AuditLog(organization_id=user.organization_id, user_id=user.id, action="auth.login", entity_type="user", entity_id=user.id))
    db.commit()
    return Token(access_token=create_access_token(user.email, user.role.value), refresh_token=refresh, role=user.role)


@router.post("/refresh", response_model=Token)
async def refresh(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    token = payload.get("refresh_token")
    if not token and request.headers.get("authorization"):
        # Backward-compatible path for older clients/tests: validate the current user
        # through the access token and issue a new access token only.
        from app.api.deps import current_user as _unused  # keeps the public contract explicit
        auth = request.headers["authorization"].replace("Bearer ", "")
        from app.core.security import decode_token
        subject = decode_token(auth).get("sub")
        user = db.query(User).filter(User.email == subject, User.is_active.is_(True)).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return Token(access_token=create_access_token(user.email, user.role.value), role=user.role)
    if not token:
        raise HTTPException(status_code=400, detail="refresh_token is required")
    row = db.query(RefreshToken).filter(RefreshToken.token_hash == hash_token(token), RefreshToken.revoked_at.is_(None)).first()
    if not row or row.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = db.get(User, row.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    row.revoked_at = datetime.utcnow()
    refresh_token = create_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=hash_token(refresh_token), expires_at=datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)))
    db.add(AuditLog(organization_id=user.organization_id, user_id=user.id, action="auth.refresh", entity_type="user", entity_id=user.id))
    db.commit()
    return Token(access_token=create_access_token(user.email, user.role.value), refresh_token=refresh_token, role=user.role)


@router.post("/logout")
def logout(payload: dict, db: Session = Depends(get_db), user: User = Depends(current_user)):
    token = payload.get("refresh_token")
    if token:
        row = db.query(RefreshToken).filter(RefreshToken.token_hash == hash_token(token), RefreshToken.revoked_at.is_(None)).first()
        if row:
            row.revoked_at = datetime.utcnow()
    db.add(AuditLog(organization_id=user.organization_id, user_id=user.id, action="auth.logout", entity_type="user", entity_id=user.id))
    db.commit()
    return {"ok": True}
