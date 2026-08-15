"""
updater.py — revisa si a la base le falta el mes actual y trata de completarlo.

Se pensó para correr 1 vez por mes (a mano, o con un "cron job" / tarea
programada del hosting). La lógica es siempre la misma:

    1. Mirar cuál es el último (año, mes) que ya tenemos en la tabla `traffic`.
    2. Compararlo contra el mes calendario actual.
    3. Si falta algo -> intentar descargarlo de la fuente oficial y cargarlo.
    4. Si no falta nada -> no hacer nada y avisar que está al día.

Fuente oficial de pasajeros/operaciones (gob.mx / AFAC):
  Reportes mensuales en PDF, URL con este patrón:
  https://www.gob.mx/cms/uploads/attachment/file/<id>/producto-aeropuertos-es-<mes>-<aa>-<fecha>.pdf
  El <id> numérico cambia cada mes y no es predecible, así que en la
  práctica hay que:
    a) entrar a https://www.gob.mx/afac (sección de estadísticas) y tomar
       el link del mes más reciente, o
    b) usar el histórico consolidado de datos.gob.mx como respaldo.

  Por eso PARSE_PDF_A_TABLA queda como función a completar: requiere una
  librería de lectura de PDF (ej. pdfplumber) y mapear las columnas del
  reporte a nuestras columnas. Te dejo la estructura lista para que la
  completemos juntos en la próxima clase, probando con un PDF real.
"""
import sqlite3
import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "tua.db"


def ultimo_mes_cargado(conn, airport_id=None):
    """Devuelve el (año, mes) más reciente que ya está en la base."""
    if airport_id:
        cur = conn.execute(
            "SELECT MAX(year), MAX(month) FROM traffic WHERE airport_id = ?",
            (airport_id,),
        )
    else:
        cur = conn.execute("SELECT MAX(year), MAX(month) FROM traffic")
    return cur.fetchone()


def mes_actual():
    hoy = datetime.date.today()
    return hoy.year, hoy.month


def falta_mes_actual(conn):
    """True si el mes calendario actual todavía no está cargado para ningún aeropuerto."""
    anio_db, mes_db = ultimo_mes_cargado(conn)
    if anio_db is None:
        return True  # base vacía, falta todo
    anio_hoy, mes_hoy = mes_actual()
    # Ojo: normalmente el reporte del mes actual sale con ~1 mes de retraso,
    # así que en la práctica conviene comparar contra el mes anterior, no
    # contra el mes en curso. Ajustable acá:
    mes_objetivo = mes_hoy - 1 or 12
    anio_objetivo = anio_hoy if mes_hoy > 1 else anio_hoy - 1
    return (anio_db, mes_db) < (anio_objetivo, mes_objetivo)


def parse_pdf_a_tabla(pdf_path):
    """
    TODO (próxima clase): usar pdfplumber para extraer la tabla del PDF
    oficial y devolver una lista de dicts:
    [{"code": "MEX", "year": 2026, "month": 7,
      "passengers_nacional": ..., "passengers_internacional": ...,
      "operaciones_nacional": ..., "operaciones_internacional": ...}, ...]
    """
    raise NotImplementedError("Falta implementar la lectura del PDF oficial")


def main():
    conn = sqlite3.connect(DB_PATH)
    if falta_mes_actual(conn):
        print("Falta cargar el último mes disponible. Buscando fuente oficial...")
        # TODO: descargar el PDF/CSV más reciente de gob.mx/afac y llamar a
        # parse_pdf_a_tabla(), luego insertar en `traffic` con INSERT OR IGNORE.
        print("Pendiente: implementar descarga automática (ver comentarios arriba).")
    else:
        print("La base ya está al día con el último mes disponible.")
    conn.close()


if __name__ == "__main__":
    main()
