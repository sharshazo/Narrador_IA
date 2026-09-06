"""Carga claves/API keys desde un archivo .env local (NUNCA en config.yaml,
para no compartirlo/subirlo por error junto con el resto de la config) --
formato simple KEY=VALOR, una por linea, ver .env en la raiz del proyecto.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _load_env(base_dir: Path) -> dict:
    env_path = base_dir / ".env"
    values: dict[str, str] = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def get_env(base_dir: Path, key: str) -> str | None:
    return _load_env(base_dir).get(key)
