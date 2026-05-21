from sqlalchemy.orm import Session
from app.models.session import UserSession
from app.models.response import UserResponse
from app.models.risk import RiskResult
from app.services.session_service import SessionService
from app.services.nlp_service import NLPService
from app.services.ai_provider import get_ai_provider
from app.config import settings
import logging
import random
from datetime import datetime

logger = logging.getLogger(__name__)


class ChatService:
    """
    Orquesta el flujo conversacional del chatbot. Delega TODA la lógica de IA
    al `AIProvider` activo (BERT hoy, Claude/OpenAI mañana). Etapas:

        1. apertura  → bot saluda con prompt abierto.
                       Usuario responde libre.
                       Provider hace triage y decide orden PHQ-9/GAD-7.
        2. evaluación → 16 ítems clínicos en el orden decidido.
                        Cada ítem se puntúa 0-3 (Likert) por el provider.
        3. completada → cálculo PHQ-9 total / GAD-7 total / severidades /
                        protocolo de crisis si PHQ-9 ítem 9 ≥ 1.
    """

    # ─────────────────────────────────────────────────────────────────
    # SESIÓN — empieza en fase APERTURA
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def crear_sesion(db: Session, user_id: str, nombre: str) -> dict:
        try:
            logger.info(f"📋 Creando sesión para usuario: {user_id}")
            user_session = SessionService.crear_sesion(db=db, user_id=user_id, nombre=nombre)
            total = len(SessionService.PREGUNTAS)
            logger.info(f"✅ Sesión creada en fase=apertura: {user_session.id}")

            primer_nombre = (nombre or "").split(" ")[0] if nombre else ""
            nombre_coma_espacio = (", " + primer_nombre) if primer_nombre else ""

            # HU-39: saludo personalizable por el admin.
            from app.services.admin_service import AdminService
            msgs = AdminService.get_chatbot_messages(db)
            plantilla = msgs.get("saludo_inicial") or AdminService.DEFAULT_CHATBOT_MSGS["saludo_inicial"]
            try:
                saludo = plantilla.format(
                    nombre=primer_nombre,
                    nombre_coma_espacio=nombre_coma_espacio,
                )
            except (KeyError, IndexError):
                # Si el admin metió placeholders raros, caemos al default.
                saludo = AdminService.DEFAULT_CHATBOT_MSGS["saludo_inicial"].format(
                    nombre=primer_nombre,
                    nombre_coma_espacio=nombre_coma_espacio,
                )
            return {
                "session_id": user_session.id,
                "fase": "apertura",
                "pregunta_numero": 0,
                "pregunta": None,
                "item_codigo": None,
                "modulo": None,
                "criterio_dsm5": None,
                "opciones_likert": settings.OPCIONES_LIKERT,
                "total_preguntas": total,
                "mensaje": saludo,
            }
        except Exception as e:
            logger.error(f"❌ Error creando sesión: {e}")
            db.rollback()
            raise

    # ─────────────────────────────────────────────────────────────────
    # AVANZAR — disambigúa por fase
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def guardar_respuesta_y_avanzar(
        db: Session,
        session_id: str,
        respuesta: str,
        score_likert: int = None,
    ) -> dict:
        try:
            user_session = SessionService.obtener_sesion(db, session_id)
            if not user_session:
                raise ValueError(f"Sesión no encontrada: {session_id}")

            if user_session.fase == "apertura":
                return ChatService._procesar_apertura(db, user_session, respuesta)

            if SessionService.es_sesion_completa(user_session.pregunta_actual):
                raise ValueError("Esta sesión ya ha sido completada")

            return ChatService._procesar_evaluacion(
                db=db,
                user_session=user_session,
                respuesta=respuesta,
                score_likert=score_likert,
            )
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"❌ Error procesando respuesta: {e}")
            db.rollback()
            raise

    # ─────────────────────────────────────────────────────────────────
    # FASE 1 — APERTURA
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _procesar_apertura(db: Session, user_session: UserSession, respuesta: str) -> dict:
        """Recibe el relato libre del usuario y arranca la evaluación."""
        if not respuesta or not respuesta.strip():
            raise ValueError("Cuéntame algo aunque sea breve para empezar.")

        provider = get_ai_provider()
        logger.info(f"🧭 Triage de apertura (provider={provider.name})")
        triage = provider.triage_apertura(respuesta, nombre=user_session.nombre)

        modulos_orden = ",".join(triage["modulos_orden"])
        SessionService.actualizar_fase(
            db=db,
            session_id=user_session.id,
            fase="evaluacion",
            modulos_orden=modulos_orden,
            apertura_texto=respuesta.strip(),
        )
        # recarga
        user_session = SessionService.obtener_sesion(db, user_session.id)
        primer_item = SessionService.obtener_item_para_sesion(user_session, 0)
        total = len(SessionService.PREGUNTAS)

        return {
            "completado": False,
            "requiere_seleccion": False,
            "fase": "evaluacion",
            "pregunta_numero": 1,
            "pregunta": primer_item["texto"],
            "item_codigo": primer_item["id"],
            "modulo": primer_item["modulo"],
            "criterio_dsm5": primer_item["criterio_dsm5"],
            "opciones_likert": settings.OPCIONES_LIKERT,
            "mensaje": triage["acuse"],
            "modulos_orden": triage["modulos_orden"],
            "modulo_prioritario": triage["modulo_prioritario"],
            "condiciones_detectadas": triage["condiciones_detectadas"],
            "crisis_inmediata": triage["crisis_inmediata"],
            "total_preguntas": total,
            "progreso": f"0/{total}",
        }

    # ─────────────────────────────────────────────────────────────────
    # FASE 2 — EVALUACIÓN (texto libre + Likert 0-3)
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _procesar_evaluacion(
        db: Session,
        user_session: UserSession,
        respuesta: str,
        score_likert: int = None,
    ) -> dict:
        idx = user_session.pregunta_actual
        item = SessionService.obtener_item_para_sesion(user_session, idx)
        if item is None:
            raise ValueError(f"Ítem inexistente en posición {idx}")

        total = len(SessionService.PREGUNTAS)
        provider = get_ai_provider()

        # ── A) Botón pulsado: score manual ────────────────────────────
        if score_likert is not None:
            if not (0 <= int(score_likert) <= 3):
                raise ValueError("score_likert debe estar entre 0 y 3")
            SessionService.guardar_respuesta(
                db=db,
                session_id=user_session.id,
                numero_pregunta=idx,
                pregunta=item["texto"],
                respuesta=respuesta or settings.OPCIONES_LIKERT[int(score_likert)]["etiqueta"],
                item=item,
                score_likert=int(score_likert),
                confianza_likert=None,
                score_origen="manual",
            )
            return ChatService._avanzar(db, user_session, idx, total, provider)

        # ── B) Texto libre: provider propone score ────────────────────
        propuesta = provider.score_likert(respuesta, item)
        if propuesta["requiere_seleccion"]:
            logger.info(
                f"   ↩️  Devolviendo botones Likert (conf "
                f"{propuesta['confianza']*100:.1f}% < umbral)"
            )
            return {
                "completado": False,
                "requiere_seleccion": True,
                "fase": "evaluacion",
                "pregunta_numero": idx + 1,
                "pregunta": item["texto"],
                "item_codigo": item["id"],
                "modulo": item["modulo"],
                "criterio_dsm5": item["criterio_dsm5"],
                "score_propuesto": propuesta["score_propuesto"],
                "confianza": propuesta["confianza"],
                "opciones_likert": settings.OPCIONES_LIKERT,
                "respuesta_usuario": respuesta,
                "mensaje": provider.acuse_aclaracion(),
                "total_preguntas": total,
                "progreso": f"{idx}/{total}",
            }

        SessionService.guardar_respuesta(
            db=db,
            session_id=user_session.id,
            numero_pregunta=idx,
            pregunta=item["texto"],
            respuesta=respuesta,
            item=item,
            score_likert=propuesta["score_propuesto"],
            confianza_likert=propuesta["confianza"],
            score_origen="nlp",
        )
        return ChatService._avanzar(db, user_session, idx, total, provider)

    @staticmethod
    def _avanzar(
        db: Session,
        user_session: UserSession,
        idx_actual: int,
        total: int,
        provider=None,
    ) -> dict:
        siguiente = idx_actual + 1
        SessionService.actualizar_pregunta(db, user_session.id, siguiente)

        if SessionService.es_sesion_completa(siguiente):
            SessionService.finalizar_sesion(db, user_session.id)
            SessionService.actualizar_fase(db, user_session.id, fase="completada")
            logger.info(f"✅ Sesión completada: {user_session.id}")
            return {
                "completado": True,
                "requiere_seleccion": False,
                "fase": "completada",
                "pregunta_numero": siguiente,
                "total_preguntas": total,
                "mensaje": "¡Evaluación completada! Procesando análisis…",
                "siguiente_paso": "Llamar a /api/v1/chatbot/analizar para obtener resultado",
            }

        user_session = SessionService.obtener_sesion(db, user_session.id)
        item_siguiente = SessionService.obtener_item_para_sesion(user_session, siguiente)
        provider = provider or get_ai_provider()
        logger.info(f"✅ Respuesta guardada. Pregunta {siguiente + 1} de {total}")
        return {
            "completado": False,
            "requiere_seleccion": False,
            "fase": "evaluacion",
            "pregunta_numero": siguiente + 1,
            "pregunta": item_siguiente["texto"],
            "item_codigo": item_siguiente["id"],
            "modulo": item_siguiente["modulo"],
            "criterio_dsm5": item_siguiente["criterio_dsm5"],
            "opciones_likert": settings.OPCIONES_LIKERT,
            "mensaje": provider.acuse_continuar(),
            "total_preguntas": total,
            "progreso": f"{siguiente}/{total}",
        }

    # ─────────────────────────────────────────────────────────────────
    # FASE 3 — ANÁLISIS FINAL
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def analizar_sesion(db: Session, session_id: str, user_id: str) -> dict:
        try:
            logger.info(f"🔍 Iniciando análisis de sesión: {session_id}")
            user_session = SessionService.obtener_sesion(db, session_id)
            if not user_session:
                raise ValueError(f"Sesión no encontrada: {session_id}")
            if not SessionService.es_sesion_completa(user_session.pregunta_actual):
                raise ValueError("La sesión debe estar completada para analizar")

            respuestas_lista = SessionService.obtener_todas_respuestas(db, session_id)
            if not respuestas_lista:
                raise ValueError("No hay respuestas para analizar")

            respuestas_dict = [{"respuesta": r["respuesta"]} for r in respuestas_lista]
            logger.info(f"📊 BERT multi-condición sobre {len(respuestas_dict)} respuestas")
            resultado_nlp = NLPService.analizar_respuestas(respuestas_dict)

            ChatService._calcular_scores_por_respuesta(db, session_id)

            puntajes = ChatService._calcular_totales_phq9_gad7(db, session_id)
            logger.info(
                f"   📐 PHQ-9: {puntajes['phq9_total']}/27 ({puntajes['phq9_severidad']})  |  "
                f"GAD-7: {puntajes['gad7_total']}/21 ({puntajes['gad7_severidad']})"
            )
            if puntajes["crisis_protocolo"]:
                logger.warning("   🚨 PROTOCOLO DE EMERGENCIA — PHQ-9 ítem 9 ≥ 1")

            ChatService._guardar_resultado(
                db=db, session_id=session_id, user_id=user_id,
                resultado_nlp=resultado_nlp, puntajes=puntajes,
            )

            return {
                "session_id": session_id,
                "usuario": user_session.nombre,
                "fecha_analisis": datetime.utcnow().isoformat(),
                "respuestas_analizadas": len(respuestas_dict),
                "apertura_texto": user_session.apertura_texto,
                "modulos_orden": (user_session.modulos_orden or "PHQ-9,GAD-7").split(","),
                "phq9": {
                    "total": puntajes["phq9_total"], "max": 27,
                    "severidad": puntajes["phq9_severidad"],
                    "accion": puntajes["phq9_accion"],
                    "items": puntajes["phq9_detalle"],
                },
                "gad7": {
                    "total": puntajes["gad7_total"], "max": 21,
                    "severidad": puntajes["gad7_severidad"],
                    "accion": puntajes["gad7_accion"],
                    "items": puntajes["gad7_detalle"],
                },
                "crisis_protocolo": puntajes["crisis_protocolo"],
                "resultado": {
                    "nivel_riesgo": resultado_nlp["nivel_riesgo"],
                    "condiciones_detectadas": resultado_nlp["condiciones_detectadas"],
                    "scores_completos": resultado_nlp["scores_completos"],
                    "explicacion": resultado_nlp["explicacion"],
                    "modelo": resultado_nlp["modelo"],
                },
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"❌ Error en análisis: {e}")
            db.rollback()
            raise

    # ─────────────────────────────────────────────────────────────────
    # SCORING CLÍNICO
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _calcular_totales_phq9_gad7(db: Session, session_id: str) -> dict:
        respuestas = (
            db.query(UserResponse)
            .filter(UserResponse.session_id == session_id)
            .order_by(UserResponse.numero_pregunta)
            .all()
        )
        phq9_detalle, gad7_detalle = [], []
        phq9_total = gad7_total = 0
        crisis = False
        for r in respuestas:
            score = r.score_likert if r.score_likert is not None else 0
            detalle = {
                "item": r.item_codigo,
                "criterio_dsm5": r.criterio_dsm5,
                "pregunta": r.pregunta,
                "respuesta": r.respuesta,
                "score": score,
                "origen": r.score_origen,
            }
            if r.modulo == "PHQ-9":
                phq9_total += score
                phq9_detalle.append(detalle)
                if r.item_codigo == "phq9_9" and score >= 1:
                    crisis = True
            elif r.modulo == "GAD-7":
                gad7_total += score
                gad7_detalle.append(detalle)
        phq9_sev = ChatService._severidad(phq9_total, settings.PHQ9_SEVERIDAD)
        gad7_sev = ChatService._severidad(gad7_total, settings.GAD7_SEVERIDAD)
        return {
            "phq9_total": phq9_total, "gad7_total": gad7_total,
            "phq9_severidad": phq9_sev["nivel"], "gad7_severidad": gad7_sev["nivel"],
            "phq9_accion": phq9_sev["accion"],   "gad7_accion": gad7_sev["accion"],
            "phq9_detalle": phq9_detalle, "gad7_detalle": gad7_detalle,
            "crisis_protocolo": crisis,
        }

    @staticmethod
    def _severidad(total: int, tabla: list) -> dict:
        for rango in tabla:
            if rango["min"] <= total <= rango["max"]:
                return rango
        return tabla[-1]

    @staticmethod
    def _calcular_scores_por_respuesta(db: Session, session_id: str) -> None:
        respuestas = (
            db.query(UserResponse)
            .filter(UserResponse.session_id == session_id)
            .order_by(UserResponse.numero_pregunta)
            .all()
        )
        for r in respuestas:
            try:
                analisis = NLPService.analizar_respuesta_individual(r.respuesta)
                r.score_riesgo = analisis["score"]
                r.nivel_riesgo = analisis["nivel"]
                r.condicion_dominante = analisis["condicion"]
            except Exception as e:
                logger.warning(f"⚠️ No se pudo analizar respuesta {r.id}: {e}")
        db.commit()
        logger.info(f"   📈 Scores BERT por pregunta calculados ({len(respuestas)} respuestas)")

    @staticmethod
    def _guardar_resultado(
        db: Session, session_id: str, user_id: str,
        resultado_nlp: dict, puntajes: dict,
    ) -> RiskResult:
        if resultado_nlp["condiciones_detectadas"]:
            score_principal = max(
                d["confianza"] for d in resultado_nlp["condiciones_detectadas"].values()
            ) / 100.0
        else:
            score_principal = resultado_nlp["scores_completos"].get("estabilidad", 0.0) / 100.0

        nivel = "CRÍTICO" if puntajes["crisis_protocolo"] else resultado_nlp["nivel_riesgo"]

        existente = db.query(RiskResult).filter(RiskResult.session_id == session_id).first()
        if existente:
            existente.nivel_riesgo = nivel
            existente.score = score_principal
            existente.explicacion = resultado_nlp["explicacion"]
            existente.phq9_total = puntajes["phq9_total"]
            existente.gad7_total = puntajes["gad7_total"]
            existente.phq9_severidad = puntajes["phq9_severidad"]
            existente.gad7_severidad = puntajes["gad7_severidad"]
            existente.crisis_protocolo = puntajes["crisis_protocolo"]
            db.commit()
            db.refresh(existente)
            return existente

        risk = RiskResult(
            session_id=session_id, user_id=user_id,
            nivel_riesgo=nivel, score=score_principal,
            explicacion=resultado_nlp["explicacion"],
            phq9_total=puntajes["phq9_total"], gad7_total=puntajes["gad7_total"],
            phq9_severidad=puntajes["phq9_severidad"],
            gad7_severidad=puntajes["gad7_severidad"],
            crisis_protocolo=puntajes["crisis_protocolo"],
        )
        db.add(risk)
        db.commit()
        db.refresh(risk)
        return risk

    # ─────────────────────────────────────────────────────────────────
    # CONVERSACIÓN
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def obtener_conversacion(db: Session, session_id: str) -> dict:
        try:
            user_session = SessionService.obtener_sesion(db, session_id)
            if not user_session:
                raise ValueError(f"Sesión no encontrada: {session_id}")
            conversacion = SessionService.obtener_todas_respuestas(db, session_id)
            return {
                "session_id": session_id,
                "usuario": user_session.nombre,
                "completado": user_session.estado == "completada",
                "conversacion": conversacion,
                "total_respuestas": len(conversacion),
            }
        except Exception as e:
            logger.error(f"❌ Error obteniendo conversación: {e}")
            raise
