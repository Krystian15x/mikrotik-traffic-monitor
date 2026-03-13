from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import app.models
from app.config import settings
from app.db import Base, Engine
from app.routers.api import router as api_router
from app.routers.pages import router as pages_router
from app.services.scheduler import run_store_traffic_data, start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
	Base.metadata.create_all(bind=Engine)
	run_store_traffic_data()
	start_scheduler()
	try:
		yield
	finally:
		stop_scheduler()

app = FastAPI(title=settings.app_name, description=settings.app_description, lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(pages_router)
app.include_router(api_router)