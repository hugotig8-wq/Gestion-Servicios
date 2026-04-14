// app/api/auth/login/route.js
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/app/api/auth/[...nextauth]/options"; // Importa tus opciones
import { NextResponse } from 'next/server';
//import { query } from '@/lib/db';
import { cookies } from 'next/headers';

export async function GET() {
  const { query } = await import("@/lib/db.js");
  // getServerSession valida la cookie 'next-auth.session-token' automáticamente
  const session = await getServerSession(authOptions);

  if (!session) {
    return NextResponse.json({ message: "No autorizado GET" }, { status: 401 });
  }

  // El ID viene del JWT que configuramos en los callbacks de NextAuth
  const userId = session.user.id;

  const result = await query(`'SELECT * FROM servicios WHERE user_id = $1;'`, [userId]);
  return NextResponse.json({ data: result.rows });
}

export async function POST(request) {
  try {
    const { query } = await import("@/lib/db.js");
    //const { email, password } = await request.json();

    // getServerSession valida la cookie 'next-auth.session-token' automáticamente
    const session = await getServerSession(authOptions);

    if (!session) {
    return NextResponse.json({ message: "No autorizado POST" }, { status: 401 });
    }
    const userId = session.user.id; // El ID del usuario autenticado
    const email = session.user.email; // El email del usuario autenticado
    const password = session.user.password; // El password del usuario autenticado (en texto plano por ahora, no recomendado para producción)

    // 1. Validación de entrada
    if (!email || !password) {
      return NextResponse.json({ message: "Credenciales incompletas" }, { status: 400 });
    }

    // 2. Buscamos al usuario en la base de datos
    // Nota: Traemos el password_hash para comparar
    const sql = `'SELECT id, nombre, email, password_hash FROM usuarios WHERE email = $1;'`;
    const result2 = await query(sql, [email]);

    // 3. ¿Existe el usuario?
    if (result.rows.length === 0) {
      return NextResponse.json({ message: "Usuario no encontrado" }, { status: 401 });
    }

    const user = result2.rows[0];

    // 4. Verificación de contraseña
    // IMPORTANTE: En producción usarías 'bcrypt.compare'. 
    // Por ahora, comparamos texto plano para que pruebes tu Free Tier rápido.
    if (user.password_hash !== password) {
      return NextResponse.json({ message: "Contraseña incorrecta" }, { status: 401 });
    }

    const result3 = await query(`'SELECT * FROM servicios WHERE user_id = $1;'`, [userId]);
    return NextResponse.json({ data: result3.rows });

  } catch (error) {
    console.error("LOGIN_ERROR:", error);
    return NextResponse.json({ message: "Error en el servidor" }, { status: 500 });
  }
}