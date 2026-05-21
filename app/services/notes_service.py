"""HU-33: notas clínicas privadas del psicólogo."""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.clinical_note import ClinicalNote


class NotesService:

    @staticmethod
    def listar(db: Session, estudiante_id: str, psicologo_id: str = None) -> list[dict]:
        q = db.query(ClinicalNote).filter(ClinicalNote.estudiante_id == estudiante_id)
        if psicologo_id:
            q = q.filter(ClinicalNote.psicologo_id == psicologo_id)
        notas = q.order_by(desc(ClinicalNote.timestamp)).all()
        return [{
            "id": n.id,
            "texto": n.texto,
            "etiqueta": n.etiqueta,
            "timestamp": n.timestamp.isoformat(),
            "psicologo_id": n.psicologo_id,
        } for n in notas]

    @staticmethod
    def crear(db: Session, estudiante_id: str, psicologo_id: str,
              texto: str, etiqueta: str = None) -> ClinicalNote:
        if not texto or not texto.strip():
            raise ValueError("La nota no puede estar vacía")
        nota = ClinicalNote(
            estudiante_id=estudiante_id,
            psicologo_id=psicologo_id,
            texto=texto.strip(),
            etiqueta=etiqueta,
        )
        db.add(nota)
        db.commit()
        db.refresh(nota)
        return nota

    @staticmethod
    def eliminar(db: Session, nota_id: int, psicologo_id: str) -> bool:
        nota = (db.query(ClinicalNote)
                  .filter(ClinicalNote.id == nota_id,
                          ClinicalNote.psicologo_id == psicologo_id)
                  .first())
        if not nota:
            return False
        db.delete(nota)
        db.commit()
        return True
