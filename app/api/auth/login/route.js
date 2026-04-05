// app/api/auth/login/route.js
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';

export async function POST(request) {
  try {
    const { email, password } = await request.json();

    // 1. Validación de entrada
    if (!email || !password) {
      return NextResponse.json({ message: "Credenciales incompletas" }, { status: 400 });
    }

    // 2. Buscamos al usuario en la base de datos
    // Nota: Traemos el password_hash para comparar
    const sql = 'SELECT id, email, password_hash FROM usuarios WHERE email = $1';
    const result = await query(sql, [email]);

    // 3. ¿Existe el usuario?
    if (result.rows.length === 0) {
      return NextResponse.json({ message: "Usuario no encontrado" }, { status: 401 });
    }

    const user = result.rows[0];

    // 4. Verificación de contraseña
    // IMPORTANTE: En producción usarías 'bcrypt.compare'. 
    // Por ahora, comparamos texto plano para que pruebes tu Free Tier rápido.
    if (user.password_hash !== password) {
      return NextResponse.json({ message: "Contraseña incorrecta" }, { status: 401 });
    }

    // 5. Respuesta de éxito
    // Aquí podrías crear una "Cookie" de sesión más adelante.
    return NextResponse.json({
      message: "¡Bienvenido de nuevo!",
      user: { id: user.id, email: user.email }
    }, { status: 200 });

  } catch (error) {
    console.error("LOGIN_ERROR:", error);
    return NextResponse.json({ message: "Error en el servidor" }, { status: 500 });
  }
}