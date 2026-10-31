import pytest

from econpulse.registry import Indicator, load_registry, validate


def make(**overrides):
    base = dict(id="x", label="X", label_es="X", section="gdp", source="ine", key="K", freq="M", unit="%")
    return Indicator(**{**base, **overrides})


def test_shipped_registry_is_valid():
    indicators = load_registry()
    assert len(indicators) >= 20
    tiles = sorted(i.tile for i in indicators if i.tile)
    assert tiles == list(range(1, len(tiles) + 1)), "tile positions should run 1..n without gaps"


def test_duplicate_ids_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        validate([make(), make()])


def test_unknown_fields_rejected():
    with pytest.raises(ValueError) as err:
        validate([make(source="nope", freq="W", section="misc", transforms=("bogus",))])
    message = str(err.value)
    for fragment in ("unknown source", "unknown freq", "unknown section", "unknown transform"):
        assert fragment in message


def test_derived_inputs_must_come_first():
    spread = make(id="spread", source="derived", key="subtract", params={"a": "es", "b": "de"})
    with pytest.raises(ValueError, match="defined earlier"):
        validate([spread, make(id="es"), make(id="de")])
    validate([make(id="es"), make(id="de"), spread])  # correct order passes


def test_duplicate_tile_rejected():
    with pytest.raises(ValueError, match="tile 1"):
        validate([make(id="a", tile=1), make(id="b", tile=1)])
