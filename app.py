"""
app.py — Dashboard del agente TUA.
Correr localmente con: streamlit run app.py
"""
import sqlite3
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from projection import totales_anuales, proyectar_quinquenios

DB_PATH = Path(__file__).resolve().parent / "data" / "tua.db"

st.set_page_config(page_title="Agente TUA - Aeropuertos de México", layout="wide")
st.title("✈️ Agente QO — TUA, tráfico e ingresos de aeropuertos mexicanos")


# --- Helpers de formato (números con coma de miles, punto decimal, pesos con MN) ---
def fmt_num(x):
    """1234567 -> '1,234,567'"""
    if pd.isna(x):
        return "-"
    return f"{x:,.0f}"


def fmt_money(x):
    """1234567.8 -> '$1,234,567.80 MN'"""
    if pd.isna(x):
        return "-"
    return f"${x:,.2f} MN"


def safe(x):
    """Reemplaza None/NaN por 0. OJO: 'x or 0' NO sirve para esto porque
    en Python 'float('nan') or 0' da NaN (nan se evalua como verdadero),
    no 0 — hay que chequear con pd.isna() explicitamente."""
    return 0 if pd.isna(x) else x


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
    st.stop()

# --- Filtros laterales ---
st.sidebar.header("Filtros")
nombres = airports["name"].tolist()
seleccionados = st.sidebar.multiselect(
    "Aeropuerto(s) a mostrar / comparar", nombres, default=nombres[:3]
)

anios_disponibles = sorted(traffic["year"].unique())
anios_sel = st.sidebar.multiselect(
    "Año(s)", anios_disponibles, default=anios_disponibles
)

