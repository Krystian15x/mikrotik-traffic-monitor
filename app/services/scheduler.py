import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.db import SessionLocal
from app.services.traffic import store_traffic_data

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def run_store_traffic_data():
	db = SessionLocal()
	try:
		store_traffic_data(db)
	except Exception:
		logger.exception("Błąd w schedulerze podczas zapisu statystyk.")
	finally:
		db.close()

def start_scheduler():
	if scheduler.get_job("fetch_traffic") is None:
		scheduler.add_job(
			func=run_store_traffic_data,
			trigger=IntervalTrigger(minutes=1),
			id="fetch_traffic",
			replace_existing=True,
			max_instances=1,
			coalesce=True,
		)
	if not scheduler.running:
		scheduler.start()

def stop_scheduler():
	if scheduler.running:
		scheduler.shutdown(wait=False)