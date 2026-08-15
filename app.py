"""
app.py — Dashboard del agente TUA.
Correr localmente con: streamlit run app.py
"""
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from projection import totales_anuales, proyectar_quinquenios

DB_PATH = Path(__file__).resolve().parent / "data" / "tua.db"

st.set_page_config(page_title="Agente TUA - Aeropuertos de México", layout="wide")
st.title("✈️ Agente QO — TUA, tráfico e ingresos de aeropuertos mexicanos")


@st.cache_data
def cargar_datos():
    conn = sqlite3.connect(DB_PATH)
    airports = pd.read_sql("SELECT * FROM airports", conn)
    traffic = pd.read_sql("SELECT * FROM traffic", conn)
    tua = pd.read_sql("SELECT * FROM tua_rates", conn)
    conn.close()
    return airports, traffic, tua


airports, traffic, tua = cargar_datos()

if traffic.empty:
    st.warning(
        "Todavía no hay datos de tráfico (pasajeros/operaciones) cargados. "
        "Falta correr la carga histórica (ver README) y luego updater.py."
    )

# --- Filtro lateral ---
st.sidebar.header("Filtros")
nombres = airports["name"].tolist()
seleccionados = st.sidebar.multiselect(
    "Aeropuerto(s) a mostrar / comparar", nombres, default=nombres[:3]
)

ids_seleccionados = airports[airports["name"].isin(seleccionados)]["id"].tolist()
traffic_f = traffic[traffic["airport_id"].isin(ids_seleccionados)]
tua_f = tua[tua["airport_id"].isin(ids_seleccionados)]

# --- Última TUA vigente por aeropuerto seleccionado ---
st.subheader("Tarifa TUA vigente")
if not tua_f.empty:
    ultima_tua = (
        tua_f.sort_values("effective_date")
        .groupby("airport_id")
        .last()
        .reset_index()
        .merge(airports, left_on="airport_id", right_on="id")
    )
    st.dataframe(
        ultima_tua[["name", "effective_date", "tua_nacional", "tua_internacional", "source_url"]],
        use_container_width=True,
    )
else:
    st.info("No hay tarifas TUA cargadas para la selección actual.")

# --- Gráficos de operaciones y pasajeros ---
if not traffic_f.empty:
    traffic_f = traffic_f.merge(airports, left_on="airport_id", right_on="id")
    traffic_f["fecha"] = pd.to_datetime(
        traffic_f["year"].astype(str) + "-" + traffic_f["month"].astype(str) + "-01"
    )
    traffic_f["pasajeros"] = (
        traffic_f["passengers_nacional"].fillna(0) + traffic_f["passengers_internacional"].fillna(0)
    )
    traffic_f["operaciones"] = (
        traffic_f["operaciones_nacional"].fillna(0) + traffic_f["operaciones_internacional"].fillna(0)
    )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Pasajeros por mes")
        pivot_pax = traffic_f.pivot_table(index="fecha", columns="name", values="pasajeros")
        st.line_chart(pivot_pax)
    with col2:
        st.subheader("Operaciones por mes")
        pivot_ops = traffic_f.pivot_table(index="fecha", columns="name", values="operaciones")
        st.line_chart(pivot_ops)

    # --- Ingresos TUA estimados (pasajeros x tarifa vigente) ---
    st.subheader("Ingresos TUA estimados por mes")
    st.caption(
        "Cálculo aproximado: pasajeros nacionales x TUA nacional vigente + "
        "pasajeros internacionales x TUA internacional vigente (usa la última tarifa conocida)."
    )
    ingresos = []
    for _, row in traffic_f.iterrows():
        tarifa = ultima_tua[ultima_tua["airport_id"] == row["airport_id"]] if not tua_f.empty else pd.DataFrame()
        if not tarifa.empty:
            t = tarifa.iloc[0]
            ing = (row["passengers_nacional"] or 0) * (t["tua_nacional"] or 0) + \
                  (row["passengers_internacional"] or 0) * (t["tua_internacional"] or 0)
        else:
            ing = None
        ingresos.append(ing)
    traffic_f["ingreso_tua_estimado"] = ingresos
    pivot_ing = traffic_f.pivot_table(index="fecha", columns="name", values="ingreso_tua_estimado")
    st.bar_chart(pivot_ing)

    # --- Proyección por quinquenio ---
    st.subheader("Proyección por quinquenio")
    st.caption(
        "⚠️ Los totales por año se calculan solo con los meses que ya están "
        "cargados en la base (no siempre son los 12 meses). Mientras falten "
        "meses, comparar un año contra otro puede ser engañoso: fijate en la "
        "columna 'meses cargados' antes de confiar en la proyección."
    )
    n_q = st.slider("¿Cuántos quinquenios proyectar?", 1, 5, 3)
    for aid in ids_seleccionados:
        nombre = airports[airports["id"] == aid]["name"].values[0]
        df_air = traffic_f[traffic_f["airport_id"] == aid]
        anual = totales_anuales(df_air)
        st.markdown(f"**{nombre}**")
        st.dataframe(
            anual.rename(columns={"meses_cargados": "meses cargados"}),
            use_container_width=True,
        )
        if (anual["meses_cargados"] < 12).any():
            st.caption("Algunos años tienen menos de 12 meses cargados — el total no es comparable todavía.")
        if len(anual) >= 2:
            proy = proyectar_quinquenios(anual, n_quinquenios=n_q)
            st.dataframe(proy, use_container_width=True)
        else:
            st.caption("Faltan al menos 2 años de historia para proyectar este aeropuerto.")
else:
    st.info("Elegí al menos un aeropuerto con datos cargados para ver los gráficos.")
