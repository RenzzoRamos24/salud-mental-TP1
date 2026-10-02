"""
EtiquetadoService — el psicólogo etiqueta dentro del sistema, a ciegas.

Tres responsabilidades:

1. **Servir la cola ciega.** Devuelve la próxima frase o el próximo caso sin
   nada de lo que dijo el modelo. La ceguedad se aplica acá, en el servidor:
   el payload no contiene scores ni banderas ni riesgo. Ocultarlo en el
   frontend no sirve — se ve abriendo el inspector, y entonces la
   concordancia deja de medir concordancia.

2. **Guardar el juicio congelando la predicción.** Al grabar la etiqueta se
   copia lo que el modelo había dicho en ese momento. Así se puede cambiar el
   clasificador, los umbrales o las hipótesis sin perder la comparación
   original, y el dataset de reentrenamiento queda autosuficiente.

3. **Calcular las métricas al final.** Matriz de confusión, recall,
   precisión, κ, y el barrido de umbral que dice si 0.55 es el corte correcto.
   Se calculan sobre la muestra con probabilidad de inclusión conocida, y se
   proyectan al corpus con los pesos del estrato.

Por qué el muestreo vive acá y no en un script
----------------------------------------------
`scripts/muestrear_frases_ideacion.py` hace lo mismo, pero deja el plan en un
JSON local que no está en el repo. Si el plan vive en la BD, la psicóloga
puede etiquetar desde cualquier despliegue y el muestreo queda auditado junto
con las etiquetas. La estratificación de acá es la misma: mismos cortes,
mismas cuotas, misma semilla por defecto.
"""
from __future__ import annotations

import hashlib
import json
import logging
import random
import unicodedata
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.bank import (
    AplicacionCuestionario,
    BankFraseIncompleta,
    PlantillaCuestionario,
    RespuestaAplicacion,
)
from app.models.etiquetado import (
    CATEGORIAS,
    PREDOMINANTES,
    CONFIANZAS,
    ESTRATOS,
    RIESGOS,
    EtiquetaCaso,
    EtiquetaFrase,
    MuestraEtiquetado,
)
from app.models.user import User

logger = logging.getLogger(__name__)

# ── Parámetros del muestreo (iguales a muestrear_frases_ideacion.py) ───────

SEMILLA_DEFAULT = 20260910

# El orden de las colas se mezcla con esta sal, igual para todos los
# evaluadores. Mezclado para que la secuencia no insinúe nada (no va por
# riesgo ni por fecha), pero COMPARTIDO a propósito: si cada evaluador
# recibiera su propio orden, dos psicólogas que no terminan el corpus
# completo se solaparían en muy pocos casos y el κ inter-evaluador quedaría
# calculado sobre un puñado de filas. Con orden común, el solapamiento es
# siempre igual al mínimo de lo que avanzó cada una.
SAL_ORDEN = "sami-etiquetado-v1"

CLINICAS = ("depresion", "ansiedad")
NO_CLINICAS = ("adaptativo", "neutral")

CUOTAS = {
    "clinica_alta": 30,
    "clinica_media": 15,
    "benigna_confiada": 20,
    "baja_todas": 15,
    "aleatoria_simple": 20,
}

# Regla de crisis vigente en nlp_service.py. Se repite acá porque las
# métricas tienen que poder recalcularse sobre los scores congelados sin
# cargar el modelo.
UMBRAL_CRISIS = 0.55


def _norm(t: str) -> str:
    return unicodedata.normalize("NFKC", t or "").strip().lower()


# Clave en `configuraciones`. El corte vive en la BD y no en el código porque
# la base de producción acumula cohortes: el piloto de julio (cargado como
# alumnos ficticios) y las aplicaciones reales en el aula. Etiquetar las dos
# juntas mezclaría dos instrumentos y dos momentos en una sola métrica.
CLAVE_CORTE = "etiquetado_desde"

# Frontera entre cohortes. El piloto del colegio se digitalizó el 2026-07-02 y
# quedó cargado en la base como alumnos ficticios; las aplicaciones reales en
# el aula son de fines de septiembre en adelante. Este default hace que el
# etiquetado arranque mirando solo la cohorte nueva **sin que nadie tenga que
# configurar nada**, que es lo que se pidió: el piloto queda como registro
# histórico, consultable en el panel, pero fuera de la validación.
#
# Se puede mover desde la pantalla de admin (POST /etiquetado/corte), y
# `"todo"` lo desactiva si alguna vez hiciera falta volver a incluir julio.
CORTE_DEFAULT_COHORTE = "2026-09-01"

# Prefijo reservado para cuentas de prueba. Sus etiquetas se guardan igual
# —así se puede ensayar el flujo completo— pero quedan fuera de las métricas.
PREFIJO_PRUEBA = "SAMI-PSI-PRUEBA"


