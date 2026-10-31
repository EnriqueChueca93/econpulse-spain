"""Local storage: one CSV per indicator plus a JSON catalog of fetch status.

data/series/<id>.csv   date,value  (full history, period-start dates)
data/catalog.json      {id: {status, fetched_at, last_date, n_obs, error, ...}}
data/<name>.json       other saved state: the release calendar, the log of new releases
"""

import json
from pathlib import Path

import pandas as pd

from .config import DATA_DIR


class Store:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = Path(data_dir)
        self.series_dir = self.data_dir / "series"
        self.catalog_file = self.data_dir / "catalog.json"

    def series_path(self, indicator_id: str) -> Path:
        return self.series_dir / f"{indicator_id}.csv"

    def save_series(self, indicator_id: str, series: pd.Series) -> None:
        self.series_dir.mkdir(parents=True, exist_ok=True)
        series.to_frame("value").to_csv(
            self.series_path(indicator_id),
            index_label="date",
            date_format="%Y-%m-%d",
            float_format="%.10g",
            lineterminator="\n",
        )

    def load_series(self, indicator_id: str) -> pd.Series | None:
        path = self.series_path(indicator_id)
        if not path.exists():
            return None
        df = pd.read_csv(path, parse_dates=["date"], index_col="date")
        return df["value"].astype("float64")

    def load_catalog(self) -> dict:
        if not self.catalog_file.exists():
            return {}
        return json.loads(self.catalog_file.read_text(encoding="utf-8"))

    def save_catalog(self, catalog: dict) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        text = json.dumps(dict(sorted(catalog.items())), indent=1, ensure_ascii=False)
        self.catalog_file.write_text(text + "\n", encoding="utf-8", newline="\n")

    def load_json(self, name: str, default=None):
        path = self.data_dir / f"{name}.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default

    def save_json(self, name: str, obj) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        text = json.dumps(obj, indent=1, ensure_ascii=False)
        (self.data_dir / f"{name}.json").write_text(text + "\n", encoding="utf-8", newline="\n")
