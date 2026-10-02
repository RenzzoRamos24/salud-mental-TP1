"""
Etiquetado clínico ciego — el psicólogo etiqueta dentro del sistema.

Para qué
--------
Dos cosas a la vez, con el mismo trabajo humano:

1. **Medir cuánto se equivoca el modelo.** La psicóloga emite su juicio sin
   ver nada de lo que dijo BETO ni el SVM, y el sistema cruza después. Eso
   convierte su criterio en patrón de oro y permite calcular recall,
   precisión, especificidad y κ. Si etiquetara viendo la predicción, el
   número mediría anclaje y no concordancia.

2. **Juntar datos para reentrenar.** Cada etiqueta queda guardada con el
   texto completo y con lo que el modelo había dicho en ese momento, así que
   el conjunto es autosuficiente: sirve de dataset aunque después se cambie
   el clasificador, los umbrales o las hipótesis.

Las dos necesidades piden cosas distintas y por eso existe `MuestraEtiquetado`:

- Para **medir** hace falta una muestra con probabilidad de inclusión
  conocida. Si la psicóloga etiqueta lo que le llama la atención, no hay
  forma de proyectar el recall al corpus completo.
- Para **entrenar** conviene todo lo que se pueda etiquetar, sin importar
  cómo se eligió.

Entonces la cola le sirve primero la muestra estratificada (marcada con su
estrato y su peso) y después el resto del corpus. Las métricas se calculan
solo sobre la muestra; el dataset de entrenamiento usa todo.
"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.database import Base

# ── Vocabularios ───────────────────────────────────────────────────────────

RIESGOS = ("SIN_RIESGO", "BAJO", "MEDIO", "ALTO", "CRITICO")
CONFIANZAS = ("alta", "media", "baja")
# Las 4 categorías que el clasificador produce hoy (nlp_service.py). No son
# 8: la taxonomía de 8 se retiró en el commit 6850641. Pedirle al psicólogo
# etiquetas que el modelo no emite haría la comparación imposible.
CATEGORIAS = ("depresion", "ansiedad", "adaptativo", "neutral")
ESTRATOS = (
    "clinica_alta",
    "clinica_media",
    "benigna_confiada",
    "baja_todas",
    "aleatoria_simple",
)


class MuestraEtiquetado(Base):
    """
    El plan de muestreo congelado: qué frases entran en la medición, en qué
    estrato cayó cada una y con qué peso se proyecta al corpus.

    Se genera una vez (`EtiquetadoService.generar_muestra`) y no se toca. El
    peso es `N_estrato / n_muestreado`: una frase del estrato `aleatoria_simple`
    representa a ~9 frases del corpus, una de `clinica_alta` a ~2.4. Sin esto
    la prevalencia y la precisión quedan infladas, porque los estratos
    clínicos están sobre-representados a propósito.
    """

    __tablename__ = "muestra_etiquetado"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Código opaco que se le muestra al evaluador (F-1008). No revela de qué
    # alumno viene ni en qué orden se respondió.
    codigo = Column(String(16), nullable=False, unique=True)

    aplicacion_id = Column(
        Integer,
        ForeignKey("aplicacion_cuestionario.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    frase_numero = Column(Integer, nullable=False)

    estrato = Column(String(24), nullable=False)
    peso = Column(Float, nullable=False)
    orden = Column(Integer, nullable=False)

    # Trazabilidad del muestreo: con esto se reproduce el sorteo.
    semilla = Column(Integer, nullable=False)
    generada_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "aplicacion_id", "frase_numero", name="uq_muestra_frase"
        ),
        Index("ix_muestra_orden", "orden"),
    )


class EtiquetaFrase(Base):
    """
    Juicio clínico sobre una frase incompleta. Es la unidad que valida BETO.

    `ideacion_presente` es la etiqueta crítica: contra ella se mide el recall
    de la bandera de crisis, que es la métrica ética del sistema (umbral
    preregistrado ≥ 0.90 en METRICAS_VALIDACION.md).

    `sufrimiento_grave` existe porque la hipótesis que BETO evalúa para
    `depresion` es compuesta: habla de ideas de muerte *o* desesperanza total
    *o* sentimientos incapacitantes de inutilidad. Si se mide la bandera solo
    contra ideación, cada frase de desesperanza severa que el modelo marcó
    bien se cuenta como falso positivo. Con los dos campos se reportan las dos
    cosas por separado y cada número dice lo que de verdad mide.
    """

    __tablename__ = "etiqueta_frase"

    id = Column(Integer, primary_key=True, autoincrement=True)

    aplicacion_id = Column(
        Integer,
        ForeignKey("aplicacion_cuestionario.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    frase_numero = Column(Integer, nullable=False)
    evaluador_id = Column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )

    # ── Copia del texto ────────────────────────────────────────────────
    # Redundante con la BD a propósito: hace que el dataset de reentrenamiento
    # sea autosuficiente y deja constancia de qué texto exacto se juzgó, por
    # si una respuesta se corrige después.
    texto_estimulo = Column(Text, nullable=False)
    texto_respuesta = Column(Text, nullable=False)

    # ── El juicio ──────────────────────────────────────────────────────
    ideacion_presente = Column(Boolean, nullable=False)
    sufrimiento_grave = Column(Boolean, nullable=False, default=False)
    categoria = Column(String(16), nullable=True)
    confianza = Column(String(8), nullable=False, default="alta")
    comentario = Column(Text, nullable=True)

    # ── Metodología ────────────────────────────────────────────────────
    es_muestra_metrica = Column(Boolean, nullable=False, default=False)
    estrato = Column(String(24), nullable=True)
    peso = Column(Float, nullable=True)
    segundos = Column(Integer, nullable=True)

    # ── Lo que el modelo había dicho, congelado ────────────────────────
    # Se escribe en el servidor al guardar, nunca viaja al cliente antes.
    # Congelarlo permite reevaluar el modelo después sin perder la
    # comparación original.
    modelo_crisis = Column(Boolean, nullable=True)
    modelo_dominante = Column(String(24), nullable=True)
    modelo_scores_json = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        # Una etiqueta por frase y por evaluador: con dos psicólogos sobre el
        # mismo subconjunto sale el κ inter-evaluador, que es el techo contra
        # el cual se interpreta el κ del sistema.
        UniqueConstraint(
            "aplicacion_id", "frase_numero", "evaluador_id",
            name="uq_etiqueta_frase_evaluador",
        ),
    )


class EtiquetaCaso(Base):
    """
    Juicio clínico sobre un cuestionario completo. Valida las reglas del
    EvaluatorService y el SVM.

    Esta es la tabla que rompe la circularidad del SVM: hoy se entrenó con
    etiquetas derivadas de los cortes de Lovibond y se evaluó contra esos
    mismos cortes, así que el 100 % del piloto solo demuestra que reproduce
    una fórmula. Con `riesgo_clinico` humano hay, por primera vez, un objetivo
    de entrenamiento que no sale de la propia fórmula.
    """

    __tablename__ = "etiqueta_caso"

    id = Column(Integer, primary_key=True, autoincrement=True)

    aplicacion_id = Column(
        Integer,
        ForeignKey("aplicacion_cuestionario.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evaluador_id = Column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )

    riesgo_clinico = Column(String(16), nullable=False)
    requiere_derivacion = Column(Boolean, nullable=False, default=False)
    # None cuando el pack no da material para opinar (p. ej. solo DASS-21 sin
    # el ítem de ideación): forzar un sí/no ahí inventaría datos.
    ideacion_presente = Column(Boolean, nullable=True)
    confianza = Column(String(8), nullable=False, default="alta")
    comentario = Column(Text, nullable=True)
    segundos = Column(Integer, nullable=True)

    # ── Congelado al momento de etiquetar ──────────────────────────────
    modelo_riesgo = Column(String(16), nullable=True)
    modelo_crisis = Column(Boolean, nullable=True)
    modelo_svm_clase = Column(String(16), nullable=True)
    modelo_svm_prob = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "aplicacion_id", "evaluador_id", name="uq_etiqueta_caso_evaluador"
        ),
    )
