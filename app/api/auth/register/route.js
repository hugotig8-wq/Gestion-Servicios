/*
Una visión de Humberto Gonzalez Tigreros
Potenciado por Gemini, Cloude y Amazon Q.
Construye un Endpoint de API
Preferible a usar una lambda externa desde el navegador. Credenciales seguras en AWS, nunca van al navegador.
v1: FrontEnd y BackEnd bajo el mismo techo
*/

//import { query } from '@/lib/db'; // El @ apunta a la raíz del proyecto

import { NextResponse } from 'next/server';

// 2. Definimos la función POST (El verbo HTTP para enviar datos)
export async function POST(request) {
  try {
    // Extraemos los datos del "paquete" que envió el frontend
    const { query } = await import("@/lib/db.js");
    const body = await request.json();
    const {identificacion, nombre, email, password } = body;

    // Validación básica: El profesor dice "Nunca te fíes del usuario"
    if (!email || !password || !identificacion || !nombre) {
      return NextResponse.json(
        { message: "Identificacion, nombre, email y contraseña son obligatorios" }, 
        { status: 400 }
      );
    }

    // 3. Ejecutamos la consulta SQL
    const sql = 'INSERT INTO usuarios (identificacion, nombre, email, password_hash) VALUES ($1, $2, $3, $4) RETURNING id';
    //Prepared statements o consultas parametrizadas, evitan inyección sql. Se precompila la estructura.
    // a diferencia de concatenación de cadenas donde el motor interpreta el texto como un único comando
    // ejecutable, precompilar define un plan de acción antes de recibir los datos reales, los trata como
    // literales nunca como ejecutables. Molde definido e inalterable, valida tipos.
    const values = [identificacion, nombre, email, password];

    const result = await query(sql, values);

    // 4. Respondemos éxito
    return NextResponse.json({ 
      message: "Usuario registrado.", 
      id: result.rows[0].id 
    }, { status: 201 });

  } catch (error) {
    console.error("ERROR EN SERVIDOR DB:", error);
    
    // Manejo de errores específicos (ej: email duplicado)
    if (error.code === '23505') {
      return NextResponse.json({ message: "El correo ya está registrado" }, { status: 409 });
    }

    return NextResponse.json({ message:error.message }, { status: 500 });
  }
}
