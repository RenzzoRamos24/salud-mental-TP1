"""HU-29 + HU-40: contenido psicoeducativo (alumno consume / admin gestiona)."""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.educational_content import EducationalContent
from datetime import datetime


class ContentService:

    @staticmethod
    def listar(db: Session, solo_activos: bool = True, categoria: str = None) -> list[dict]:
        q = db.query(EducationalContent)
        if solo_activos:
            q = q.filter(EducationalContent.activo.is_(True))
        if categoria:
            q = q.filter(EducationalContent.categoria == categoria)
        items = q.order_by(desc(EducationalContent.updated_at)).all()
        return [ContentService._serializar(i) for i in items]

    @staticmethod
    def obtener(db: Session, content_id: int) -> dict | None:
        item = db.query(EducationalContent).filter(EducationalContent.id == content_id).first()
        return ContentService._serializar(item) if item else None

    @staticmethod
    def crear(db: Session, data: dict) -> dict:
        if not data.get("titulo") or not data.get("descripcion"):
            raise ValueError("Título y descripción son obligatorios.")
        item = EducationalContent(
            titulo=data["titulo"],
            descripcion=data["descripcion"],
            tipo=data.get("tipo", "articulo"),
            categoria=data.get("categoria"),
            url=data.get("url"),
            contenido=data.get("contenido"),
            autor=data.get("autor"),
            icono=data.get("icono", "📄"),
            activo=data.get("activo", True),
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return ContentService._serializar(item)

    @staticmethod
    def actualizar(db: Session, content_id: int, data: dict) -> dict | None:
        item = db.query(EducationalContent).filter(EducationalContent.id == content_id).first()
        if not item:
            return None
        for campo in ("titulo", "descripcion", "tipo", "categoria",
                      "url", "contenido", "autor", "icono", "activo"):
            if campo in data and data[campo] is not None:
                setattr(item, campo, data[campo])
        item.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(item)
        return ContentService._serializar(item)

    @staticmethod
    def eliminar(db: Session, content_id: int) -> bool:
        item = db.query(EducationalContent).filter(EducationalContent.id == content_id).first()
        if not item:
            return False
        db.delete(item)
        db.commit()
        return True

    @staticmethod
    def _serializar(item: EducationalContent) -> dict:
        return {
            "id": item.id,
            "titulo": item.titulo,
            "descripcion": item.descripcion,
            "tipo": item.tipo,
            "categoria": item.categoria,
            "url": item.url,
            "contenido": item.contenido,
            "autor": item.autor,
            "icono": item.icono,
            "activo": item.activo,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        }
