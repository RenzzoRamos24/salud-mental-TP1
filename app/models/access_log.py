from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base


class AccessLog(Base):
    """Registro de auditoría de accesos al sistema (HU-22)."""
    __tablename__ = "access_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=True, index=True)
    email = Column(String(255), nullable=True)
    role = Column(String(20), nullable=True)
    method = Column(String(10), nullable=False)
    endpoint = Column(String(255), nullable=False)
    status_code = Column(Integer, nullable=True)
    ip = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<AccessLog {self.method} {self.endpoint} {self.status_code}>"