def corte_desde(db: Session) -> str | None:
    """
    Fecha (YYYY-MM-DD) desde la cual se etiqueta.

    Si nadie configuró nada devuelve `CORTE_DEFAULT_COHORTE`, no None: la
    base de producción tiene las dos cohortes y el default seguro es mirar
    solo la nueva. Para incluir todo hay que pedirlo explícitamente.
    """
    from app.models.configuracion import Configuracion
    row = (
        db.query(Configuracion)
        .filter(Configuracion.clave == CLAVE_CORTE)
        .first()
    )
    if not row:
        return CORTE_DEFAULT_COHORTE
    try:
        valor = json.loads(row.valor)
    except (ValueError, TypeError):
        return CORTE_DEFAULT_COHORTE
    # `None` guardado a propósito = sin corte, entra todo el histórico.
    return valor or None


def ids_evaluadores_prueba(db: Session) -> set[str]:
    """Cuentas de prueba, por prefijo del código de acceso."""
    filas = (
        db.query(User.id)
        .filter(
            User.role == "psicologo",
            User.codigo_acceso.like(f"{PREFIJO_PRUEBA}%"),
        )
        .all()
    )
    return {f[0] for f in filas}


def fijar_corte(db: Session, desde: str | None) -> str | None:
    """Fija (o borra, con None) el corte de fecha del etiquetado."""
    from app.models.configuracion import Configuracion

    if desde:
        try:
            datetime.strptime(desde, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"Fecha inválida '{desde}'. El formato es YYYY-MM-DD."
            )
    row = (
        db.query(Configuracion)
        .filter(Configuracion.clave == CLAVE_CORTE)
        .first()
    )
    if row:
        row.valor = json.dumps(desde, ensure_ascii=False)
        row.updated_at = datetime.utcnow()
    else:
        db.add(Configuracion(
            clave=CLAVE_CORTE, valor=json.dumps(desde, ensure_ascii=False)
        ))
    db.commit()
    return desde


def _svm_instalado() -> bool:
    """¿Existe el .joblib en este servidor? En Azure no: el paquete de deploy
    (ver DEPLOY.md) no incluye `models/`."""
    from app.services.svm_service import SVMService
    return SVMService.disponible()


def _codigo_estable(aplicacion_id: int, numero: int) -> str:
    """Código opaco y determinista para frases fuera de la muestra."""
    h = hashlib.md5(f"{aplicacion_id}:{numero}".encode()).hexdigest()
    return f"C-{int(h[:6], 16) % 9000 + 1000}"


