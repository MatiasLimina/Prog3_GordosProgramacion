from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator

ROLES_PERMITIDOS = {"autor", "coautor", "traductor", "ilustrador"}


class LibroAutorCreate(BaseModel):
    autor_id: int = Field(gt=0, description="ID del autor existente")
    rol: str = Field(min_length=1, max_length=50, description="Rol del autor en el libro")
    orden: int = Field(ge=1, description="Orden de aparición (>= 1)")

    @field_validator("rol")
    @classmethod
    def validar_rol(cls, valor: str) -> str:
        rol_normalizado = valor.strip().lower()
        if rol_normalizado not in ROLES_PERMITIDOS:
            raise ValueError(
                f"El rol '{valor}' no es válido. Roles permitidos: {', '.join(sorted(ROLES_PERMITIDOS))}."
            )
        return rol_normalizado


class LibroCreate(BaseModel):
    isbn: str = Field(min_length=1, max_length=30)
    titulo: str = Field(min_length=1, max_length=255)
    precio: Decimal = Field(
        gt=Decimal(0),
        max_digits=10,
        decimal_places=2,  # coincide con Numeric(10,2): evita overflow (500) y redondeo silencioso
        description="El precio debe ser mayor a 0 (RN-03)",
    )
    stock: int = Field(default=0, ge=0, description="El stock no puede ser negativo (RN-03)")
    editorial_id: int = Field(gt=0)
    genero_id: int | None = Field(default=None)
    autores: list[LibroAutorCreate] = Field(default_factory=list)

    @field_validator("isbn", "titulo")
    @classmethod
    def no_vacio(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("No puede estar vacío.")
        return valor


class LibroUpdate(BaseModel):
    isbn: str | None = Field(default=None, min_length=1, max_length=30)
    titulo: str | None = Field(default=None, min_length=1, max_length=255)
    precio: Decimal | None = Field(default=None, gt=Decimal(0), max_digits=10, decimal_places=2)
    stock: int | None = Field(default=None, ge=0)
    editorial_id: int | None = Field(default=None, gt=0)
    genero_id: int | None = Field(default=None)

    @field_validator("isbn", "titulo", "precio", "stock", "editorial_id", mode="before")
    @classmethod
    def no_null(cls, valor):
        if valor is None:
            raise ValueError("No puede ser null; omití el campo para no modificarlo.")
        return valor


class EditorialSimpleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    pais: str


class GeneroSimpleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class AutorEnLibroRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    autor_id: int
    nombre: str
    nacionalidad: str
    rol: str
    orden: int


class LibroRead(BaseModel):
    """Representación de libro con editorial y género (usada en listados)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    isbn: str
    titulo: str
    precio: Decimal
    stock: int
    editorial: EditorialSimpleRead
    genero: GeneroSimpleRead | None = None


class LibroDetalleRead(LibroRead):
    """Representación completa de libro con editorial, género y autores (usada en detalle, alta y patch)."""
    autores: list[AutorEnLibroRead] = Field(default_factory=list)
