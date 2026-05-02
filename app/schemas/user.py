from pydantic import BaseModel, Field


class UpdateProfileRequest(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    apellido: str = Field(..., min_length=1, max_length=100)


class ChangePasswordRequest(BaseModel):
    password_actual: str = Field(..., min_length=1)
    nueva_password: str = Field(..., min_length=8, max_length=72)


class DeleteAccountRequest(BaseModel):
    password: str = Field(..., min_length=1, description="Contraseña para confirmar")
    confirmacion: str = Field(..., description='Debe ser "ELIMINAR"')
