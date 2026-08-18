"""
seed_traffic.py - carga datos REALES de pasajeros, combinando 3 fuentes
oficiales distintas:

  1) gob.mx (SICT/AFAC/DT): dic-2022 y dic-2023, los 10 aeropuertos.

  2) GAP (Grupo Aeroportuario del Pacifico) - comunicados mensuales
     propios (GlobeNewswire/Nasdaq): serie COMPLETA enero-julio de
     2025 y 2026 para Guadalajara, Tijuana, Los Cabos, Puerto Vallarta
     y Del Bajio/Guanajuato.

  3) ASUR y OMA - comunicados mensuales propios: julio 2025/2026 para
     Cancun, Merida y Monterrey (numeros exactos, no en miles).

IMPORTANTE - que sigue faltando:
  - AICM (MEX) y AIFA (NLU): sin comunicado mensual publico como
    GAP/ASUR/OMA, solo dic-2022 y dic-2023.
  - Agosto en adelante de 2025/2026, y todo 2024: no cargado todavia.
  - Operaciones (vuelos): ninguna de estas fuentes las trae junto con
    pasajeros.
"""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tua.db"

FUENTE_GOBMX = ("Estadistica Operacional de Aeropuertos - Diciembre 2023 (SICT/AFAC/DT) - "
                "https://www.gob.mx/cms/uploads/attachment/file/885180/"
                "producto-aeropuertos-es-dic-23-26012024.pdf")
FUENTE_GAP = ("GAP - serie historica compilada de los reportes mensuales en PDF "
              "(aeropuertosgap.com.mx), mayo 2016 a mayo 2026")
FUENTE_ASUR_OMA = ("ASUR (prnewswire.com, jul-2026) y OMA (noticias.oma.aero, jul-2026) - "
                    "comunicados mensuales de trafico de pasajeros")
FUENTE_OMA_EXCEL = ("OMA - Excel oficial de trafico historico de pasajeros "
                     "(oma.aero/es/nuestros-servicios/aviacion-comercial/monterrey-c/"
                     "estadisticas-de-pasajeros.php)")
FUENTE_ASUR_EXCEL = ("ASUR - Excel oficial de trafico historico de pasajeros "
                      "(asur.com.mx/trafico-de-pasajeros-1), enero 2000 a julio 2026")

DATOS_GOBMX = [
    ("MEX", 2022, 12, 2861.8, 1376.9), ("MEX", 2023, 12, 2700.9, 1557.9),
    ("CUN", 2022, 12, 1050.5, 1884.1), ("CUN", 2023, 12, 961.6, 2059.6),
    ("GDL", 2022, 12, 1103.3, 438.0), ("GDL", 2023, 12, 1027.9, 531.2),
    ("MTY", 2022, 12, 919.0, 167.2), ("MTY", 2023, 12, 970.3, 170.9),
    ("TIJ", 2022, 12, 1146.8, None), ("TIJ", 2023, 12, 1102.6, None),
    ("SJD", 2022, 12, 247.1, 403.6), ("SJD", 2023, 12, 251.5, 425.2),
    ("PVR", 2022, 12, 246.9, 416.6), ("PVR", 2023, 12, 227.0, 467.5),
    ("MID", 2022, 12, 301.9, 25.7), ("MID", 2023, 12, 313.5, 30.0),
    ("NLU", 2022, 12, 199.9, 11.8), ("NLU", 2023, 12, 253.6, 22.9),
    ("BJX", 2022, 12, 188.0, 73.9), ("BJX", 2023, 12, 189.2, 83.1),
]

# Serie completa GDL/TIJ/SJD/PVR/BJX: mayo-2016 a mayo-2026, extraida del
# Excel de GAP que compilo el propio usuario a partir de los reportes
# mensuales en PDF (gap_full_history.json, generado aparte). Los valores
# ya vienen en pasajeros exactos (no en miles).
GAP_JSON_PATH = Path(__file__).resolve().parent / "gap_full_history.json"

# Serie completa CUN y MID: enero-2000 a julio-2026, extraida del Excel
# oficial de ASUR (asur_full_history.json, generado aparte). Valores ya
# en pasajeros exactos (no en miles).
ASUR_JSON_PATH = Path(__file__).resolve().parent / "asur_full_history.json"

