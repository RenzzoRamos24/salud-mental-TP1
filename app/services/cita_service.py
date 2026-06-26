"""Servicio CRUD para citas psicólogo–estudiante (HU-19)."""
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.cita import Cita
from app.models.user import User

logger = logging.getLogger(__name__)


def _enriquecer(cita: Cita, db: Session) -> dict:
    """Agrega nombre/apellido/email del estudiante al dict de salida."""
    est = db.query(User).filter(User.id == cita.estudiante_id).first()
    return {
        "id": cita.id,
        "psicologo_id": cita.psicologo_id,
        "estudiante_id": cita.estudiante_id,
        "fecha": cita.fecha,
        "hora": cita.hora,
        "modalidad": cita.modalidad,
        "estado": cita.estado,
        "notas": cita.notas,
        "resumen_para_estudiante": getattr(cita, "resumen_para_estudiante", None),
        "completada_at": getattr(cita, "completada_at", None),
        "created_at": cita.created_at,
        "es_crisis": bool(getattr(cita, "es_crisis", False)),
        "estudiante_nombre": est.nombre if est else None,
        "estudiante_apellido": est.apellido if est else None,
        "estudiante_email": est.email if est else None,
    }


class CitaService:

    @staticmethod
    def crear(db: Session, psicologo_id: str, datos: dict) -> dict:
        cita = Cita(
            psicologo_id=psicologo_id,
            estudiante_id=datos["estudiante_id"],
            fecha=datos["fecha"],
            hora=datos["hora"],
            modalidad=datos.get("modalidad", "presencial"),
            notas=datos.get("notas"),
            es_crisis=bool(datos.get("es_crisis", False)),
        )
        db.add(cita)
        db.commit()
        db.refresh(cita)
        logger.info(
            f"Cita {cita.id} creada para estudiante {cita.estudiante_id} "
            f"(crisis={cita.es_crisis})"
        )
        return _enriquecer(cita, db)

    @staticmethod
    def listar(db: Session, psicologo_id: str, estudiante_id: str | None = None) -> list:
        q = db.query(Cita).filter(Cita.psicologo_id == psicologo_id)
        if estudiante_id:
            q = q.filter(Cita.estudiante_id == estudiante_id)
        citas = q.order_by(Cita.fecha.asc(), Cita.hora.asc()).all()
        return [_enriquecer(c, db) for c in citas]

    @staticmethod
    def actualizar(db: Session, cita_id: int, psicologo_id: str, cambios: dict) -> dict:
        cita = db.query(Cita).filter(
            Cita.id == cita_id,
            Cita.psicologo_id == psicologo_id,
        ).first()
        if not cita:
            raise ValueError("Cita no encontrada")

        # Si la cita pasa a "completada" y aún no tiene completada_at, lo seteamos.
        nuevo_estado = cambios.get("estado")
        if nuevo_estado == "completada" and not cita.completada_at:
            cita.completada_at = datetime.utcnow()

        for campo, valor in cambios.items():
            if valor is not None:
                setattr(cita, campo, valor)
        db.commit()
        db.refresh(cita)
        return _enriquecer(cita, db)

    @staticmethod
    def cancelar(db: Session, cita_id: int, psicologo_id: str) -> None:
        cita = db.query(Cita).filter(
            Cita.id == cita_id,
            Cita.psicologo_id == psicologo_id,
        ).first()
        if not cita:
            raise ValueError("Cita no encontrada")
        cita.estado = "cancelada"
        db.commit()

    # ── HU-30: agendamiento iniciado por el ESTUDIANTE ───────────────
    @staticmethod
    def solicitar_desde_estudiante(db: Session, estudiante_id: str, datos: dict) -> dict:
        """
        El estudiante propone una cita. Si tiene psicólogo asignado
        (`User.psicologo_id`), va a él; si no, se asigna al primer
        psicólogo activo del sistema (psicólogo de guardia).
        """
        estudiante = db.query(User).filter(User.id == estudiante_id).first()
        if not estudiante:
            raise ValueError("Estudiante no encontrado")

        psicologo_id = getattr(estudiante, "psicologo_id", None)
        if not psicologo_id:
            guardia = (
                db.query(User)
                .filter(User.role == "psicologo", User.activo.is_(True))
                .order_by(User.created_at.asc())
                .first()
            )
            if not guardia:
                raise ValueError(
                    "No hay psicólogos disponibles para tomar tu solicitud. "
                    "Avisa a soporte."
                )
            psicologo_id = guardia.id

        cita = Cita(
            psicologo_id=psicologo_id,
            estudiante_id=estudiante_id,
            fecha=datos["fecha"],
            hora=datos["hora"],
            modalidad=datos.get("modalidad", "presencial"),
            notas=datos.get("motivo") or datos.get("notas"),
            estado="pendiente",
        )
        db.add(cita)
        db.commit()
        db.refresh(cita)
        logger.info(f"Estudiante {estudiante_id} solicitó cita {cita.id}")
        return _enriquecer(cita, db)

    @staticmethod
    def listar_estudiante(db: Session, estudiante_id: str) -> list:
        citas = (db.query(Cita)
                   .filter(Cita.estudiante_id == estudiante_id)
                   .order_by(Cita.fecha.asc(), Cita.hora.asc())
                   .all())
        return [_enriquecer(c, db) for c in citas]

    @staticmethod
    def slots_sugeridos(
        db: Session,
        estudiante_id: str,
        cantidad: int = 4,
        dias_horizonte: int = 14,
    ) -> list[dict]:
        """
        Devuelve hasta `cantidad` slots libres (próximos días hábiles)
        descartando los horarios donde el psicólogo asignado (o de guardia)
        ya tiene una cita y los que caen sábado/domingo.

        Horarios base: 09:00, 10:00, 11:00, 15:00, 16:00, 17:00.
        """
        estudiante = db.query(User).filter(User.id == estudiante_id).first()
        if not estudiante:
            return []

        psic_id = getattr(estudiante, "psicologo_id", None)
        if not psic_id:
            guardia = (
                db.query(User)
                .filter(User.role == "psicologo", User.activo.is_(True))
                .order_by(User.created_at.asc())
                .first()
            )
            psic_id = guardia.id if guardia else None

        ocupadas = set()
        if psic_id:
            ocupadas = {
                (c.fecha, c.hora)
                for c in db.query(Cita)
                .filter(
                    Cita.psicologo_id == psic_id,
                    Cita.estado.in_(("pendiente", "confirmada")),
                )
                .all()
            }

        HORARIOS = ("09:00", "10:00", "11:00", "15:00", "16:00", "17:00")
        DIAS_LBL = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")
        MESES_LBL = ("Ene", "Feb", "Mar", "Abr", "May", "Jun",
                     "Jul", "Ago", "Sep", "Oct", "Nov", "Dic")

        hoy = datetime.now()
        out: list[dict] = []

        for off in range(1, dias_horizonte + 1):
            if len(out) >= cantidad:
                break
            d = hoy + timedelta(days=off)
            dow = d.weekday()
            if dow >= 5:  # sábado/domingo
                continue
            fecha = d.strftime("%Y-%m-%d")
            for hora in HORARIOS:
                if (fecha, hora) in ocupadas:
                    continue
                out.append({
                    "fecha": fecha,
                    "hora": hora,
                    "label": f"{DIAS_LBL[dow]} {d.day:02d}",
                    "label_largo": (
                        f"{DIAS_LBL[dow]} {d.day:02d} {MESES_LBL[d.month - 1]} · {hora}"
                    ),
                    "modalidad_sugerida": "online",
                })
                if len(out) >= cantidad:
                    break
        return out
