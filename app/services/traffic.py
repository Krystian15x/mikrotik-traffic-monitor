import re
from datetime import datetime, timedelta
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from app.config import settings
from app.models import TrafficRecord
from app.schemas import ChartData, TimeRange, TrafficSummary
from app.services.routeros import fetch_traffic_stats

PERIODS = ["4min", "10min", "15min", "1h", "12h", "24h", "7d", "1m", "3m", "6m", "12m", "36m", "all"]

PERIOD_LABELS = {
	"h": "godz.",
	"min": "min",
	"d": "dni",
	"m": "mies.",
	"all": "Całość",
}

def store_traffic_data(db: Session):
	rx, tx, rx_p, tx_p = fetch_traffic_stats(settings.lte_nr_interface)
	record = TrafficRecord(
		rx_bytes=rx,
		tx_bytes=tx,
		rx_packets=rx_p,
		tx_packets=tx_p,
	)
	db.add(record)
	db.commit()
	return record

def get_start_time(period: str, now: datetime) -> datetime:
	if period == "all":
		return datetime.min
	match = re.match(r"(\d+)(min|h|d|m)$", period)
	if not match:
		return datetime.min
	value, unit = int(match.group(1)), match.group(2)
	if unit == "m":
		month = now.month - (value - 1)
		year = now.year
		while month <= 0:
			month += 12
			year -= 1
		return datetime(year, month, 1, 0, 0, 0)
	delta_map = {
		"min": "minutes",
		"h": "hours",
		"d": "days",
	}
	return now - timedelta(**{delta_map[unit]: value})

def get_traffic_summary(db: Session, start: datetime, end: datetime | None = None) -> TrafficSummary:
	row = db.execute(
		text("""
			WITH ordered AS (
				SELECT
					rx_bytes,
					tx_bytes,
					rx_packets,
					tx_packets,
					timestamp,
					LAG(rx_bytes) OVER (ORDER BY timestamp) AS p_rx,
					LAG(tx_bytes) OVER (ORDER BY timestamp) AS p_tx,
					LAG(rx_packets) OVER (ORDER BY timestamp) AS p_rp,
					LAG(tx_packets) OVER (ORDER BY timestamp) AS p_tp
				FROM traffic_records
				WHERE timestamp >= :start
				  AND (:end IS NULL OR timestamp < :end)
			),
			deltas AS (
				SELECT
					COALESCE(rx_bytes - p_rx, 0) AS rd,
					COALESCE(tx_bytes - p_tx, 0) AS td,
					COALESCE(rx_packets - p_rp, 0) AS rpd,
					COALESCE(tx_packets - p_tp, 0) AS tpd,
					timestamp
				FROM ordered
				WHERE p_rx IS NOT NULL
			)
			SELECT
				COALESCE(SUM(GREATEST(rd, 0)), 0) AS rx,
				COALESCE(SUM(GREATEST(td, 0)), 0) AS tx,
				COALESCE(SUM(GREATEST(rpd, 0)), 0) AS rp,
				COALESCE(SUM(GREATEST(tpd, 0)), 0) AS tp,
				MIN(timestamp) AS mi,
				MAX(timestamp) AS ma
			FROM deltas
		"""),
		{"start": start, "end": end},
	).one()
	if not row.mi:
		return TrafficSummary(
			rx_bytes=0,
			tx_bytes=0,
			rx_packets=0,
			tx_packets=0,
			avg_rx_mbps=0,
			avg_tx_mbps=0,
		)

	rx = float(row.rx)
	tx = float(row.tx)
	duration_seconds = max((row.ma - row.mi).total_seconds(), 1)
	return TrafficSummary(
		rx_bytes=int(rx),
		tx_bytes=int(tx),
		rx_packets=int(float(row.rp)),
		tx_packets=int(float(row.tp)),
		avg_rx_mbps=round(rx * 8 / duration_seconds / 1_000_000, 2),
		avg_tx_mbps=round(tx * 8 / duration_seconds / 1_000_000, 2),
	)

