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
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tua.db"

FUENTE_GOBMX = ("Estadistica Operacional de Aeropuertos - Diciembre 2023 (SICT/AFAC/DT) - "
                "https://www.gob.mx/cms/uploads/attachment/file/885180/"
                "producto-aeropuertos-es-dic-23-26012024.pdf")
FUENTE_GAP = "Comunicados mensuales de trafico de pasajeros de GAP (GlobeNewswire/Nasdaq), ene-jul 2025/2026"
FUENTE_ASUR_OMA = ("ASUR (prnewswire.com, jul-2026) y OMA (noticias.oma.aero, jul-2026) - "
                    "comunicados mensuales de trafico de pasajeros")
FUENTE_OMA_EXCEL = ("OMA - Excel oficial de trafico historico de pasajeros "
                     "(oma.aero/es/nuestros-servicios/aviacion-comercial/monterrey-c/"
                     "estadisticas-de-pasajeros.php)")

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

# Serie completa ene-jul 2025 y ene-jul 2026 (miles de pasajeros)
DATOS_GAP = [
    # GDL
    ("GDL", 2025, 1, 1006.2, 600.8), ("GDL", 2025, 2, 926.2, 430.1),
    ("GDL", 2025, 3, 1088.8, 476.1), ("GDL", 2025, 4, 1067.5, 452.9),
    ("GDL", 2025, 5, 1023.4, 457.5), ("GDL", 2025, 6, 1000.1, 476.9),
    ("GDL", 2025, 7, 1092.5, 563.9),
    ("GDL", 2026, 1, 1066.3, 598.1), ("GDL", 2026, 2, 906.2, 428.8),
    ("GDL", 2026, 3, 1063.1, 465.3), ("GDL", 2026, 4, 1066.2, 467.2),
    ("GDL", 2026, 5, 1085.9, 499.9), ("GDL", 2026, 6, 1033.9, 531.9),
    ("GDL", 2026, 7, 1225.6, 649.7),
    # TIJ
    ("TIJ", 2025, 1, 702.1, 380.0), ("TIJ", 2025, 2, 631.4, 290.1),
    ("TIJ", 2025, 3, 724.0, 344.7), ("TIJ", 2025, 4, 748.6, 351.1),
    ("TIJ", 2025, 5, 730.5, 336.6), ("TIJ", 2025, 6, 660.1, 364.1),
    ("TIJ", 2025, 7, 776.3, 379.1),
    ("TIJ", 2026, 1, 698.4, 338.7), ("TIJ", 2026, 2, 584.7, 268.9),
    ("TIJ", 2026, 3, 685.4, 290.0), ("TIJ", 2026, 4, 671.7, 312.8),
    ("TIJ", 2026, 5, 664.5, 297.9), ("TIJ", 2026, 6, 637.5, 339.4),
    ("TIJ", 2026, 7, 811.6, 427.2),
    # SJD
    ("SJD", 2025, 1, 232.2, 426.7), ("SJD", 2025, 2, 197.8, 410.5),
    ("SJD", 2025, 3, 238.9, 545.8), ("SJD", 2025, 4, 254.6, 442.9),
    ("SJD", 2025, 5, 245.0, 367.3), ("SJD", 2025, 6, 240.1, 414.1),
    ("SJD", 2025, 7, 282.9, 403.9),
    ("SJD", 2026, 1, 219.1, 437.9), ("SJD", 2026, 2, 185.7, 427.8),
    ("SJD", 2026, 3, 223.5, 507.0), ("SJD", 2026, 4, 240.9, 400.1),
    ("SJD", 2026, 5, 247.0, 328.8), ("SJD", 2026, 6, 235.4, 355.4),
    ("SJD", 2026, 7, 302.6, 336.9),
    # PVR
    ("PVR", 2025, 1, 229.5, 483.8), ("PVR", 2025, 2, 192.6, 457.3),
    ("PVR", 2025, 3, 231.5, 531.4), ("PVR", 2025, 4, 278.4, 375.7),
    ("PVR", 2025, 5, 278.2, 236.1), ("PVR", 2025, 6, 273.8, 237.3),
    ("PVR", 2025, 7, 321.5, 229.1),
    ("PVR", 2026, 1, 242.5, 489.2), ("PVR", 2026, 2, 186.5, 428.9),
    ("PVR", 2026, 3, 215.8, 360.8), ("PVR", 2026, 4, 255.1, 287.5),
    ("PVR", 2026, 5, 266.7, 173.5), ("PVR", 2026, 6, 257.4, 157.9),
    ("PVR", 2026, 7, 323.3, 160.9),
    # BJX
    ("BJX", 2025, 1, 176.8, 107.4), ("BJX", 2025, 2, 158.4, 72.4),
    ("BJX", 2025, 3, 180.3, 83.2), ("BJX", 2025, 4, 194.0, 84.3),
    ("BJX", 2025, 5, 194.1, 80.3), ("BJX", 2025, 6, 188.6, 88.1),
    ("BJX", 2025, 7, 204.0, 108.7),
    ("BJX", 2026, 1, 180.9, 109.6), ("BJX", 2026, 2, 151.3, 71.7),
    ("BJX", 2026, 3, 178.6, 76.6), ("BJX", 2026, 4, 179.1, 72.2),
    ("BJX", 2026, 5, 181.3, 71.9), ("BJX", 2026, 6, 173.4, 78.0),
    ("BJX", 2026, 7, 212.7, 102.1),
]

