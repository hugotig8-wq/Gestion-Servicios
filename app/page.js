// app/page.js
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation'; // El navegador de Next.js
//import './styles.css';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (res.ok) {
        // ¡Éxito! Guardamos info básica y saltamos al Dashboard
        router.push('/dashboard');
      } else {
        setError(data.message);
        router.push('/dashboard')
      }
    } catch (err) {
      setError("Error de conexión");
      router.push('/dashboard')
    }
  };

  return (
    <div className='fullPage'>
      <div className='card'>
        <h1>GESTSEGUROS</h1>
        <form className="formLogin" onSubmit={handleLogin}>
          <input 
            type="email" 
            placeholder="Email" 
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="auth-input"
          />
          <input 
            type="password" 
            placeholder="Contraseña" 
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="auth-input"
          />
          {error && <p className="error-text">{error}</p>}
          <button type="submit" className="btn-primary">Entrar</button>
        </form>
        <p>¿No tienes cuenta? <a href="/register">Regístrate aquí</a></p>
      </div>
    </div>
  );
}