"""
projection.py — proyecta pasajeros/operaciones/ingresos TUA a futuro,
agrupado en bloques de 5 años (quinquenios).

Método: regresión lineal simple sobre el total anual histórico
(pasajeros = a * año + b). Es el método más simple y transparente para
explicar en un TP; más adelante se puede reemplazar por algo más fino
(ej. tasa de crecimiento compuesta, o un modelo por temporada).
"""
import numpy as np
import pandas as pd


def totales_anuales(df_traffic: pd.DataFrame) -> pd.DataFrame:
    """
    Recibe el dataframe de `traffic` (una fila por aeropuerto-mes) y
    devuelve el total de pasajeros y operaciones por año.
    """
    df = df_traffic.copy()
    df["passengers_nacional"] = pd.to_numeric(df["passengers_nacional"], errors="coerce")
    df["passengers_internacional"] = pd.to_numeric(df["passengers_internacional"], errors="coerce")
    df["operaciones_nacional"] = pd.to_numeric(df["operaciones_nacional"], errors="coerce")
    df["operaciones_internacional"] = pd.to_numeric(df["operaciones_internacional"], errors="coerce")
    df["pasajeros"] = df["passengers_nacional"].fillna(0) + df["passengers_internacional"].fillna(0)
    df["operaciones"] = df["operaciones_nacional"].fillna(0) + df["operaciones_internacional"].fillna(0)
    df = df.groupby("year").agg(
        pasajeros=("pasajeros", "sum"),
        operaciones=("operaciones", "sum"),
        meses_cargados=("month", "nunique"),
    ).reset_index()
    return df


def proyectar_quinquenios(df_anual: pd.DataFrame, n_quinquenios: int = 3) -> pd.DataFrame:
    """
    Ajusta una recta a los datos históricos anuales y proyecta el
    promedio anual esperado para cada uno de los próximos quinquenios.

    Devuelve un dataframe con columnas: quinquenio, anio_desde, anio_hasta,
    pasajeros_proyectados, operaciones_proyectadas.
    """
    if len(df_anual) < 2:
        raise ValueError("Se necesitan al menos 2 años de historia para proyectar")

    ultimo_anio = int(df_anual["year"].max())
    resultados = []

    for col, nombre in [("pasajeros", "pasajeros_proyectados"),
                         ("operaciones", "operaciones_proyectadas")]:
        x = df_anual["year"].values
        y = df_anual[col].values
        pendiente, ordenada = np.polyfit(x, y, 1)  # regresión lineal grado 1

        for q in range(n_quinquenios):
            anio_desde = ultimo_anio + 1 + q * 5
            anio_hasta = anio_desde + 4
            anios_medio = (anio_desde + anio_hasta) / 2
            valor_proyectado = pendiente * anios_medio + ordenada
            valor_proyectado = max(valor_proyectado, 0)  # no permitir negativos

            if len(resultados) <= q:
                resultados.append({
                    "quinquenio": q + 1,
                    "anio_desde": anio_desde,
                    "anio_hasta": anio_hasta,
                })
            resultados[q][nombre] = round(valor_proyectado)

    return pd.DataFrame(resultados)
