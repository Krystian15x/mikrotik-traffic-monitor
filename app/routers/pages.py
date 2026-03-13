from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from app.auth import create_access_token, get_current_user_or_none, verify_login_token, generate_login_token
from app.config import settings
from app.services.traffic import PERIOD_LABELS, PERIODS
from app.templates import templates

router = APIRouter()

@router.get("/favicon.ico")
async def favicon():
	return FileResponse("static/favicon.ico")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
	user = await get_current_user_or_none(request)
	if user:
		return RedirectResponse(url="/", status_code=303)
	generate_login_token(request)
	return templates.TemplateResponse("pages/login.html", {"request": request})

@router.post("/login")
async def login(request: Request):
	form = await request.form()
	if not verify_login_token(request, form.get("password")):
		return templates.TemplateResponse("pages/login.html", {"request": request, "error": "Nieprawidłowe hasło"}, status_code=401)
	response = RedirectResponse(url="/", status_code=303)
	response.set_cookie(
		key="auth_token",
		value=create_access_token(data={"sub": "user"}),
		max_age=(settings.access_token_expire_days * 86400),
		httponly=True,
		path="/",
		secure=request.url.scheme == "https"
	)
	return response

@router.get("/logout")
async def logout():
	response = RedirectResponse(url="/login", status_code=303)
	response.delete_cookie("auth_token", path="/")
	return response

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
	user = await get_current_user_or_none(request)
	if not user:
		return RedirectResponse(url="/login", status_code=303)
	return templates.TemplateResponse("pages/index.html", { "request": request, "periods": PERIODS, "mapping": PERIOD_LABELS, })