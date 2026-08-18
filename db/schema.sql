-- Esquema de la base de datos del agente TUA
-- SQLite: no necesita servidor, es un solo archivo (.db)

CREATE TABLE IF NOT EXISTS airports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,        -- ej. 'MEX', 'CUN', 'GDL'
    name TEXT NOT NULL,               -- ej. 'Ciudad de México (AICM)'
    operator TEXT NOT NULL            -- ej. 'AICM', 'GAP', 'ASUR', 'OMA', 'AIFA', 'ASA'
);

CREATE TABLE IF NOT EXISTS tua_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    airport_id INTEGER NOT NULL REFERENCES airports(id),
    effective_date TEXT NOT NULL,     -- 'YYYY-MM-DD', desde cuándo rige esta tarifa
    tua_nacional REAL,                -- pesos MXN, IVA incluido (puede faltar temporalmente)
    tua_internacional REAL,           -- pesos MXN, IVA incluido (puede faltar temporalmente)
    source_url TEXT,                  -- de dónde se sacó el dato
    UNIQUE(airport_id, effective_date)
);

CREATE TABLE IF NOT EXISTS traffic (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    airport_id INTEGER NOT NULL REFERENCES airports(id),
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,           -- 1-12
    passengers_nacional INTEGER,
    passengers_internacional INTEGER,
    operaciones_nacional INTEGER,     -- despegues + aterrizajes nacionales
    operaciones_internacional INTEGER,
    source_url TEXT,
    UNIQUE(airport_id, year, month)
);
