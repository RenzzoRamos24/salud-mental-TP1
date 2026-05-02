from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class PasswordResetToken(Base):
    """Token temporal de 6 dígitos para recuperación de contraseña."""
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(10), nullable=False, index=True)
    expira_en = Column(DateTime, nullable=False)
    usado = Column(Boolean, default=False, nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="password_resets")

    def __repr__(self):
        return f"<PasswordResetToken user={self.user_id} usado={self.usado}>"