DATOS_ASUR_OMA = [
    # MTY (Monterrey) - solo julio via comunicado mensual; la serie completa
    # 2024-2026 se carga aparte, desde el Excel oficial de OMA (mas abajo).
    ("MTY", 2025, 7, 1269119, 235347), ("MTY", 2026, 7, 1240747, 261947),
]

# MTY (Monterrey) - serie completa 2024, 2025 y 2026, extraida del Excel
# historico oficial de OMA (fuente distinta al comunicado mensual de arriba).
DATOS_OMA_EXCEL_MTY = [
    ("MTY", 2024, 1, 817194, 155889), ("MTY", 2024, 2, 744793, 137897),
    ("MTY", 2024, 3, 852897, 172495), ("MTY", 2024, 4, 867584, 162242),
    ("MTY", 2024, 5, 937807, 173222), ("MTY", 2024, 6, 913359, 183716),
    ("MTY", 2024, 7, 1100114, 215201), ("MTY", 2024, 8, 1071452, 200659),
    ("MTY", 2024, 9, 933935, 179820), ("MTY", 2024, 10, 975338, 191437),
    ("MTY", 2024, 11, 1067546, 207175), ("MTY", 2024, 12, 1074750, 245077),
    ("MTY", 2025, 1, 905723, 207934), ("MTY", 2025, 2, 819214, 162815),
    ("MTY", 2025, 3, 994105, 201495), ("MTY", 2025, 4, 1139113, 234601),
    ("MTY", 2025, 5, 1086661, 215272), ("MTY", 2025, 6, 1110255, 213193),
    ("MTY", 2025, 8, 1229554, 217927), ("MTY", 2025, 9, 1081071, 189511),
    ("MTY", 2025, 10, 1142717, 202812), ("MTY", 2025, 11, 1142971, 202633),
    ("MTY", 2025, 12, 1171622, 247610), ("MTY", 2026, 1, 1003821, 199023),
    ("MTY", 2026, 2, 907833, 154814), ("MTY", 2026, 3, 1084554, 191788),
    ("MTY", 2026, 4, 1078875, 196193), ("MTY", 2026, 5, 1136007, 196848),
    ("MTY", 2026, 6, 1092665, 235257),
]


def cargar(conn, code_to_id, filas, fuente, escala_miles):
    insertados = 0
    for code, year, month, dom, intl in filas:
        airport_id = code_to_id.get(code)
        if airport_id is None:
            continue
        pax_nac = round(dom * 1000) if (dom is not None and escala_miles) else (
            round(dom) if dom is not None else None)
        pax_intl = round(intl * 1000) if (intl is not None and escala_miles) else (
            round(intl) if intl is not None else None)
        conn.execute(
            """INSERT OR IGNORE INTO traffic
               (airport_id, year, month, passengers_nacional, passengers_internacional,
                operaciones_nacional, operaciones_internacional, source_url)
               VALUES (?, ?, ?, ?, ?, NULL, NULL, ?)""",
            (airport_id, year, month, pax_nac, pax_intl, fuente),
        )
        insertados += 1
    return insertados


def main():
    conn = sqlite3.connect(DB_PATH)
    code_to_id = dict(conn.execute("SELECT code, id FROM airports"))

    n1 = cargar(conn, code_to_id, DATOS_GOBMX, FUENTE_GOBMX, escala_miles=True)

    with open(GAP_JSON_PATH) as f:
        datos_gap = [tuple(x) for x in json.load(f)]
    n2 = cargar(conn, code_to_id, datos_gap, FUENTE_GAP, escala_miles=False)

    n3 = cargar(conn, code_to_id, DATOS_ASUR_OMA, FUENTE_ASUR_OMA, escala_miles=False)
    n4 = cargar(conn, code_to_id, DATOS_OMA_EXCEL_MTY, FUENTE_OMA_EXCEL, escala_miles=False)

    with open(ASUR_JSON_PATH) as f:
        datos_asur = [tuple(x) for x in json.load(f)]
    n5 = cargar(conn, code_to_id, datos_asur, FUENTE_ASUR_EXCEL, escala_miles=False)

    conn.commit()
    conn.close()
    print(f"Cargadas {n1} filas de gob.mx, {n2} de GAP, {n3} de ASUR/OMA, "
          f"{n4} de OMA (Excel Monterrey), {n5} de ASUR (Excel Cancun/Merida).")
    print("Operaciones (vuelos): siguen pendientes, ninguna fuente las trae junto a pasajeros.")


if __name__ == "__main__":
    main()
