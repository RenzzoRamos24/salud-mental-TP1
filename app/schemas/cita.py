from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CitaCreate(BaseModel):
    estudiante_id: str
    fecha: str        # YYYY-MM-DD
    hora: str         # HH:MM
    modalidad: str = "presencial"
    notas: Optional[str] = None
    # True si la psicóloga agenda esta cita como atención de crisis. Al
    # completarse adelanta el cierre del ciclo en curso.
    es_crisis: bool = False


class CitaUpdate(BaseModel):
    estado: Optional[str] = None
    notas: Optional[str] = None
    fecha: Optional[str] = None
    hora: Optional[str] = None
    modalidad: Optional[str] = None
    resumen_para_estudiante: Optional[str] = None
    es_crisis: Optional[bool] = None


class CitaSolicitudEstudiante(BaseModel):
    """Pedido de cita iniciado por el estudiante (HU-30)."""
    fecha: str        # YYYY-MM-DD
    hora: str         # HH:MM
    modalidad: str = "online"
    motivo: Optional[str] = None


class CitaOut(BaseModel):
    id: int
    psicologo_id: Optional[str] = None
    estudiante_id: str
    fecha: str
    hora: str
    modalidad: str
    estado: str
    notas: Optional[str] = None
    resumen_para_estudiante: Optional[str] = None
    completada_at: Optional[datetime] = None
    created_at: datetime
    es_crisis: bool = False
    # Datos del estudiante (se añaden en el servicio)
    estudiante_nombre: Optional[str] = None
    estudiante_apellido: Optional[str] = None
    estudiante_email: Optional[str] = None

    class Config:
        from_attributes = True


class CitaOutEstudiante(BaseModel):
    """Vista de una cita tal como la recibe el ESTUDIANTE (HU-52).

    Deliberadamente NO expone `notas`: ese campo es la anotación interna de
    la psicóloga y nunca debe llegar al alumno. Lo único dirigido a él es
    `resumen_para_estudiante`.
    """
    id: int
    psicologo_id: Optional[str] = None
    estudiante_id: str
    fecha: str
    hora: str
    modalidad: str
    estado: str
    resumen_para_estudiante: Optional[str] = None
    completada_at: Optional[datetime] = None
    created_at: datetime
    es_crisis: bool = False

    class Config:
        from_attributes = True
