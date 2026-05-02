from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Consent(Base):
    """Aceptación del consentimiento informado por un usuario."""
    __tablename__ = "consents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    aceptado_en = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address = Column(String(45), nullable=True)

    user = relationship("User", back_populates="consents")

    def __repr__(self):
        return f"<Consent user={self.user_id} v{self.version}>"