ids_seleccionados = airports[airports["name"].isin(seleccionados)]["id"].tolist()
traffic_f = traffic[
    traffic["airport_id"].isin(ids_seleccionados) & traffic["year"].isin(anios_sel)
].copy()
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
    tabla_tua = ultima_tua[["name", "effective_date", "tua_nacional", "tua_internacional", "source_url"]].copy()
    tabla_tua["tua_nacional"] = tabla_tua["tua_nacional"].apply(fmt_money)
    tabla_tua["tua_internacional"] = tabla_tua["tua_internacional"].apply(fmt_money)
    tabla_tua = tabla_tua.rename(columns={
        "name": "Aeropuerto",
        "effective_date": "Vigente desde",
        "tua_nacional": "TUA nacional",
        "tua_internacional": "TUA internacional",
        "source_url": "Fuente",
    })
    st.dataframe(tabla_tua, use_container_width=True, hide_index=True)
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
    sin_tua = [
        airports[airports["id"] == aid]["name"].values[0]
        for aid in ids_seleccionados
        if not tua_f.empty and aid not in tua_f["airport_id"].values
    ]
    if sin_tua:
        st.warning(
            "Sin tarifa TUA cargada todavía: " + ", ".join(sin_tua) +
            ". Sus barras de ingreso van a salir vacías en TODOS sus meses "
            "(no es un error de datos faltantes, es que la tarifa no está cargada)."
        )
    st.caption(
        "Los huecos entre fechas (ej. entre dic-2023 y ene-2025) son meses que "
        "todavía no se cargaron a la base, no un error del gráfico."
    )
    ingresos = []
    for _, row in traffic_f.iterrows():
        tarifa = ultima_tua[ultima_tua["airport_id"] == row["airport_id"]] if not tua_f.empty else pd.DataFrame()
        if not tarifa.empty:
            t = tarifa.iloc[0]
            ing = safe(row["passengers_nacional"]) * safe(t["tua_nacional"]) + \
                  safe(row["passengers_internacional"]) * safe(t["tua_internacional"])
        else:
            ing = None
        ingresos.append(ing)
    traffic_f["ingreso_tua_estimado"] = ingresos
    pivot_ing = traffic_f.pivot_table(index="fecha", columns="name", values="ingreso_tua_estimado")
    st.bar_chart(pivot_ing)

    # --- Comparar un mes específico entre aeropuertos ---
    st.subheader("Comparar un mes específico")
    meses_es = {1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
                7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"}
    combos = traffic_f[["year", "month"]].drop_duplicates().sort_values(["year", "month"])
    combos["etiqueta"] = combos.apply(lambda r: f"{meses_es[r['month']]} {r['year']}", axis=1)

    if not combos.empty:
        etiqueta_sel = st.selectbox("Elegí el mes a comparar", combos["etiqueta"].tolist(), index=len(combos) - 1)
        fila = combos[combos["etiqueta"] == etiqueta_sel].iloc[0]
        mes_data = traffic_f[(traffic_f["year"] == fila["year"]) & (traffic_f["month"] == fila["month"])]

        tabla_mes = mes_data[["name", "passengers_nacional", "passengers_internacional",
                               "pasajeros", "operaciones", "ingreso_tua_estimado"]].copy()
        tabla_mes["passengers_nacional"] = tabla_mes["passengers_nacional"].apply(fmt_num)
        tabla_mes["passengers_internacional"] = tabla_mes["passengers_internacional"].apply(fmt_num)
        tabla_mes["pasajeros"] = tabla_mes["pasajeros"].apply(fmt_num)
        tabla_mes["operaciones"] = tabla_mes["operaciones"].apply(fmt_num)
        tabla_mes["ingreso_tua_estimado"] = tabla_mes["ingreso_tua_estimado"].apply(fmt_money)
        tabla_mes = tabla_mes.rename(columns={
            "name": "Aeropuerto",
            "passengers_nacional": "Pasajeros nacionales",
            "passengers_internacional": "Pasajeros internacionales",
            "pasajeros": "Pasajeros totales",
            "operaciones": "Operaciones",
            "ingreso_tua_estimado": "Ingreso TUA estimado",
        })
        st.dataframe(tabla_mes, use_container_width=True, hide_index=True)

        if len(mes_data) < 2:
            st.caption(
                "Con un solo aeropuerto seleccionado no hay nada que comparar todavía — "
                "elegí 2 o más en \"Aeropuerto(s) a mostrar / comparar\" (barra lateral)."
            )
        grafico_mes = (
            alt.Chart(mes_data)
            .mark_bar(size=40)
            .encode(
                x=alt.X("name:N", title="Aeropuerto", sort="-y"),
                y=alt.Y("pasajeros:Q", title="Pasajeros", scale=alt.Scale(domainMin=0)),
                tooltip=[alt.Tooltip("name:N", title="Aeropuerto"),
                         alt.Tooltip("pasajeros:Q", title="Pasajeros", format=",.0f")],
            )
            .properties(height=320)
        )
        st.altair_chart(grafico_mes, use_container_width=True)
    else:
        st.caption("No hay meses cargados todavía para esta selección.")

    # --- Proyección por quinquenio ---
    st.subheader("Proyección por quinquenio")
    st.caption(
        "⚠️ Los totales por año se calculan solo con los meses que ya están "
        "cargados en la base (no siempre son los 12 meses). Mientras falten "
        "meses, comparar un año contra otro puede ser engañoso: fijate en la "
        "columna 'Meses cargados' antes de confiar en la proyección."
    )
    n_q = st.slider("¿Cuántos quinquenios proyectar?", 1, 5, 3)
    for aid in ids_seleccionados:
        nombre = airports[airports["id"] == aid]["name"].values[0]
        df_air = traffic_f[traffic_f["airport_id"] == aid]
        anual = totales_anuales(df_air)
        st.markdown(f"**{nombre}**")

        tabla_anual = anual.copy()
        tabla_anual["pasajeros"] = tabla_anual["pasajeros"].apply(fmt_num)
        tabla_anual["operaciones"] = tabla_anual["operaciones"].apply(fmt_num)
        tabla_anual = tabla_anual.rename(columns={
            "year": "Año", "pasajeros": "Pasajeros", "operaciones": "Operaciones",
            "meses_cargados": "Meses cargados",
        })
        st.dataframe(tabla_anual, use_container_width=True, hide_index=True)

        if (anual["meses_cargados"] < 12).any():
            incompletos = anual[anual["meses_cargados"] < 12]["year"].tolist()
            st.caption(
                f"Años excluidos del cálculo de la proyección por tener menos de 12 meses "
                f"cargados: {incompletos}. Solo se usan años completos para que la recta no "
                f"se distorsione."
            )
        completos = anual[anual["meses_cargados"] >= 12]
        if len(completos) >= 2:
            proy = proyectar_quinquenios(anual, n_quinquenios=n_q)
            tabla_proy = proy.copy()
            tabla_proy["pasajeros_proyectados"] = tabla_proy["pasajeros_proyectados"].apply(fmt_num)
            tabla_proy["operaciones_proyectadas"] = tabla_proy["operaciones_proyectadas"].apply(fmt_num)
            tabla_proy = tabla_proy.rename(columns={
                "quinquenio": "Quinquenio", "anio_desde": "Año desde", "anio_hasta": "Año hasta",
                "pasajeros_proyectados": "Pasajeros proyectados (total del quinquenio)",
                "operaciones_proyectadas": "Operaciones proyectadas (total del quinquenio)",
            })
            st.dataframe(tabla_proy, use_container_width=True, hide_index=True)
        else:
            st.caption(
                f"Todavía no hay suficientes años completos (12 meses) para proyectar "
                f"{nombre} de forma confiable — hay {len(completos)}, hacen falta al menos 2."
            )
else:
    st.info("Elegí al menos un aeropuerto y un año con datos cargados para ver los gráficos.")
