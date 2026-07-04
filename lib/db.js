import { Pool } from 'pg'; // Usamos 'pg', que es el equivalente a 'psycopg2' en Node.js

/*
const pool = new Pool({
  connectionString: process.env.DATABASE_URL, // Una sola cadena es más limpia
  ssl: { rejectUnauthorized: false }
});
*/
/*
BD un banco. Abrir y cerrar la puerta del banco para cada persona es lento. Un Pool mantiene a 10 cajeros
listos en sus puestos para atender a quien llegue de inmediato.
Se hace modulariza en otro archivo para no definirlo en cada archivo que se use. MANTENIBILIDAD.
*/
// lib/db.js

// Configurar SSL según el entorno
const sslConfig = process.env.NODE_ENV === 'production' 
  ? { rejectUnauthorized: true }
  : process.env.DB_SSL === 'true' 
    ? { rejectUnauthorized: false }
    : false;

const pool = new Pool({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  port: process.env.DB_PORT ? Number(process.env.DB_PORT) : 5432,
  ssl: sslConfig

});

let initPromise = null;

const initDB = async () => {
  // 1. Tabla de Usuarios
  const tableUsuarios = `
    CREATE TABLE IF NOT EXISTS usuarios (
      id SERIAL PRIMARY KEY,
      identificacion VARCHAR(20) UNIQUE NOT NULL,
      nombre VARCHAR(255) UNIQUE NOT NULL,
      email VARCHAR(255) UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );`;

  // 2. Tabla de Categorías (Catálogo maestro)
  const tableCategorias = `
    CREATE TABLE IF NOT EXISTS categorias (
      id SERIAL PRIMARY KEY,
      nombre VARCHAR(50) UNIQUE NOT NULL,
      icono VARCHAR(50) -- Para guardar el nombre de un icono si quieres
    );`;

  const tableDescripciones = `
    CREATE TABLE IF NOT EXISTS descripciones (
      descripciones_id SERIAL PRIMARY KEY,
      id_servicio INTEGER NOT NULL,
      id_categoria INTEGER REFERENCES categorias(id),
      descripcion1 TEXT NOT NULL,
      descripcion2 TEXT NOT NULL,
      descripcion3 TEXT NOT NULL UNIQUE,
      mas_detalles TEXT,
      id_contrato INTEGER NOT NULL
    );`;

  const tableContrato = `
    CREATE TABLE IF NOT EXISTS contratos (
      contrato_id INTEGER PRIMARY KEY,
      contrato_numero VARCHAR(100) UNIQUE NOT NULL,
      id_servicio INTEGER NOT NULL,
      id_categoria INTEGER REFERENCES categorias(id),
      descripcion_id INTEGER REFERENCES descripciones(descripciones_id),
      instalacion_id INTEGER,
      fecha_contratacion DATE NOT NULL,
      fecha_inicio_servicio DATE,
      fecha_fin_servicio DATE,
      s3_folder_path VARCHAR(255)
    );`;

  const tableRenovacion = `
    CREATE TABLE IF NOT EXISTS renovacion (
      renovacion_id SERIAL PRIMARY KEY,
      id_contrato INTEGER REFERENCES contratos(contrato_id) ON DELETE CASCADE,
      id_categoria INTEGER REFERENCES categorias(id),
      descripcion_id INTEGER REFERENCES descripciones(descripciones_id),
      fecha_inicio_renovacion DATE,
      fecha_fin_renovacion DATE,
      dynamo_id VARCHAR(255),
      s3_folder_path VARCHAR(255)
    );
    COMMENT ON COLUMN renovacion.dynamo_id IS 'ID de unión para buscar metadatos en DynamoDB';
    COMMENT ON COLUMN renovacion.s3_folder_path IS 'Ruta de la carpeta en S3 donde se guardan audios y scrapper JSON relacionados con esta renovacion';
  `;

  const tableInstalacion = `
    CREATE TABLE IF NOT EXISTS instalacion (
      instalacion_id SERIAL PRIMARY KEY,
      id_contrato INTEGER REFERENCES contratos(contrato_id) ON DELETE CASCADE,
      id_categoria INTEGER REFERENCES categorias(id),
      descripcion_id INTEGER REFERENCES descripciones(descripciones_id),
      fecha_instalacion DATE
    );`;

  // 3. Tabla de Servicios (Relacionada con ambos)
  const tableServicios = `
   CREATE TABLE IF NOT EXISTS servicios (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    categoria_id INTEGER REFERENCES categorias(id),
    empresa VARCHAR(100) NOT NULL,
    precio_mensual DECIMAL(10, 2),
    novedad BOOLEAN DEFAULT FALSE,
    nro_contrato VARCHAR(100) UNIQUE,
    contrato_id INTEGER REFERENCES contratos(contrato_id),
    descripciones_id INTEGER REFERENCES descripciones(descripciones_id),
    
    -- ESTOS SON LOS PUNTOS DE UNIÓN CON EL MUNDO NO-RELACIONAL --
    dynamo_id VARCHAR(255),
    s3_folder_path VARCHAR(255),

    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
  COMMENT ON COLUMN servicios.dynamo_id IS 'ID de unión para buscar metadatos en DynamoDB';
  COMMENT ON COLUMN servicios.s3_folder_path IS 'Ruta de la carpeta en S3 donde se guardan audios y scrapper JSON relacionados con este servicio';  
  `;

  try {
    await pool.query(tableUsuarios);
    await pool.query(tableCategorias);
    await pool.query(tableDescripciones);
    await pool.query(tableContrato);
    await pool.query(tableRenovacion);
    await pool.query(tableInstalacion);
    await pool.query(tableServicios);


    // 4. EL SEEDER: Insertar categorías base si la tabla está vacía
    const checkCats = await pool.query('SELECT COUNT(*) FROM categorias');
    if (parseInt(checkCats.rows[0].count) === 0) {
      const seedQuery = `
        INSERT INTO categorias (nombre) VALUES ('Seguro-Coche');
        INSERT INTO categorias (nombre) VALUES ('Seguro-Hogar');
        INSERT INTO categorias (nombre) VALUES ('Seguro-Dental');
        INSERT INTO categorias (nombre) VALUES ('Seguro-Vida');
        INSERT INTO categorias (nombre) VALUES ('Seguro-Particular');
        INSERT INTO categorias (nombre) VALUES ('Seguro-Salud');
        INSERT INTO categorias (nombre) VALUES ('Internet-Telefonia');
        INSERT INTO categorias (nombre) VALUES ('Suministros');
      `;
      await pool.query(seedQuery);
      console.log("🌱 Categorías iniciales sembradas.");
    }

    const checkUsuarios = await pool.query('SELECT COUNT(*) FROM usuarios');
    if (parseInt(checkUsuarios.rows[0].count) === 0) {
      const seedQuery = `
        INSERT INTO usuarios (nombre, identificacion, email, password_hash) VALUES 
        ('Ramon Garcia Lopez','x9999999l','Prueba1@gmail.com','Password_123');
        INSERT INTO usuarios (nombre, identificacion, email, password_hash) VALUES 
        ('Rafael Torres Garces','y8888888k','Prueba2@gmail.com','Password_123');
      `;
      await pool.query(seedQuery);
      console.log("🌱 Usuarios iniciales sembrado.");
    }

    const checkDescripciones = await pool.query('SELECT COUNT(*) FROM descripciones');
    if (parseInt(checkDescripciones.rows[0].count) === 0) {
      //La siguiente ya estaba insertada y tocó sacarla para npm run build
      /**/
      const seedQuery = `INSERT INTO descripciones (descripciones_id, id_servicio, id_categoria, descripcion1, descripcion2, descripcion3, mas_detalles, id_contrato) 
          VALUES (1, 1, 1, 'Dacia Sandero Stepway', 'Terceros Ampliado km 0', 'VVV111', 'Con cheque Amazon de 50 euros.', 1);
        INSERT INTO descripciones (descripciones_id, id_servicio, id_categoria, descripcion1, descripcion2, descripcion3, mas_detalles, id_contrato) 
          VALUES (2, 2, 3, 'Dental Plus', 'Reconstruccion gratis', 'Sanitas1234', 'Con blanqueamiento gratis.', 2);
        INSERT INTO descripciones (descripciones_id, id_servicio, id_categoria, descripcion1, descripcion2, descripcion3, mas_detalles, id_contrato)
          VALUES (3, 3, 1, 'Range Rover Evoque HSE Dynamic', 'Terceros basico limite 150 km', 'RR111VVV', 'Con cheque Amazon de 100 euros.', 3);
        INSERT INTO descripciones (descripciones_id, id_servicio, id_categoria, descripcion1, descripcion2, descripcion3, mas_detalles, id_contrato)
          VALUES (4, 4, 7, 'Fibra 300MB Sin permanencia', 'Calle Ochoa 5, 3,2', 'Router12345', 'Con router gratis.', 4);
        INSERT INTO descripciones (descripciones_id, id_servicio, id_categoria, descripcion1, descripcion2, descripcion3, mas_detalles, id_contrato)
          VALUES (5, 5, 8, 'Electricidad', 'Calle Maria 6, 15,b', 'Luz12345', 'Con 3 meses gratis.', 5);
        INSERT INTO descripciones (descripciones_id, id_servicio, id_categoria, descripcion1, descripcion2, descripcion3, mas_detalles, id_contrato)
          VALUES (6, 6, 8, 'Gas Natural', 'Calle Luz 7, 6,b', 'Gas12345', 'Con 3 meses gratis.', 6);
        INSERT INTO descripciones (descripciones_id, id_servicio, id_categoria, descripcion1, descripcion2, descripcion3, mas_detalles, id_contrato)
          VALUES (7, 7, 7, 'Fibra 500MB + 2 L.Moviles inf GB. Sin permanencia', 'Calle Arosa 15, 13,2', 'Router12346', 'Con router gratis.', 7);
        INSERT INTO descripciones (descripciones_id, id_servicio, id_categoria, descripcion1, descripcion2, descripcion3, mas_detalles, id_contrato)
          VALUES (8, 8, 1, 'BMW Serie 3 Touring', 'Terceros ampliado kilometro cero', 'YYY000', 'Con asistencia en carretera gratis.', 8);
        INSERT INTO descripciones (descripciones_id, id_servicio, id_categoria, descripcion1, descripcion2, descripcion3, mas_detalles, id_contrato)
          VALUES (9, 9, 1, 'Mazda CX-5', 'Todo riesgo con franquicia 250', 'ZZZ111', 'Con cheque Amazon de 50 euros.', 9);
      `;
      await pool.query(seedQuery);
      console.log("🌱 descripciones iniciales sembradas.");
    }

    const checkContratos = await pool.query('SELECT COUNT(*) FROM contratos');
    if (parseInt(checkContratos.rows[0].count) === 0) {
      const seedQuery = `
        INSERT INTO contratos (contrato_id, contrato_numero, id_servicio, id_categoria, descripcion_id, instalacion_id, fecha_contratacion, fecha_inicio_servicio, fecha_fin_servicio, s3_folder_path) VALUES 
        (1, 'CONTRATO-001', 1, 1, 1, null, '2024-10-10', '2025-01-01', '2026-01-01', null),
        (2, 'CONTRATO-002', 2, 3, 2, null, '2026-01-01', '2026-02-01', '2027-02-01', null),
        (3, 'CONTRATO-003', 3, 1, 3, null, '2026-02-02', '2026-03-01', '2027-03-01', null),
        (4, 'CONTRATO-004', 4, 7, 4, 1, '2026-03-03', '2026-04-01', '2027-04-01', null),
        (5, 'CONTRATO-005', 5, 8, 5, 2, '2025-04-04', '2025-05-01', '2026-05-01', null),
        (6, 'CONTRATO-006', 6, 8, 6, 3, '2025-05-05', '2025-06-01', '2026-06-01', null),
        (7, 'CONTRATO-007', 7, 7, 7, 4, '2025-06-06', '2025-07-01', '2026-07-01', null),
        (8, 'CONTRATO-008', 8, 1, 8, null, '2025-07-07', '2025-08-01', '2026-08-01', null),
        (9, 'CONTRATO-009', 9, 1, 9, null, '2025-01-01', '2025-02-02', '2026-02-02', null);
      `;
      await pool.query(seedQuery);
      console.log("🌱 contratos iniciales sembrados.");
    }

    const checkServicios = await pool.query('SELECT COUNT(*) FROM servicios');
    if (parseInt(checkServicios.rows[0].count) === 0) {
      const seedQuery = `
        INSERT INTO servicios (user_id, categoria_id, empresa, precio_mensual, novedad, nro_contrato, descripciones_id, contrato_id) VALUES 
        (1, 1, 'Mapfre', 100.00, true, 'CONTRATO-001', 1, 1);
        INSERT INTO servicios (user_id, categoria_id, empresa, precio_mensual, novedad, nro_contrato, descripciones_id, contrato_id) VALUES
        (1, 3, 'Sanitas', 30.00, false, 'CONTRATO-002', 2, 2);
        INSERT INTO servicios (user_id, categoria_id, empresa, precio_mensual, novedad, nro_contrato, descripciones_id, contrato_id) VALUES
        (1, 1, 'Mapfre', 130.00, true, 'CONTRATO-003', 3, 3);
        INSERT INTO servicios (user_id, categoria_id, empresa, precio_mensual, novedad, nro_contrato, descripciones_id, contrato_id) VALUES
        (1, 7, 'Yoigo', 33.50, false, 'CONTRATO-004', 4, 4);
        INSERT INTO servicios (user_id, categoria_id, empresa, precio_mensual, novedad, nro_contrato, descripciones_id, contrato_id) VALUES
        (2, 8, 'Iberdrola', 60.00, false, 'CONTRATO-005', 5, 5);
        INSERT INTO servicios (user_id, categoria_id, empresa, precio_mensual, novedad, nro_contrato, descripciones_id, contrato_id) VALUES
        (2, 8, 'Baxi', 40.00, false, 'CONTRATO-006', 6, 6);
        INSERT INTO servicios (user_id, categoria_id, empresa, precio_mensual, novedad, nro_contrato, descripciones_id, contrato_id) VALUES
        (2, 7, 'Vodafone', 55.00, true, 'CONTRATO-007', 7, 7);
        INSERT INTO servicios (user_id, categoria_id, empresa, precio_mensual, novedad, nro_contrato, descripciones_id, contrato_id) VALUES
        (2, 1, 'Verti', 260.00, true, 'CONTRATO-008', 8, 8);
        INSERT INTO servicios (user_id, categoria_id, empresa, precio_mensual, novedad, nro_contrato, descripciones_id, contrato_id) VALUES
        (2, 1, 'Verti', 360.00, false, 'CONTRATO-009', 9, 9);
      `;
      await pool.query(seedQuery);
      console.log("🌱 Servicios contratados iniciales sembrados.");
    }

    const checkRenovaciones = await pool.query('SELECT COUNT(*) FROM renovacion');
    if (parseInt(checkRenovaciones.rows[0].count) === 0) {
      const seedQuery = `
        INSERT INTO renovacion (id_contrato, id_categoria, descripcion_id, fecha_inicio_renovacion, fecha_fin_renovacion, dynamo_id, s3_folder_path) VALUES
        (1, 1, 1, '2026-01-01', '2027-01-01', 'null', 'null'),
        (9, 1, 9, '2026-02-02', '2027-02-02', 'null', 'null');
      `;
      await pool.query(seedQuery);
      console.log("🌱 Renovaciones iniciales sembradas.");
    }

    const checkInstalaciones = await pool.query('SELECT COUNT(*) FROM instalacion');
    if (parseInt(checkInstalaciones.rows[0].count) === 0) {
      const seedQuery = `
        INSERT INTO instalacion (instalacion_id,  id_contrato, id_categoria, descripcion_id, fecha_instalacion) VALUES
        (1, 4, 7, 4, '2026-03-13'),
        (2, 5, 8, 5, '2025-04-14'),
        (3, 6, 8, 6, '2025-05-15'),
        (4, 7, 7, 7, '2025-06-16');
      `;
      await pool.query(seedQuery);
      console.log("🌱 Instalaciones iniciales sembradas.");
    }

    console.log("✅ Arquitectura de 7 tablas lista.");
  } catch (err) {
    console.error("❌ Error en initDB:", err);
    throw err;
  }
};

export { initDB };

const ensureDBInitialized = async () => {
  if (!initPromise) {
    initPromise = initDB().catch((err) => {
      initPromise = null;
      throw err;
    });
  }

  return initPromise;
};

export const query = async (text, params) => {
  await ensureDBInitialized();
  return pool.query(text, params);
};
