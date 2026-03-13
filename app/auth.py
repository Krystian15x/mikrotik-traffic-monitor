import logging
import secrets
from datetime import datetime, timedelta
from fastapi import HTTPException, Request
from jose import JWTError, jwt
from app.config import settings

logger = logging.getLogger(__name__)

def generate_login_token(request: Request):
	request.app.state.login_token = secrets.token_urlsafe(32)
	logger.info(f"Podaj następujące hasło logowania: {request.app.state.login_token}")

def verify_login_token(request: Request, token: str | None) -> bool:
	expected_token = getattr(request.app.state, "login_token", None)
	if not expected_token:
		return False
	return secrets.compare_digest(expected_token, token)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
	to_encode = data.copy()
	expire = datetime.utcnow() + (expires_delta or timedelta(days=settings.access_token_expire_days))
	to_encode.update({"exp": expire})
	return jwt.encode(to_encode, settings.secret_key, algorithm=settings.access_token_algorithm)

async def get_current_user(request: Request) -> str:
	token = request.cookies.get("auth_token")
	if not token:
		raise HTTPException(status_code=401, detail="Niezalogowany, odmowa dostępu")
	try:
		payload = jwt.decode(token, settings.secret_key, algorithms=[settings.access_token_algorithm])
		user: str | None = payload.get("sub")
		if not user:
			raise HTTPException(status_code=401, detail="Zmanipulowany token")
		return user
	except JWTError as exc:
		raise HTTPException(status_code=401, detail="Nieprawidłowy token") from exc

async def get_current_user_or_none(request: Request) -> str | None:
	try:
		return await get_current_user(request)
	except HTTPException:
		return None