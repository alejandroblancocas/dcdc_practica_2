"""Rutas y utilidades compartidas; ejecutar desde cualquier directorio."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
MODELS = ROOT / "models"
REPORTS = ROOT / "reports"


def config():
    for path in (RAW, PROCESSED, MODELS, REPORTS):
        path.mkdir(parents=True, exist_ok=True)
    return json.loads((ROOT / "config.json").read_text(encoding="utf-8"))


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require_file(path):
    if not path.is_file():
        raise FileNotFoundError(f"Falta {path}. Ejecuta primero el paso anterior del README.")
    return path


def prepared_hash():
    with require_file(PROCESSED / "corpus_clean.parquet").open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()
