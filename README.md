# Agente TUA — Aeropuertos de México

Dashboard que muestra TUA, pasajeros, operaciones e ingresos estimados de
los 10 principales aeropuertos de México, con proyección por quinquenio.

## Estructura

```
agente-qo-tua/
├── app.py              # Dashboard Streamlit (lo que se ve en el navegador)
├── projection.py        # Función de proyección por quinquenio
├── updater.py            # Chequea/carga el último mes disponible
├── requirements.txt
├── data/
│   └── airports_seed.csv  # Lista de los 10 aeropuertos
└── db/
    ├── schema.sql        # Estructura de la base de datos
    ├── seed_tua.py        # Crea la base y carga aeropuertos + TUA semilla
    └── seed_traffic.py    # Carga tráfico real (gob.mx + GAP + ASUR/OMA)
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
- **TUA**: cargada para 8 de los 10 (falta Puerto Vallarta y Mérida).
- **Tráfico de pasajeros**: 96 filas reales, de 3 fuentes oficiales:
  - **gob.mx** (SICT/AFAC/DT): dic-2022 y dic-2023, los 10 aeropuertos.
  - **GAP** (comunicados mensuales propios): serie COMPLETA enero a
    julio de 2025 y 2026 (14 meses) para Guadalajara, Tijuana, Los
    Cabos, Puerto Vallarta y Del Bajío/Guanajuato.
  - **ASUR y OMA** (comunicados mensuales propios): julio 2025/2026
    para Cancún, Mérida y Monterrey.
  - **AICM y AIFA no tienen comunicado mensual público** con el mismo
    detalle — solo cuentan con dic-2022 y dic-2023.
  - ⚠️ Los años siguen sin los 12 meses completos (falta ago-dic de
    2025/2026 y todo 2024), así que los "totales anuales" que usa la
    proyección son parciales — el dashboard lo marca con una
    advertencia (columna "meses cargados").
- **Operaciones (vuelos)**: todavía sin cargar — ninguna de las 3
  fuentes usadas trae ese dato junto con los pasajeros.

## Lo que falta completar (próximos pasos del TP)

1. **Completar 2024 y ago-dic de 2025/2026**: seguir sumando
   comunicados mensuales de GAP, ASUR y OMA (mismo patrón que
   seed_traffic.py).
2. **Buscar AICM y AIFA**: no publican comunicado mensual como
   GAP/ASUR/OMA; revisar aicm.com.mx o gob.mx/afac mes a mes.
3. **Buscar operaciones (vuelos)**: ninguna fuente usada hasta ahora
   las trae junto a pasajeros — hace falta otra fuente (posiblemente
   ASA o el dataset específico de cada aeropuerto en datos.gob.mx).
4. **Completar TUA faltante** (Puerto Vallarta, Mérida).
5. **Completar `updater.py`**: implementar `parse_pdf_a_tabla()` para
   automatizar la descarga mensual en vez de cargar a mano.
6. **Desplegar**: subir este repo a GitHub y conectarlo en
   share.streamlit.io (Streamlit Community Cloud) — detecta `app.py`
   y `requirements.txt` solo.
