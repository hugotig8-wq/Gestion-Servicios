-- Contratos
CREATE TABLE contracts (
    id SERIAL PRIMARY KEY,
    numero_contrato VARCHAR(100) UNIQUE,
    pais VARCHAR(50), -- 'España' o 'Colombia'
    administracion VARCHAR(255),
    objeto TEXT,
    importe DECIMAL(15, 2),
    fecha_adjudicacion DATE,
    estado VARCHAR(50),
    fuente VARCHAR(100), -- 'BOE', 'SECOP', etc
    datos_raw JSONB,
    creado_en TIMESTAMP DEFAULT NOW()
);

-- Análisis de Impacto
CREATE TABLE impacts (
    id SERIAL PRIMARY KEY,
    contrato_id INTEGER REFERENCES contracts(id),
    señales_positivas TEXT[],
    señales_negativas TEXT[],
    cambio_valor DECIMAL(5, 2),
    conclusión VARCHAR(50), -- 'mejoró', 'empeoró', 'neutral'
    confianza INTEGER,
    analizado_en TIMESTAMP DEFAULT NOW()
);

-- Sentencias
CREATE TABLE judgments (
    id SERIAL PRIMARY KEY,
    contrato_id INTEGER REFERENCES contracts(id),
    numero_sentencia VARCHAR(100),
    tribunal VARCHAR(255),
    fecha_sentencia DATE,
    fallo TEXT,
    impacto_contrato TEXT,
    jurisdiccion VARCHAR(50),
    datos_raw JSONB,
    creado_en TIMESTAMP DEFAULT NOW()
);

-- Sugerencias de Código
CREATE TABLE code_reviews (
    id SERIAL PRIMARY KEY,
    archivo_path VARCHAR(255),
    severidad VARCHAR(20),
    problema TEXT,
    sugerencia TEXT,
    codigo_mejorado TEXT,
    tiempo_estimado INTEGER,
    creado_en TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_contracts_pais ON contracts(pais);
CREATE INDEX idx_contracts_fecha ON contracts(fecha_adjudicacion);
CREATE INDEX idx_impacts_contrato ON impacts(contrato_id);
CREATE INDEX idx_judgments_contrato ON judgments(contrato_id);