class EtiquetadoService:

    # ══════════════════════════════════════════════════════════════════
    # Corpus
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def corpus_frases(db: Session) -> list[dict]:
        """
        Todas las frases respondidas que tienen scores del modelo vigente.

        Las frases evaluadas con la taxonomía de 8 categorías (anterior al
        commit 6850641) se descartan: no tienen `depresion`, así que no se
        pueden comparar contra la regla de crisis actual. Para incluirlas hay
        que re-evaluarlas con `POST /admin/piloto/re-evaluar-beto`.
        """
        q = db.query(
            AplicacionCuestionario.id, AplicacionCuestionario.resultado_json
        ).filter(AplicacionCuestionario.resultado_json.isnot(None))
        desde = corte_desde(db)
        if desde:
            q = q.filter(
                AplicacionCuestionario.completada_at
                >= datetime.strptime(desde, "%Y-%m-%d")
            )
        filas = q.order_by(AplicacionCuestionario.id).all()
        out = []
        descartadas_modelo_viejo = 0
        for apl_id, rj in filas:
            try:
                resultado = json.loads(rj)
            except (ValueError, TypeError):
                logger.warning("resultado_json ilegible en aplicación %s", apl_id)
                continue
            for f in resultado.get("frases") or []:
                scores = f.get("scores") or {}
                respuesta = (f.get("respuesta") or "").strip()
                if not respuesta:
                    continue
                if "depresion" not in scores:
                    descartadas_modelo_viejo += 1
                    continue
                out.append({
                    "aplicacion_id": apl_id,
                    "frase_numero": f.get("numero"),
                    "area": f.get("area"),
                    "estimulo": (f.get("pregunta") or "").strip(),
                    "respuesta": respuesta,
                    "scores": {k: float(v) for k, v in scores.items()},
                    "dominante": f.get("dominante"),
                    "crisis": bool(f.get("crisis")),
                })
        if descartadas_modelo_viejo:
            logger.info(
                "Corpus de etiquetado: %s frases descartadas por venir del "
                "modelo de 8 categorías.", descartadas_modelo_viejo,
            )
        return out

    # ══════════════════════════════════════════════════════════════════
    # Muestreo estratificado
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def _estratificar(frases: list[dict]) -> dict[str, list[dict]]:
        estratos: dict[str, list[dict]] = {k: [] for k in CUOTAS}
        for f in frases:
            s = f["scores"]
            max_clin = max(s.get(k, 0.0) for k in CLINICAS)
            max_todas = max(s.values()) if s else 0.0
            dom = f["dominante"]
            if max_clin >= 0.40:
                estratos["clinica_alta"].append(f)
            elif max_clin >= 0.25:
                estratos["clinica_media"].append(f)
            elif dom in NO_CLINICAS and s.get(dom, 0.0) >= 0.55:
                estratos["benigna_confiada"].append(f)
            elif max_todas < 0.40:
                estratos["baja_todas"].append(f)
            else:
                estratos["aleatoria_simple"].append(f)
        return estratos

    @staticmethod
    def generar_muestra(
        db: Session,
        n: int = 100,
        semilla: int = SEMILLA_DEFAULT,
        reemplazar: bool = False,
    ) -> dict:
        """
        Sortea la muestra de medición y la persiste.

        Idempotente por diseño: si ya hay un plan, no lo toca salvo
        `reemplazar=True`, y ni así si ya existen etiquetas de la muestra —
        regenerar el plan después de empezar a etiquetar invalidaría los pesos
        y, con ellos, todas las métricas proyectadas.
        """
        existentes = db.query(MuestraEtiquetado).count()
        if existentes and not reemplazar:
            return {
                "creada": False,
                "motivo": (
                    f"Ya existe un plan de muestreo con {existentes} frases. "
                    "Usá reemplazar=true para rehacerlo."
                ),
                "n": existentes,
            }
        if existentes and reemplazar:
            ya_etiquetadas = (
                db.query(EtiquetaFrase)
                .filter(EtiquetaFrase.es_muestra_metrica.is_(True))
                .count()
            )
            if ya_etiquetadas:
                raise ValueError(
                    f"No se puede rehacer el muestreo: ya hay {ya_etiquetadas} "
                    "etiquetas de la muestra. Los pesos quedarían inconsistentes "
                    "con lo etiquetado y las métricas proyectadas dejarían de "
                    "ser válidas."
                )
            db.query(MuestraEtiquetado).delete(synchronize_session=False)
            db.flush()

        frases = EtiquetadoService.corpus_frases(db)
        if not frases:
            desde = corte_desde(db)
            extra = (
                f" El corte de fecha vigente es {desde}: puede que ninguna "
                "aplicación de esa cohorte tenga frases respondidas."
                if desde else ""
            )
            raise ValueError(
                "No hay frases con scores del modelo vigente. Corré primero "
                "las aplicaciones con frases, o re-evaluá con BETO." + extra
            )

        estratos = EtiquetadoService._estratificar(frases)
        rng = random.Random(semilla)
        escala = n / sum(CUOTAS.values())

        vistos: set[tuple[str, str]] = set()
        muestra: list[dict] = []
        resumen: dict[str, dict] = {}

        for nombre, cuota in CUOTAS.items():
            pool = list(estratos[nombre])
            rng.shuffle(pool)
            objetivo = max(1, round(cuota * escala)) if pool else 0
            elegidas = []
            for f in pool:
                if len(elegidas) >= objetivo:
                    break
                clave = (_norm(f["estimulo"]), _norm(f["respuesta"]))
                if clave in vistos:
                    continue  # no se gastan etiquetas en frases idénticas
                vistos.add(clave)
                elegidas.append(dict(f, estrato=nombre))
            muestra.extend(elegidas)
            resumen[nombre] = {
                "N_estrato": len(pool),
                "n_muestreado": len(elegidas),
                "peso": round(len(pool) / len(elegidas), 4) if elegidas else None,
            }

        # Códigos opacos y orden mezclado: ni el código ni la posición dejan
        # ver de qué alumno viene la frase ni en qué estrato cayó.
        codigos = rng.sample(range(1000, 10000), len(muestra))
        for f, c in zip(muestra, codigos):
            f["codigo"] = f"F-{c}"
        muestra.sort(key=lambda f: f["codigo"])

        for orden, f in enumerate(muestra, start=1):
            db.add(MuestraEtiquetado(
                codigo=f["codigo"],
                aplicacion_id=f["aplicacion_id"],
                frase_numero=f["frase_numero"],
                estrato=f["estrato"],
                peso=resumen[f["estrato"]]["peso"],
                orden=orden,
                semilla=semilla,
            ))
        db.commit()

        logger.info("Muestra de etiquetado generada: %s frases", len(muestra))
        return {
            "creada": True,
            "n": len(muestra),
            "n_corpus": len(frases),
            "semilla": semilla,
            "corte_desde": corte_desde(db),
            "estratos": resumen,
        }

    # ══════════════════════════════════════════════════════════════════
    # Cola de frases (ciega)
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def siguiente_frase(db: Session, evaluador_id: str) -> dict | None:
        """
        Próxima frase sin etiquetar para este evaluador.

        Orden: primero la muestra de medición por su `orden`, después el resto
        del corpus mezclado de forma determinista por evaluador. El
        determinismo es lo que permite parar y seguir mañana sin repetir ni
        saltear.

        El payload NO lleva scores, ni dominante, ni bandera de crisis.
        """
        etiquetadas = {
            (a, n) for a, n in db.query(
                EtiquetaFrase.aplicacion_id, EtiquetaFrase.frase_numero
            ).filter(EtiquetaFrase.evaluador_id == evaluador_id).all()
        }

        corpus = {
            (f["aplicacion_id"], f["frase_numero"]): f
            for f in EtiquetadoService.corpus_frases(db)
        }

        # ── Fase 1: la muestra de medición ────────────────────────────
        plan = (
            db.query(MuestraEtiquetado)
            .order_by(MuestraEtiquetado.orden)
            .all()
        )
        n_muestra = len(plan)
        hechas_muestra = 0
        pendiente_muestra = None
        for m in plan:
            clave = (m.aplicacion_id, m.frase_numero)
            if clave in etiquetadas:
                hechas_muestra += 1
            elif pendiente_muestra is None and clave in corpus:
                pendiente_muestra = (m, corpus[clave])

        if pendiente_muestra is not None:
            m, f = pendiente_muestra
            return {
                "ref": f"{m.aplicacion_id}:{m.frase_numero}",
                "codigo": m.codigo,
                "estimulo": f["estimulo"],
                "respuesta": f["respuesta"],
                "fase": "muestra",
                "progreso": {
                    "fase": "Muestra de medición",
                    "hechas": hechas_muestra,
                    "total": n_muestra,
                },
            }

        # ── Fase 2: el resto del corpus (solo entrenamiento) ──────────
        claves_plan = {(m.aplicacion_id, m.frase_numero) for m in plan}
        resto = [
            f for k, f in corpus.items()
            if k not in claves_plan and k not in etiquetadas
        ]
        if not resto:
            return None

        # Mezcla determinista y compartida: las dos evaluadoras recorren el
        # resto del corpus en el mismo orden, así lo que hagan se solapa.
        resto.sort(key=lambda f: hashlib.md5(
            f"{SAL_ORDEN}:{f['aplicacion_id']}:{f['frase_numero']}".encode()
        ).hexdigest())
        f = resto[0]
        total_resto = len(corpus) - len(claves_plan)
        return {
            "ref": f"{f['aplicacion_id']}:{f['frase_numero']}",
            "codigo": _codigo_estable(f["aplicacion_id"], f["frase_numero"]),
            "estimulo": f["estimulo"],
            "respuesta": f["respuesta"],
            "fase": "corpus",
            "progreso": {
                "fase": "Resto del corpus (para reentrenar)",
                "hechas": total_resto - len(resto),
                "total": total_resto,
            },
        }

    @staticmethod
    def guardar_etiqueta_frase(
        db: Session,
        evaluador_id: str,
        ref: str,
        ideacion_presente: bool,
        sufrimiento_grave: bool = False,
        categoria: str | None = None,
        confianza: str = "alta",
        comentario: str | None = None,
        segundos: int | None = None,
    ) -> dict:
        try:
            apl_id_s, numero_s = ref.split(":")
            aplicacion_id, frase_numero = int(apl_id_s), int(numero_s)
        except (ValueError, AttributeError):
            raise ValueError(f"Referencia de frase inválida: '{ref}'.")

        if categoria and categoria not in CATEGORIAS:
            raise ValueError(
                f"Categoría '{categoria}' inválida. Usá una de: "
                f"{', '.join(CATEGORIAS)}."
            )
        if confianza not in CONFIANZAS:
            raise ValueError(
                f"Confianza '{confianza}' inválida. Usá: {', '.join(CONFIANZAS)}."
            )

        corpus = {
            (f["aplicacion_id"], f["frase_numero"]): f
            for f in EtiquetadoService.corpus_frases(db)
        }
        f = corpus.get((aplicacion_id, frase_numero))
        if f is None:
            raise ValueError(
                f"La frase {ref} no está en el corpus etiquetable."
            )

        m = (
            db.query(MuestraEtiquetado)
            .filter(
                MuestraEtiquetado.aplicacion_id == aplicacion_id,
                MuestraEtiquetado.frase_numero == frase_numero,
            )
            .first()
        )

        fila = (
            db.query(EtiquetaFrase)
            .filter(
                EtiquetaFrase.aplicacion_id == aplicacion_id,
                EtiquetaFrase.frase_numero == frase_numero,
                EtiquetaFrase.evaluador_id == evaluador_id,
            )
            .first()
        )
        if fila is None:
            fila = EtiquetaFrase(
                aplicacion_id=aplicacion_id,
                frase_numero=frase_numero,
                evaluador_id=evaluador_id,
            )
            db.add(fila)

        fila.texto_estimulo = f["estimulo"]
        fila.texto_respuesta = f["respuesta"]
        fila.ideacion_presente = bool(ideacion_presente)
        fila.sufrimiento_grave = bool(sufrimiento_grave)
        fila.categoria = categoria
        fila.confianza = confianza
        fila.comentario = (comentario or "").strip() or None
        fila.segundos = segundos
        fila.es_muestra_metrica = m is not None
        fila.estrato = m.estrato if m else None
        fila.peso = m.peso if m else None
        # Congelado: lo que el modelo decía al momento de etiquetar.
        fila.modelo_crisis = f["crisis"]
        fila.modelo_dominante = f["dominante"]
        fila.modelo_scores_json = json.dumps(f["scores"], ensure_ascii=False)

        db.commit()
        db.refresh(fila)
        return {"id": fila.id, "guardada": True, "es_muestra_metrica": fila.es_muestra_metrica}

    # ══════════════════════════════════════════════════════════════════
    # Cola de casos (ciega)
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def siguiente_caso(
        db: Session, evaluador_id: str, solo_con_svm: bool = False
    ) -> dict | None:
        """
        Próximo cuestionario sin etiquetar, con las respuestas crudas y sin
        ningún cálculo del sistema.

        `solo_con_svm=True` restringe a las aplicaciones donde el SVM opinó
        (las que incluyen DASS-21). Es el subconjunto que rompe la
        circularidad de su validación, así que conviene empezar por ahí.
        """
        from app.services.cuestionario_service import CuestionarioService

        etiquetados = {
            r[0] for r in db.query(EtiquetaCaso.aplicacion_id)
            .filter(EtiquetaCaso.evaluador_id == evaluador_id).all()
        }

        q = db.query(AplicacionCuestionario).filter(
            AplicacionCuestionario.resultado_json.isnot(None)
        )
        desde = corte_desde(db)
        if desde:
            q = q.filter(
                AplicacionCuestionario.completada_at
                >= datetime.strptime(desde, "%Y-%m-%d")
            )
        candidatas = q.order_by(AplicacionCuestionario.id).all()

        pendientes = []
        for a in candidatas:
            if a.id in etiquetados:
                continue
            if solo_con_svm:
                try:
                    tiene_svm = bool(
                        json.loads(a.resultado_json).get("svm_segunda_opinion")
                    )
                except (ValueError, TypeError):
                    tiene_svm = False
                if not tiene_svm:
                    continue
            pendientes.append(a)

        total = len([
            a for a in candidatas
            if not solo_con_svm or EtiquetadoService._tiene_svm(a)
        ])
        if not pendientes:
            return None

        # Orden determinista y compartido entre evaluadores — mezclado para
        # que la secuencia no insinúe nada, pero igual para los dos para que
        # el acuerdo inter-evaluador se pueda calcular desde el primer caso.
        pendientes.sort(key=lambda a: hashlib.md5(
            f"{SAL_ORDEN}:{a.id}".encode()
        ).hexdigest())
        apl = pendientes[0]

        datos = EtiquetadoService._render_caso(db, apl)
        datos["progreso"] = {"hechas": total - len(pendientes), "total": total}
        return datos

    @staticmethod
    def _render_caso(db: Session, apl: AplicacionCuestionario) -> dict:
        """
        Las respuestas crudas de una aplicación, sin ningún cálculo.

        Lo usan la cola secuencial y la vista de un caso puntual, así que las
        dos muestran exactamente lo mismo.
        """
        from app.services.cuestionario_service import CuestionarioService

        plantilla = (
            db.query(PlantillaCuestionario)
            .filter(PlantillaCuestionario.id == apl.plantilla_id)
            .first()
        )
        preguntas = CuestionarioService.render_preguntas(db, plantilla)
        respuestas = {
            r.origen: r
            for r in db.query(RespuestaAplicacion)
            .filter(RespuestaAplicacion.aplicacion_id == apl.id)
            .all()
        }

        items = []
        for p in preguntas:
            r = respuestas.get(p["origen"])
            if r is None:
                continue
            if p["tipo"] == "texto":
                texto = (r.valor_texto or "").strip()
                if not texto:
                    continue
                items.append({
                    "bloque": p["bloque_nombre"],
                    "tipo": "texto",
                    "pregunta": p["texto"],
                    "respuesta_texto": texto,
                })
            else:
                if r.valor_num is None:
                    continue
                items.append({
                    "bloque": p["bloque_nombre"],
                    "tipo": p["tipo"],
                    "pregunta": p["texto"],
                    "valor": int(r.valor_num),
                    "likert_min": p["likert_min"],
                    "likert_max": p["likert_max"],
                })

        alumno = db.query(User).filter(User.id == apl.estudiante_id).first()
        return {
            "aplicacion_id": apl.id,
            "codigo": f"CASO-{apl.id:03d}",
            "codigo_alumno": getattr(alumno, "codigo_acceso", None) if alumno else None,
            "nombre": f"{alumno.nombre} {alumno.apellido}".strip() if alumno else None,
            "grado": getattr(alumno, "grado", None) if alumno else None,
            "completada_at": apl.completada_at.isoformat() if apl.completada_at else None,
            "instrumentos": sorted({
                i["bloque"] for i in items if i["tipo"] != "texto"
            }),
            "items": items,
        }

    @staticmethod
    def _tiene_svm(apl: AplicacionCuestionario) -> bool:
        try:
            return bool(json.loads(apl.resultado_json).get("svm_segunda_opinion"))
        except (ValueError, TypeError):
            return False

    @staticmethod
    def estudiantes_de_la_cohorte(db: Session, evaluador_id: str) -> dict:
        """
        Los alumnos de la cohorte vigente, con el estado de etiquetado de
        ESTE evaluador.

        No filtra por `psicologo_id` a propósito. El listado normal del panel
        clínico sí lo hace, y por eso una cuenta de evaluador recién creada
        aparecía sin ningún alumno: no es la psicóloga titular de nadie. La
        alternativa —reasignarle los alumnos— los sacaría del panel de quien
        sí los atiende, que es peor.

        No incluye el riesgo que calculó el sistema: la idea es que la
        psicóloga abra el caso sin saber de antemano qué dijo el modelo.
        """
        desde = corte_desde(db)
        q = (
            db.query(AplicacionCuestionario)
            .filter(AplicacionCuestionario.resultado_json.isnot(None))
        )
        if desde:
            q = q.filter(
                AplicacionCuestionario.completada_at
                >= datetime.strptime(desde, "%Y-%m-%d")
            )
        aplicaciones = q.order_by(
            AplicacionCuestionario.completada_at.desc()
        ).all()
        if not aplicaciones:
            return {"corte_desde": desde, "total": 0, "etiquetados": 0,
                    "estudiantes": []}

        alumnos = {
            u.id: u for u in db.query(User)
            .filter(User.id.in_({a.estudiante_id for a in aplicaciones})).all()
        }
        mias = {
            e.aplicacion_id: e for e in db.query(EtiquetaCaso)
            .filter(EtiquetaCaso.evaluador_id == evaluador_id).all()
        }
        prueba = ids_evaluadores_prueba(db)
        # Cuántos evaluadores reales ya juzgaron cada caso — sin decir QUÉ
        # juzgaron, que sería la fuga que ya cerramos.
        otros: dict[int, int] = {}
        for e in db.query(EtiquetaCaso).all():
            if e.evaluador_id == evaluador_id or e.evaluador_id in prueba:
                continue
            otros[e.aplicacion_id] = otros.get(e.aplicacion_id, 0) + 1

        filas = []
        for a in aplicaciones:
            al = alumnos.get(a.estudiante_id)
            mi = mias.get(a.id)
            filas.append({
                "aplicacion_id": a.id,
                "codigo": f"CASO-{a.id:03d}",
                "codigo_alumno": getattr(al, "codigo_acceso", None) if al else None,
                "nombre": f"{al.nombre} {al.apellido}".strip() if al else "(alumno borrado)",
                "grado": getattr(al, "grado", None) if al else None,
                "completada_at": a.completada_at.isoformat() if a.completada_at else None,
                "mi_etiqueta": (
                    {
                        "riesgo_clinico": mi.riesgo_clinico,
                        "requiere_derivacion": bool(mi.requiere_derivacion),
                        "predominante": mi.predominante,
                        "actualizada_at": (
                            mi.updated_at.isoformat() if mi.updated_at else None
                        ),
                    }
                    if mi else None
                ),
                "otros_evaluadores": otros.get(a.id, 0),
            })

        return {
            "corte_desde": desde,
            "total": len(filas),
            "etiquetados": sum(1 for f in filas if f["mi_etiqueta"]),
            "estudiantes": filas,
        }

    @staticmethod
    def caso_por_id(
        db: Session, evaluador_id: str, aplicacion_id: int
    ) -> dict:
        """
        Un caso concreto, ciego, más mi etiqueta si ya lo juzgué.

        Si ya hay etiqueta propia se adjunta `analisis_sistema`: una vez
        emitido el juicio ya no hay nada que contaminar, y es justo lo que la
        psicóloga quiere ver para comparar.
        """
        apl = (
            db.query(AplicacionCuestionario)
            .filter(AplicacionCuestionario.id == aplicacion_id)
            .first()
        )
        if apl is None or not apl.resultado_json:
            raise ValueError(f"La aplicación #{aplicacion_id} no está evaluada.")

        desde = corte_desde(db)
        if desde and apl.completada_at and apl.completada_at < datetime.strptime(
            desde, "%Y-%m-%d"
        ):
            raise ValueError(
                f"La aplicación #{aplicacion_id} es de una cohorte anterior al "
                f"corte vigente ({desde}). Queda como registro, no se etiqueta."
            )

        datos = EtiquetadoService._render_caso(db, apl)

        mi = (
            db.query(EtiquetaCaso)
            .filter(
                EtiquetaCaso.aplicacion_id == aplicacion_id,
                EtiquetaCaso.evaluador_id == evaluador_id,
            )
            .first()
        )
        datos["mi_etiqueta"] = (
            {
                "riesgo_clinico": mi.riesgo_clinico,
                "requiere_derivacion": bool(mi.requiere_derivacion),
                "ideacion_presente": mi.ideacion_presente,
                "predominante": mi.predominante,
                "confianza": mi.confianza,
                "comentario": mi.comentario,
                "actualizada_at": mi.updated_at.isoformat() if mi.updated_at else None,
            }
            if mi else None
        )
        datos["analisis_sistema"] = (
            EtiquetadoService.analisis_sistema(apl) if mi else None
        )
        return datos

    @staticmethod
    def analisis_sistema(apl: AplicacionCuestionario) -> dict | None:
        """
        Lo que calculó el sistema, para mostrarlo DESPUÉS del juicio humano.

        Se entrega solo cuando ya hay etiqueta propia. Antes de eso el
        endpoint devuelve None — si viajara en el payload se vería abriendo el
        inspector, y la concordancia dejaría de medir concordancia.
        """
        try:
            r = json.loads(apl.resultado_json or "{}")
        except (ValueError, TypeError):
            return None
        frases = r.get("frases") or []
        svm = r.get("svm_segunda_opinion")
        return {
            "riesgo_global": r.get("riesgo_global"),
            "crisis_activada": bool(r.get("crisis_activada")),
            "n_senales": r.get("n_senales"),
            "bloques": [
                {
                    "codigo": b.get("codigo"),
                    "nombre": b.get("nombre"),
                    "puntaje": b.get("puntaje"),
                    "rango_max": b.get("rango_max"),
                    "severidad": b.get("severidad"),
                    "severidad_alerta": bool(b.get("severidad_alerta")),
                    "bandera_crisis": bool(b.get("bandera_crisis")),
                }
                for b in (r.get("bloques") or [])
            ],
            "frases": [
                {
                    "pregunta": f.get("pregunta"),
                    "respuesta": f.get("respuesta"),
                    "dominante": f.get("dominante"),
                    "crisis": bool(f.get("crisis")),
                    "score_depresion": (f.get("scores") or {}).get("depresion"),
                }
                for f in frases
            ],
            "n_frases": len(frases),
            "n_frases_crisis": sum(1 for f in frases if f.get("crisis")),
            "svm": svm,
        }

    @staticmethod
    def guardar_etiqueta_caso(
        db: Session,
        evaluador_id: str,
        aplicacion_id: int,
        riesgo_clinico: str,
        requiere_derivacion: bool = False,
        ideacion_presente: bool | None = None,
        predominante: str | None = None,
        confianza: str = "alta",
        comentario: str | None = None,
        segundos: int | None = None,
    ) -> dict:
        if predominante and predominante not in PREDOMINANTES:
            raise ValueError(
                f"Predominante '{predominante}' inválido. Usá una de: "
                f"{', '.join(PREDOMINANTES)}."
            )
        if riesgo_clinico not in RIESGOS:
            raise ValueError(
                f"Riesgo '{riesgo_clinico}' inválido. Usá: {', '.join(RIESGOS)}."
            )
        if confianza not in CONFIANZAS:
            raise ValueError(
                f"Confianza '{confianza}' inválida. Usá: {', '.join(CONFIANZAS)}."
            )

        apl = (
            db.query(AplicacionCuestionario)
            .filter(AplicacionCuestionario.id == aplicacion_id)
            .first()
        )
        if apl is None or not apl.resultado_json:
            raise ValueError(f"La aplicación #{aplicacion_id} no está evaluada.")

        try:
            resultado = json.loads(apl.resultado_json)
        except (ValueError, TypeError):
            resultado = {}
        svm = resultado.get("svm_segunda_opinion") or {}

        fila = (
            db.query(EtiquetaCaso)
            .filter(
                EtiquetaCaso.aplicacion_id == aplicacion_id,
                EtiquetaCaso.evaluador_id == evaluador_id,
            )
            .first()
        )
        if fila is None:
            fila = EtiquetaCaso(
                aplicacion_id=aplicacion_id, evaluador_id=evaluador_id
            )
            db.add(fila)

        fila.riesgo_clinico = riesgo_clinico
        fila.requiere_derivacion = bool(requiere_derivacion)
        fila.ideacion_presente = ideacion_presente
        fila.predominante = predominante
        fila.confianza = confianza
        fila.comentario = (comentario or "").strip() or None
        fila.segundos = segundos
        fila.modelo_riesgo = resultado.get("riesgo_global")
        fila.modelo_crisis = bool(resultado.get("crisis_activada"))
        fila.modelo_svm_clase = svm.get("clase")
        fila.modelo_svm_prob = svm.get("probabilidad")

        db.commit()
        db.refresh(fila)
        return {
            "id": fila.id,
            "guardada": True,
            # Recién acá se devuelve lo que calculó el sistema: el juicio ya
            # está emitido y guardado, así que mostrarlo no lo contamina.
            "analisis_sistema": EtiquetadoService.analisis_sistema(apl),
        }

    # ══════════════════════════════════════════════════════════════════
    # Progreso
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def progreso(db: Session, evaluador_id: str) -> dict:
        corpus = EtiquetadoService.corpus_frases(db)
        n_plan = db.query(MuestraEtiquetado).count()

        mis_frases = (
            db.query(EtiquetaFrase)
            .filter(EtiquetaFrase.evaluador_id == evaluador_id)
            .all()
        )
        mis_muestra = [e for e in mis_frases if e.es_muestra_metrica]

        desde = corte_desde(db)
        q_casos = db.query(AplicacionCuestionario).filter(
            AplicacionCuestionario.resultado_json.isnot(None)
        )
        if desde:
            q_casos = q_casos.filter(
                AplicacionCuestionario.completada_at
                >= datetime.strptime(desde, "%Y-%m-%d")
            )
        n_casos_total = q_casos.count()
        mis_casos = (
            db.query(EtiquetaCaso)
            .filter(EtiquetaCaso.evaluador_id == evaluador_id)
            .count()
        )

        return {
            "frases": {
                "muestra_hechas": len(mis_muestra),
                "muestra_total": n_plan,
                "corpus_hechas": len(mis_frases) - len(mis_muestra),
                "corpus_total": max(0, len(corpus) - n_plan),
                "ideacion_marcadas": sum(1 for e in mis_frases if e.ideacion_presente),
            },
            "casos": {"hechas": mis_casos, "total": n_casos_total},
            # El SVM solo opina si la plantilla trae DASS-21 **y** el .joblib
            # está en el servidor. En producción no se cumple ninguna de las
            # dos, así que el filtro "solo con SVM" dejaría la cola vacía.
            "svm_instalado": _svm_instalado(),
            # Qué cohorte se está etiquetando. Si es None, entra todo.
            "corte_desde": desde,
            # Para que la pantalla avise que las etiquetas no van a contar.
            "es_cuenta_prueba": evaluador_id in ids_evaluadores_prueba(db),
            "evaluadores_activos": len({
                f[0] for f in db.query(EtiquetaFrase.evaluador_id).distinct().all()
            } - ids_evaluadores_prueba(db)),
            "muestra_generada": n_plan > 0,
        }

    # ══════════════════════════════════════════════════════════════════
    # Dataset para reentrenar
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def dataset_frases(db: Session) -> list[dict]:
        """
        Todas las etiquetas de frases, en formato plano, listas para entrenar.

        Incluye el texto, la etiqueta humana y los scores que el modelo
        vigente había dado. Con eso se puede (a) recalibrar el umbral,
        (b) entrenar un clasificador liviano sobre los 4 scores, o
        (c) hacer fine-tuning si algún día hay volumen suficiente.
        """
        filas = (
            db.query(EtiquetaFrase)
            .order_by(EtiquetaFrase.aplicacion_id, EtiquetaFrase.frase_numero)
            .all()
        )
        # No se filtran: se marcan. Quien entrene decide si las usa, pero la
        # columna evita que entren sin que nadie lo note.
        prueba = ids_evaluadores_prueba(db)
        out = []
        for e in filas:
            try:
                scores = json.loads(e.modelo_scores_json or "{}")
            except (ValueError, TypeError):
                scores = {}
            out.append({
                "aplicacion_id": e.aplicacion_id,
                "frase_numero": e.frase_numero,
                "evaluador_id": e.evaluador_id,
                "es_cuenta_prueba": int(e.evaluador_id in prueba),
                "estimulo": e.texto_estimulo,
                "respuesta": e.texto_respuesta,
                # La frase completa es la unidad clínica. Ojo: en producción
                # BETO puntúa solo `respuesta` — ver nota en el reporte.
                "texto_completo": f"{e.texto_estimulo} {e.texto_respuesta}".strip(),
                "y_ideacion": int(e.ideacion_presente),
                "y_sufrimiento_grave": int(e.sufrimiento_grave),
                "y_categoria": e.categoria,
                "confianza": e.confianza,
                "es_muestra_metrica": int(e.es_muestra_metrica),
                "estrato": e.estrato,
                "peso": e.peso,
                "modelo_crisis": int(e.modelo_crisis) if e.modelo_crisis is not None else None,
                "modelo_dominante": e.modelo_dominante,
                "score_depresion": scores.get("depresion"),
                "score_ansiedad": scores.get("ansiedad"),
                "score_adaptativo": scores.get("adaptativo"),
                "score_neutral": scores.get("neutral"),
                "etiquetada_at": e.created_at.isoformat() if e.created_at else None,
            })
        return out

    @staticmethod
    def dataset_casos(db: Session) -> list[dict]:
        filas = (
            db.query(EtiquetaCaso).order_by(EtiquetaCaso.aplicacion_id).all()
        )
        return [
            {
                "aplicacion_id": e.aplicacion_id,
                "evaluador_id": e.evaluador_id,
                "y_riesgo": e.riesgo_clinico,
                "y_derivacion": int(e.requiere_derivacion),
                "y_ideacion": (
                    int(e.ideacion_presente) if e.ideacion_presente is not None else None
                ),
                "y_predominante": e.predominante,
                "confianza": e.confianza,
                "modelo_riesgo": e.modelo_riesgo,
                "modelo_crisis": int(e.modelo_crisis) if e.modelo_crisis is not None else None,
                "modelo_svm_clase": e.modelo_svm_clase,
                "modelo_svm_prob": e.modelo_svm_prob,
                "comentario": e.comentario,
                "etiquetada_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in filas
        ]
