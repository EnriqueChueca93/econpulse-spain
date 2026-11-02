"""The indicator registry: every series the site tracks, defined in indicators.yaml."""

import itertools
import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import sources, transforms
from .config import REGISTRY_FILE
from .sources import derived

SECTIONS = (
    "gdp", "labour", "wages", "inflation", "financial", "ecb",
    "fiscal", "activity", "housing", "pensions", "international", "regions", "analysis",
)

# How old the latest observation may get before we flag the series as not updating.
# Dates are period starts, so a year's figure published the following spring or
# December is already 15-23 months "old" when the next one is due.
DEFAULT_MAX_AGE_DAYS = {"D": 10, "M": 120, "Q": 260, "A": 850}


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

    @property
    def source_name(self) -> str:
        return sources.source_name(self.source, self.key)

    def source_url(self) -> str | None:
        client = sources.CLIENTS.get(self.source)
        return client.source_url(self.key, self.params) if client else None

    def signature(self) -> str:
        """Identifies what is fetched; stored history is only reused while this stays the same."""
        return json.dumps([self.source, self.key, self.params, self.scale], sort_keys=True, ensure_ascii=False)


def _fill(value, item: dict):
    """Fill {placeholders} in every string of an entry from one for_each item."""
    if isinstance(value, str):
        return value.format(**item)
    if isinstance(value, dict):
        return {k: _fill(v, item) for k, v in value.items()}
    if isinstance(value, list):
        return [_fill(v, item) for v in value]
    return value


def expand(entry: dict) -> list[dict]:
    """One entry, or one per item of its `for_each` list (a country or region, say). A `for_each` of
    several lists ([*measures, *countries]) gives one entry per combination, each item's fields merged."""
    entry = dict(entry)
    items = entry.pop("for_each", None)
    if items is None:
        return [entry]
    if items and all(isinstance(x, list) for x in items):
        items = [{k: v for part in combo for k, v in part.items()} for combo in itertools.product(*items)]
    return [_fill(entry, item) for item in items]


def load_registry(path: Path = REGISTRY_FILE) -> list[Indicator]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    indicators = []
    for entry in (e for template in raw["indicators"] for e in expand(template)):
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
