# Agente TUA — Aeropuertos de México

Dashboard que muestra TUA, pasajeros, operaciones e ingresos estimados de
los 10 principales aeropuertos de México, con proyección por quinquenio.

## Estructura

```
agente-qo-tua/
├── app.py                     # Dashboard Streamlit
├── projection.py               # Función de proyección por quinquenio
├── updater.py                   # Chequea/carga el último mes disponible
├── requirements.txt
├── README.md
├── data/
│   ├── airports_seed.csv        # Lista de los 10 aeropuertos
│   └── tua.db                    # Base de datos SQLite (ya cargada)
└── db/
    ├── schema.sql                # Estructura de la base de datos
    ├── seed_tua.py                # Crea la base y carga aeropuertos + TUA
    ├── seed_traffic.py            # Carga tráfico real (todas las fuentes)
    ├── gap_full_history.json      # Serie histórica GAP (2016-2026)
    └── asur_full_history.json     # Serie histórica ASUR (2000-2026)
```

## Cómo correrlo por primera vez (local o en Replit)

```bash
pip install -r requirements.txt
python db/seed_tua.py       # crea data/tua.db y carga aeropuertos + TUA
python db/seed_traffic.py    # carga tráfico real (ver fuentes abajo)
streamlit run app.py
```

## Estado actual de los datos (agosto 2026)

- **Aeropuertos**: los 10 reales por volumen de pasajeros (AICM, Cancún,
  Guadalajara, Monterrey, Tijuana, Los Cabos, Puerto Vallarta, Mérida,
  AIFA, Del Bajío).
- **TUA**: cargada para 8 de los 10 (faltan Puerto Vallarta y Del Bajío).
  Monterrey y Mérida tienen valores exactos y oficiales.
- **Tráfico de pasajeros**: 1,300 filas reales, de 5 fuentes oficiales:
  - **ASUR (Excel oficial)**: serie MENSUAL COMPLETA de **enero 2000 a
    julio 2026** (319 meses, 26 años) para Cancún y Mérida. Incluye la
    caída real de la pandemia en 2020, visible y consistente.
  - **GAP**: serie mensual completa de mayo 2016 a mayo 2026 (125
    meses) para Guadalajara, Tijuana, Los Cabos, Puerto Vallarta y
    Del Bajío.
  - **OMA (Excel oficial)**: serie mensual completa de Monterrey,
    2024 a jul-2026.
  - **gob.mx**: dic-2022 y dic-2023, los 10 aeropuertos (respaldo).
  - **AICM y AIFA no tienen fuente mensual pública** con el mismo
    detalle — solo cuentan con dic-2022 y dic-2023, los más débiles
    del proyecto.
- **Operaciones (vuelos)**: todavía sin cargar — ninguna fuente usada
  hasta ahora trae ese dato junto con los pasajeros.

## Cómo funciona la proyección (importante)

`projection.py` ajusta una regresión lineal SOLO con los años que
tienen los 12 meses cargados — un año parcial se excluye automáticamente
porque su total se parece al de un mes, no al de un año, y distorsiona
la recta. El total de cada quinquenio se calcula sumando la predicción
año por año. El dashboard muestra qué años quedaron afuera del cálculo
para cada aeropuerto. Con 26 y 10 años de historia real respectivamente,
Cancún/Mérida y los 5 aeropuertos de GAP tienen la proyección más
confiable del proyecto; AICM, AIFA y Monterrey siguen siendo los más
débiles por tener poca historia completa.

## Lo que falta completar (próximos pasos del TP)

1. **Buscar AICM y AIFA**: no publican fuente mensual como GAP/ASUR/OMA;
   revisar aicm.com.mx, datos.gob.mx (dataset `movimiento_operacional_aicm`,
   que también trae operaciones) o gob.mx/afac mes a mes.
2. **Buscar operaciones (vuelos)**: ninguna fuente usada hasta ahora
   las trae junto a pasajeros — el dataset de AICM en datos.gob.mx sí
   las tiene, sería un buen punto de partida.
3. **Completar TUA faltante** (Puerto Vallarta, Del Bajío).
4. **Completar `updater.py`**: implementar `parse_pdf_a_tabla()` para
   automatizar la descarga mensual en vez de cargar a mano.
5. **Desplegar**: ya está en Streamlit Community Cloud, conectado al
   repositorio de GitHub — se redespliega solo con cada actualización.
