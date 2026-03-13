from datetime import datetime
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.db import get_db
from app.schemas import ChartData, TimeRange, TrafficSummary
from app.services.traffic import build_statement_context, get_chart_data, get_daily_usage, get_last_records, get_monthly_usage, get_start_time, get_traffic_summary
from app.templates import templates

router = APIRouter(prefix="/api", tags=["api"])

@router.get("/summary/{period}", response_model=TrafficSummary)
async def api_summary(period: str, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
	start = get_start_time(period, datetime.utcnow())
	return get_traffic_summary(db, start)

@router.get("/chart/{period}", response_model=ChartData)
async def api_chart(period: str, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
	start = get_start_time(period, datetime.utcnow())
	records = get_last_records(db, start, max_points=50)
	return get_chart_data(records)

@router.get("/daily")
async def api_daily(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
	return get_daily_usage(db, days=30)

@router.get("/monthly")
async def api_monthly(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
	return get_monthly_usage(db, months=12)

@router.post("/statement", response_class=HTMLResponse)
async def generate_statement(time_range: TimeRange, request: Request, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
	context = build_statement_context(db, time_range)
	context["request"] = request
	return templates.TemplateResponse("pages/statement.html", context)