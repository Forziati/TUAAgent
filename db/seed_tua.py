"""
Crea la base de datos (si no existe) y carga:
  1) La lista de aeropuertos (desde data/airports_seed.csv)
  2) Las tarifas TUA vigentes que encontramos por búsqueda web (agosto 2026)

Correr una sola vez: python db/seed_tua.py
"""
import csv
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "tua.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
AIRPORTS_CSV = Path(__file__).resolve().parent.parent / "data" / "airports_seed.csv"

# Tarifas TUA encontradas por búsqueda web (vigentes en 2026).
# IMPORTANTE: cada aeropuerto actualiza esto por su cuenta y puede cambiar
# mes a mes. Estos son los últimos valores públicos que encontramos, con su
# fuente, para que el agente tenga un punto de partida real.
TUA_SEED = [
    # code, effective_date, tua_nacional, tua_internacional, source_url
    ("MEX", "2026-04-01", 537.228, 1020.009,
     "https://www.gob.mx (ajuste AICM abril 2026, +2.9%)"),
    ("NLU", "2026-07-01", 266.62, None,
     "https://aifa.aero/tua"),
    ("MTY", "2026-01-01", 600.0, 1115.0,
     "https://heraldodemexico.com.mx (ajuste TUA 2026)"),
    ("GDL", "2026-01-01", 665.0, 1404.0,
     "https://heraldodemexico.com.mx (ajuste TUA 2026)"),
    ("SJD", "2026-01-01", 655.0, 1404.0,
     "https://heraldodemexico.com.mx (ajuste TUA 2026)"),
    ("TIJ", "2025-01-01", 619.0, None,
     "https://www.informador.mx (tarifas TUA 2026)"),
    ("CUN", "2025-01-01", 351.0, 861.0,
     "https://www.informador.mx (tarifas TUA 2026)"),
    # PVR, MID y BJX: no encontramos aún la tarifa puntual -> queda pendiente
    # de completar a mano o en la próxima corrida del updater.
]


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_PATH.read_text())

    # 1) Cargar aeropuertos
    with open(AIRPORTS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            conn.execute(
                "INSERT OR IGNORE INTO airports (code, name, operator) VALUES (?, ?, ?)",
                (row["code"], row["name"], row["operator"]),
            )

    # 2) Cargar tarifas TUA semilla
    code_to_id = {
        row[0]: row[1]
        for row in conn.execute("SELECT code, id FROM airports")
    }
    for code, eff_date, nac, inter, source in TUA_SEED:
        airport_id = code_to_id.get(code)
        if airport_id is None:
            print(f"Aviso: código {code} no está en airports_seed.csv, se omite")
            continue
        conn.execute(
            """INSERT OR IGNORE INTO tua_rates
               (airport_id, effective_date, tua_nacional, tua_internacional, source_url)
               VALUES (?, ?, ?, ?, ?)""",
            (airport_id, eff_date, nac, inter, source),
        )

    conn.commit()
    conn.close()
    print(f"Base de datos lista en: {DB_PATH}")


if __name__ == "__main__":
    main()
