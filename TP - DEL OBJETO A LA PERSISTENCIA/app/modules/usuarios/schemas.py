"""Contratos de entrada y salida para autenticación y usuarios."""
from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, field_validator


_ROLES = Literal["ADMIN", "VENDEDOR", "CLIENTE"]


def _validar_password(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("La contraseña no puede superar los 72 bytes.")
    return password


Password = Annotated[str, AfterValidator(_validar_password)]


class _Entrada(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RegistroCreate(_Entrada):
    email: EmailStr = Field(max_length=255)
    nombre: str = Field(min_length=1, max_length=150)
    password: Password

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("El nombre no puede estar vacío.")
        return valor


class LoginCreate(_Entrada):
    email: EmailStr = Field(max_length=255)
    password: Password


class CambioPasswordCreate(_Entrada):
    password_actual: Password
    password_nueva: Password


class UsuarioCreate(_Entrada):
    email: EmailStr = Field(max_length=255)
    nombre: str = Field(min_length=1, max_length=150)
    password: Password

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("El nombre no puede estar vacío.")
        return valor


class AsignacionRolCreate(_Entrada):
    rol: _ROLES
    vence_en: datetime | None = None

    @field_validator("vence_en")
    @classmethod
    def vence_en_con_zona_y_futuro(cls, valor: datetime | None) -> datetime | None:
        if valor is None:
            return valor
        if valor.tzinfo is None or valor.utcoffset() is None:
            raise ValueError("La fecha de vencimiento debe incluir zona horaria.")
        if valor <= datetime.now(timezone.utc):
            raise ValueError("La fecha de vencimiento debe estar en el futuro.")
        return valor


class UsuarioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    nombre: str
    activo: bool
    debe_cambiar_password: bool


class AsignacionRolRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    rol: _ROLES
    desde: datetime
    vence_en: datetime | None = None
    revocada_en: datetime | None = None
    otorgada_por: int | None = None


class LoginRead(BaseModel):
    mensaje: str
    debe_cambiar_password: bool
    expira_en_segundos: int


class AuthYoRead(BaseModel):
    usuario: UsuarioRead
    roles_vigentes: list[_ROLES]
    roles_token: list[_ROLES]
