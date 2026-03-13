from datetime import datetime
from sqlalchemy import Column, BigInteger, DateTime

from app.db import Base

class TrafficRecord(Base):
	__tablename__ = "traffic_records"
	id = Column(BigInteger, primary_key=True, index=True)
	timestamp = Column(DateTime, default=datetime.utcnow, index=True)
	rx_bytes = Column(BigInteger, default=0)
	tx_bytes = Column(BigInteger, default=0)
	rx_packets = Column(BigInteger, default=0)
	tx_packets = Column(BigInteger, default=0)