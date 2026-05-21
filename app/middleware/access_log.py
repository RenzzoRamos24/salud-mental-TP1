"""
Middleware de auditoría: registra cada llamada a /api/v1 en access_logs (HU-22).
Extrae usuario del JWT si está presente; no bloquea la respuesta ante errores.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class AccessLogMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        # Solo loguear endpoints de la API
        if not request.url.path.startswith("/api/v1"):
            return await call_next(request)

        response = await call_next(request)

        try:
            user_id, email, role = None, None, None
            auth = request.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                from app.core.security import decodificar_token
                from app.database import SessionLocal
                from app.models.user import User
                payload = decodificar_token(auth[7:])
                uid = payload.get("sub")
                if uid:
                    db = SessionLocal()
                    user = db.query(User).filter(User.id == uid).first()
                    if user:
                        user_id, email, role = user.id, user.email, user.role
                    db.close()
        except Exception:
            pass

        try:
            from app.database import SessionLocal
            from app.models.access_log import AccessLog
            db = SessionLocal()
            db.add(AccessLog(
                user_id=user_id,
                email=email,
                role=role,
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                ip=request.client.host if request.client else None,
            ))
            db.commit()
            db.close()
        except Exception:
            pass

        return response