def get_last_records(db: Session, start: datetime, max_points: int = 50):
	min_ts, max_ts = (
		db.query(
			func.min(TrafficRecord.timestamp),
			func.max(TrafficRecord.timestamp),
		)
		.filter(TrafficRecord.timestamp >= start)
		.one()
	)
	if not min_ts or not max_ts:
		return []
	interval = max(int((max_ts - min_ts).total_seconds() // max_points), 1)
	return (
		db.query(
			TrafficRecord.timestamp,
			TrafficRecord.rx_bytes,
			TrafficRecord.tx_bytes,
		)
		.filter(TrafficRecord.timestamp >= start)
		.group_by(func.floor(func.unix_timestamp(TrafficRecord.timestamp) / interval))
		.order_by(TrafficRecord.timestamp.asc())
		.all()
	)

def get_chart_data(records) -> ChartData:
	if not records:
		return ChartData(labels=[], rx_data=[], tx_data=[])
	return ChartData(
		labels=[r.timestamp.strftime("%Y-%m-%d %H:%M") for r in records],
		rx_data=[
			0 if i == 0 or r.rx_bytes < records[i - 1].rx_bytes
			else r.rx_bytes - records[i - 1].rx_bytes
			for i, r in enumerate(records)
		],
		tx_data=[
			0 if i == 0 or r.tx_bytes < records[i - 1].tx_bytes
			else r.tx_bytes - records[i - 1].tx_bytes
			for i, r in enumerate(records)
		],
	)

def get_daily_usage(db: Session, days: int = 30):
	now = datetime.utcnow()
	daily = []

	for day in range(days):
		days_ago = now - timedelta(days=day + 1)
		start = days_ago.replace(hour=0, minute=0, second=0, microsecond=0)
		end = start + timedelta(days=1)
		summary = get_traffic_summary(db, start, end)
		daily.append({
			"date": start.strftime("%Y-%m-%d"),
			"rx_bytes": summary.rx_bytes,
			"tx_bytes": summary.tx_bytes,
			"total_bytes": summary.rx_bytes + summary.tx_bytes,
		})
	daily.reverse()
	return daily

def get_monthly_usage(db: Session, months: int = 12):
	now = datetime.utcnow()
	monthly = []
	for m in range(months):
		month_val = now.month - m
		year = now.year

		while month_val <= 0:
			month_val += 12
			year -= 1

		start = datetime(year, month_val, 1, 0, 0, 0)
		end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
		summary = get_traffic_summary(db, start, end)

		monthly.append({
			"month": start.strftime("%Y-%m"),
			"rx_bytes": summary.rx_bytes,
			"tx_bytes": summary.tx_bytes,
			"total_bytes": summary.rx_bytes + summary.tx_bytes,
		})

	monthly.reverse()
	return monthly

def build_statement_context(db: Session, time_range: TimeRange):
	records = (
		db.query(TrafficRecord)
		.filter(
			TrafficRecord.timestamp >= time_range.start,
			TrafficRecord.timestamp <= time_range.end,
		)
		.order_by(TrafficRecord.timestamp.asc())
		.all()
	)
	if not records:
		return {
			"no_data": True,
			"time_range": time_range,
		}
	total_rx = total_tx = total_rx_packets = total_tx_packets = 0
	data_rows = []
	for i, r in enumerate(records):
		rx = tx = rx_p = tx_p = 0
		if i > 0:
			prev = records[i - 1]

			if r.rx_bytes >= prev.rx_bytes:
				rx = r.rx_bytes - prev.rx_bytes
			if r.tx_bytes >= prev.tx_bytes:
				tx = r.tx_bytes - prev.tx_bytes
			if r.rx_packets >= prev.rx_packets:
				rx_p = r.rx_packets - prev.rx_packets
			if r.tx_packets >= prev.tx_packets:
				tx_p = r.tx_packets - prev.tx_packets
		total_rx += rx
		total_tx += tx
		total_rx_packets += rx_p
		total_tx_packets += tx_p
		data_rows.append({
			"timestamp": r.timestamp,
			"rx": rx,
			"tx": tx,
			"rx_packets": rx_p,
			"tx_packets": tx_p,
			"total_packets": rx_p + tx_p,
		})
	return {
		"no_data": False,
		"time_range": time_range,
		"data_rows": data_rows,
		"total_rx": total_rx,
		"total_tx": total_tx,
		"total_rx_packets": total_rx_packets,
		"total_tx_packets": total_tx_packets,
		"total_packets": total_rx_packets + total_tx_packets,
		"generated_at": datetime.utcnow(),
	}