DATOS_ASUR_OMA = [
    # CUN (Cancun) - serie completa ene-jul 2025 y 2026
    ("CUN", 2025, 1, 813464, 1945595), ("CUN", 2026, 1, 743606, 1988889),
    ("CUN", 2025, 2, 680189, 1809498), ("CUN", 2026, 2, 630468, 1868343),
    ("CUN", 2025, 3, 794115, 2142355), ("CUN", 2026, 3, 747556, 2054234),
    ("CUN", 2025, 4, 835045, 1739253), ("CUN", 2026, 4, 789691, 1674788),
    ("CUN", 2025, 5, 867155, 1468569), ("CUN", 2026, 5, 841058, 1305796),
    ("CUN", 2025, 6, 828705, 1558510), ("CUN", 2026, 6, 759398, 1353772),
    ("CUN", 2025, 7, 921781, 1709759), ("CUN", 2026, 7, 917079, 1492358),
    # MID (Merida) - serie completa ene-jul 2025 y 2026
    ("MID", 2025, 1, 278728, 37753), ("MID", 2026, 1, 315955, 41433),
    ("MID", 2025, 2, 248115, 34932), ("MID", 2026, 2, 271434, 38726),
    ("MID", 2025, 3, 280523, 39066), ("MID", 2026, 3, 309513, 41830),
    ("MID", 2025, 4, 287801, 32524), ("MID", 2026, 4, 308622, 31690),
    ("MID", 2025, 5, 281520, 28352), ("MID", 2026, 5, 313280, 29549),
    ("MID", 2025, 6, 279926, 31718), ("MID", 2026, 6, 270792, 29404),
    ("MID", 2025, 7, 317740, 33557), ("MID", 2026, 7, 328378, 34450),
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
    n2 = cargar(conn, code_to_id, DATOS_GAP, FUENTE_GAP, escala_miles=True)
    n3 = cargar(conn, code_to_id, DATOS_ASUR_OMA, FUENTE_ASUR_OMA, escala_miles=False)
    n4 = cargar(conn, code_to_id, DATOS_OMA_EXCEL_MTY, FUENTE_OMA_EXCEL, escala_miles=False)

    conn.commit()
    conn.close()
    print(f"Cargadas {n1} filas de gob.mx, {n2} de GAP, {n3} de ASUR/OMA, {n4} de OMA (Excel Monterrey).")
    print("Operaciones (vuelos): siguen pendientes, ninguna fuente las trae junto a pasajeros.")


if __name__ == "__main__":
    main()
