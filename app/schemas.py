from datetime import datetime
from pydantic import BaseModel

class TimeRange(BaseModel):
	start: datetime
	end: datetime

class TrafficSummary(BaseModel):
	rx_bytes: int
	tx_bytes: int
	rx_packets: int
	tx_packets: int
	avg_rx_mbps: float
	avg_tx_mbps: float

class ChartData(BaseModel):
	labels: list[str]
	rx_data: list[float]
	tx_data: list[float]