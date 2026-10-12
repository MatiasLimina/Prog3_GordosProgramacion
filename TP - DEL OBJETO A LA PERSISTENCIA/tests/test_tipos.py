import pytest
from pydantic import BaseModel, ValidationError

from app.core.tipos import INT32_MAX, IdDto, StockDto


class Dto(BaseModel):
    id: IdDto
    stock: StockDto = 0


@pytest.mark.parametrize("valor", [1, 100, INT32_MAX])
def test_id_valido(valor):
    assert Dto(id=valor).id == valor


@pytest.mark.parametrize("valor", [0, -1, INT32_MAX + 1, 99_999_999_999])
def test_id_invalido(valor):
    with pytest.raises(ValidationError):
        Dto(id=valor)


@pytest.mark.parametrize("valor", [0, 5, INT32_MAX])
def test_stock_valido(valor):
    assert Dto(id=1, stock=valor).stock == valor


@pytest.mark.parametrize("valor", [-1, INT32_MAX + 1])
def test_stock_invalido(valor):
    with pytest.raises(ValidationError):
        Dto(id=1, stock=valor)
