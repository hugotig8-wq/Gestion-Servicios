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


// lib/db.js

const pool = new Pool({
  host: 'gestseguros-db.cklimqmymbi6.us-east-1.rds.amazonaws.com:5432',
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  port: 5432,
  ssl: { rejectUnauthorized: false }
});

const initDB = async () => {
  // 1. Tabla de Usuarios
  const tableUsuarios = `
    CREATE TABLE IF NOT EXISTS usuarios (
      id SERIAL PRIMARY KEY,
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

  // 3. Tabla de Servicios (Relacionada con ambos)
  const tableServicios = `
   CREATE TABLE IF NOT EXISTS servicios (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    categoria_id INTEGER REFERENCES categorias(id),
    empresa VARCHAR(100) NOT NULL,
    precio DECIMAL(10, 2),
    
    -- ESTOS SON LOS PUNTOS DE UNIÓN CON EL MUNDO NO-RELACIONAL --
    dynamo_id VARCHAR(255), -- ID para buscar en DynamoDB (audios/scrapper)
    s3_folder_path VARCHAR(255), -- Ruta de la carpeta en S3 para este servicio
    
    fecha_vencimiento DATE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
  `;

  try {
    await pool.query(tableUsuarios);
    await pool.query(tableCategorias);
    await pool.query(tableServicios);

    // 4. EL SEEDER: Insertar categorías base si la tabla está vacía
    const checkCats = await pool.query('SELECT COUNT(*) FROM categorias');
    if (parseInt(checkCats.rows[0].count) === 0) {
      const seedQuery = `
        INSERT INTO categorias (nombre) VALUES 
        ('Seguro-Coche'), ('Seguro-Hogar'), ('Salud'), ('Internet'), ('Suministros');
      `;
      await pool.query(seedQuery);
      console.log("🌱 Categorías iniciales sembradas.");
    }

    console.log("✅ Arquitectura de 3 tablas lista.");
  } catch (err) {
    console.error("❌ Error en initDB:", err);
  }
};

initDB();
export const query = (text, params) => pool.query(text, params);