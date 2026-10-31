"""The indicator registry: every series the site tracks, defined in indicators.yaml."""

import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import sources, transforms
from .config import REGISTRY_FILE
from .sources import derived

SECTIONS = (
    "gdp", "labour", "wages", "inflation", "financial", "ecb",
    "fiscal", "activity", "housing", "international",
)

# How old the latest observation may get before we flag the series as not updating.
DEFAULT_MAX_AGE_DAYS = {"D": 10, "M": 120, "Q": 260, "A": 560}


@dataclass
class Indicator:
    id: str
    label: str
    label_es: str
    section: str
    source: str
    key: str
    freq: str
    unit: str
    params: dict = field(default_factory=dict)
    scale: float = 1.0              # multiply fetched values, e.g. 0.001 for persons -> thousands
    transforms: tuple[str, ...] = ("level",)
    decimals: int = 1
    change_unit: str | None = None  # "pp" or "bp" for rates, "%" for relative change
    tile: int | None = None         # position in the key-indicators strip
    max_age_days: int | None = None
    notes: str = ""

    @property
    def headline(self) -> str:
        return self.transforms[0]

    @property
    def max_age(self) -> int:
        return self.max_age_days or DEFAULT_MAX_AGE_DAYS[self.freq]

    @property
    def is_derived(self) -> bool:
        return self.source == sources.DERIVED

    def source_url(self) -> str | None:
        client = sources.CLIENTS.get(self.source)
        return client.source_url(self.key, self.params) if client else None

    def signature(self) -> str:
        """Identifies what is fetched; stored history is only reused while this stays the same."""
        return json.dumps([self.source, self.key, self.params, self.scale], sort_keys=True, ensure_ascii=False)


def load_registry(path: Path = REGISTRY_FILE) -> list[Indicator]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    indicators = []
    for entry in raw["indicators"]:
        entry = dict(entry)
        entry["transforms"] = tuple(entry.get("transforms", ("level",)))
        entry["params"] = entry.get("params") or {}
        indicators.append(Indicator(**entry))
    validate(indicators)
    return indicators


def validate(indicators: list[Indicator]) -> None:
    errors, seen, tiles = [], set(), {}
    for ind in indicators:
        where = f"[{ind.id}]"
        if ind.id in seen:
            errors.append(f"{where} duplicate id")
        if ind.source not in sources.CLIENTS and not ind.is_derived:
            errors.append(f"{where} unknown source {ind.source!r}")
        if ind.freq not in transforms.FREQS:
            errors.append(f"{where} unknown freq {ind.freq!r}")
        if ind.section not in SECTIONS:
            errors.append(f"{where} unknown section {ind.section!r}")
        for t in ind.transforms:
            if t not in transforms.TRANSFORMS:
                errors.append(f"{where} unknown transform {t!r}")
        if ind.change_unit not in (None, "pp", "bp", "%"):
            errors.append(f"{where} change_unit must be pp, bp or %")
        if ind.tile is not None:
            if ind.tile in tiles:
                errors.append(f"{where} tile {ind.tile} already used by {tiles[ind.tile]}")
            tiles[ind.tile] = ind.id
        if ind.is_derived:
            for dep in derived.inputs_of(ind.params):
                if dep not in seen:
                    errors.append(f"{where} input {dep!r} must be defined earlier in the registry")
        seen.add(ind.id)
    if errors:
        raise ValueError("Invalid indicator registry:\n  " + "\n  ".join(errors))
