"""
Servicio de consentimiento informado.
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models.consent import Consent
from app.config import settings

logger = logging.getLogger(__name__)


class ConsentService:

    @staticmethod
    def aceptar(
        db: Session,
        user_id: str,
        version: str,
        ip_address: Optional[str] = None,
    ) -> Consent:
        if version != settings.CONSENT_VERSION_ACTUAL:
            raise ValueError(
                f"Versión inválida. Esperada: {settings.CONSENT_VERSION_ACTUAL}"
            )

        existente = (
            db.query(Consent)
            .filter(Consent.user_id == user_id, Consent.version == version)
            .first()
        )
        if existente:
            return existente

        consent = Consent(user_id=user_id, version=version, ip_address=ip_address)
        db.add(consent)
        db.commit()
        db.refresh(consent)

        logger.info(f"📝 Consentimiento aceptado por {user_id} v{version}")
        return consent

    @staticmethod
    def estado(db: Session, user_id: str) -> dict:
        consent = (
            db.query(Consent)
            .filter(
                Consent.user_id == user_id,
                Consent.version == settings.CONSENT_VERSION_ACTUAL,
            )
            .order_by(Consent.aceptado_en.desc())
            .first()
        )
        return {
            "aceptado": consent is not None,
            "version": consent.version if consent else None,
            "aceptado_en": consent.aceptado_en if consent else None,
            "version_actual": settings.CONSENT_VERSION_ACTUAL,
        }
