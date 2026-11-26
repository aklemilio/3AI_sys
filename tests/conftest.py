import json
from pathlib import Path

import pytest

CASO = Path(__file__).resolve().parent.parent / "fixtures" / "caso-libanes-c4"
ETAPAS_C4 = ["find", "record_or_rescue", "preserve", "describe", "access", "keep_alive", "transmit"]


@pytest.fixture(autouse=True)
def sin_red(monkeypatch):
    """Las pruebas nunca descargan nada: toda fuente queda «inaccesible» salvo que
    una prueba sustituya ``descargar`` por su propia página falsa."""
    from tresia.calculo import fuentes

    def descargar(url):
        raise OSError("sin red en las pruebas")

    monkeypatch.setattr(fuentes, "descargar", descargar)


def cargar(nombre: str):
    return json.loads((CASO / nombre).read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def grupos():
    return cargar("grupos_c4.json")


@pytest.fixture(scope="session")
def exploradores():
    return {e: cargar(f"{e}.json") for e in ("E1", "E2", "E3")}


@pytest.fixture(scope="session")
def cribas():
    return {s: cargar(f"{s}.json") for s in ("S1", "S2", "S3")}


@pytest.fixture(scope="session")
def ranking_esperado():
    return cargar("ranking_c4.json")
