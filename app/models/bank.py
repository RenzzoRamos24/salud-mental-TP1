"""
Modelos del banco de instrumentos clínicos y del sistema de cuestionarios de Sami.

Capas:
  * Banco fijo (validado): BankInstrumento + BankItem + BankFraseIncompleta.
    Cargado por seed (`seeds/banco_instrumentos.sql`), NO editable por nadie en
    la app — son escalas publicadas con cita literatura (PHQ-A, GAD-7, etc.).

  * Banco personalizable (custom): BloqueCustom + BloqueCustomItem.
    La psicóloga crea estos bloques con sus propias preguntas, escala y
    cortes. Quedan en el banco junto a los instrumentos validados.

  * Plantillas: PlantillaCuestionario + PlantillaBloque. La psicóloga arma
    plantillas eligiendo qué bloques (validados o custom) incluir.

  * Aplicación: AplicacionCuestionario (asignación a un alumno) +
    RespuestaAplicacion (cada respuesta del alumno con su ítem origen).
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.database import Base


# ── Banco fijo (validado) ────────────────────────────────────────────────────


class BankInstrumento(Base):
    __tablename__ = "bank_instrumento"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(20), nullable=False, unique=True)
    nombre = Column(String(200), nullable=False)
    autor = Column(String(200), nullable=False)
    anio = Column(Integer, nullable=False)
    dominio = Column(String(80), nullable=False)
    tipo_escala = Column(String(20), nullable=False)
    likert_min = Column(Integer, nullable=True)
    likert_max = Column(Integer, nullable=True)
    n_items = Column(Integer, nullable=False)
    tiempo_min = Column(Integer, nullable=True)
    instruccion = Column(Text, nullable=True)
    citacion = Column(Text, nullable=False)
    validacion_es = Column(Text, nullable=True)
    activo = Column(Integer, nullable=False, default=1, server_default="1")

    items = relationship(
        "BankItem", back_populates="instrumento", order_by="BankItem.numero"
    )


class BankItem(Base):
    __tablename__ = "bank_item"
    __table_args__ = (UniqueConstraint("instrumento_id", "numero"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    instrumento_id = Column(
        Integer, ForeignKey("bank_instrumento.id"), nullable=False, index=True
    )
    numero = Column(Integer, nullable=False)
    texto = Column(Text, nullable=False)
    inverso = Column(Integer, nullable=False, default=0, server_default="0")
    criterio_dsm5 = Column(Text, nullable=True)
    bandera_crisis = Column(Integer, nullable=False, default=0, server_default="0")

    instrumento = relationship("BankInstrumento", back_populates="items")


class BankFraseIncompleta(Base):
    __tablename__ = "bank_frase_incompleta"

    id = Column(Integer, primary_key=True, autoincrement=True)
    area = Column(String(40), nullable=False, index=True)
    numero = Column(Integer, nullable=False, unique=True)
    texto = Column(Text, nullable=False)
    activo = Column(Integer, nullable=False, default=1, server_default="1")


# ── Banco custom (psicóloga) ─────────────────────────────────────────────────


class BloqueCustom(Base):
    """Bloque que la psicóloga crea desde cero con sus propias preguntas."""
    __tablename__ = "bloque_custom"

    id = Column(Integer, primary_key=True, autoincrement=True)
    psicologo_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    nombre = Column(String(200), nullable=False)
    dominio = Column(String(80), nullable=True)
    # 'likert' (rango configurable) | 'binaria' (0/1)
    tipo_escala = Column(String(20), nullable=False)
    likert_min = Column(Integer, nullable=False, default=0)
    likert_max = Column(Integer, nullable=False, default=3)
    instruccion = Column(Text, nullable=True)
    # Cortes (suma total del bloque). El front sugiere por tercios.
    corte_sin_alerta_max = Column(Integer, nullable=False)
    corte_posible_max = Column(Integer, nullable=False)
    corte_alto_max = Column(Integer, nullable=False)
    activo = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    items = relationship(
        "BloqueCustomItem", back_populates="bloque", order_by="BloqueCustomItem.numero",
        cascade="all, delete-orphan",
    )


class BloqueCustomItem(Base):
    __tablename__ = "bloque_custom_item"
    __table_args__ = (UniqueConstraint("bloque_id", "numero"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    bloque_id = Column(Integer, ForeignKey("bloque_custom.id"), nullable=False, index=True)
    numero = Column(Integer, nullable=False)
    texto = Column(Text, nullable=False)
    inverso = Column(Integer, nullable=False, default=0)

    bloque = relationship("BloqueCustom", back_populates="items")


# ── Plantillas de cuestionario ──────────────────────────────────────────────


class PlantillaCuestionario(Base):
    __tablename__ = "plantilla_cuestionario"

    id = Column(Integer, primary_key=True, autoincrement=True)
    psicologo_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    activa = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    bloques = relationship(
        "PlantillaBloque", back_populates="plantilla", order_by="PlantillaBloque.orden",
        cascade="all, delete-orphan",
    )


class PlantillaBloque(Base):
    """Un bloque dentro de una plantilla. Apunta a un instrumento del banco,
    a un bloque custom, o al banco de frases incompletas (con áreas elegidas)."""
    __tablename__ = "plantilla_bloque"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plantilla_id = Column(
        Integer, ForeignKey("plantilla_cuestionario.id"), nullable=False, index=True
    )
    orden = Column(Integer, nullable=False, default=0)
    # 'instrumento' | 'custom' | 'frases'
    tipo = Column(String(20), nullable=False)
    instrumento_id = Column(Integer, ForeignKey("bank_instrumento.id"), nullable=True)
    bloque_custom_id = Column(Integer, ForeignKey("bloque_custom.id"), nullable=True)
    # Para 'frases': lista CSV de áreas activas (ej: "familia,autoconcepto,escuela")
    frases_areas = Column(Text, nullable=True)

    plantilla = relationship("PlantillaCuestionario", back_populates="bloques")


# ── Aplicación (asignación al alumno) ───────────────────────────────────────


class AplicacionCuestionario(Base):
    __tablename__ = "aplicacion_cuestionario"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plantilla_id = Column(
        Integer, ForeignKey("plantilla_cuestionario.id"), nullable=False, index=True
    )
    estudiante_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    psicologo_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    # 'pendiente' | 'en_progreso' | 'completado' | 'revisado'
    estado = Column(String(20), nullable=False, default="pendiente")
    asignada_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    iniciada_at = Column(DateTime, nullable=True)
    completada_at = Column(DateTime, nullable=True)
    revisada_at = Column(DateTime, nullable=True)

    # Resultados de la evaluación al cerrar (JSON serializado).
    resultado_json = Column(Text, nullable=True)
    riesgo_global = Column(String(20), nullable=True)
    crisis_activada = Column(Boolean, nullable=False, default=False)

    respuestas = relationship(
        "RespuestaAplicacion", back_populates="aplicacion",
        cascade="all, delete-orphan",
    )


class RespuestaAplicacion(Base):
    __tablename__ = "respuesta_aplicacion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    aplicacion_id = Column(
        Integer, ForeignKey("aplicacion_cuestionario.id"), nullable=False, index=True
    )
    # Identifica el ítem origen.
    # Para 'instrumento': "INSTR:{codigo}:{numero}"  (ej. "INSTR:PHQ-A:1")
    # Para 'custom':      "CUSTOM:{bloque_id}:{numero}"
    # Para 'frase':       "FRASE:{numero}"
    origen = Column(String(80), nullable=False, index=True)
    # Valor de respuesta numérico (Likert / binario).
    valor_num = Column(Integer, nullable=True)
    # Texto libre (para frases incompletas).
    valor_texto = Column(Text, nullable=True)
    respondida_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    aplicacion = relationship("AplicacionCuestionario", back_populates="respuestas")
