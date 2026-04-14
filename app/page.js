// app/page.js
'use client';

import { useState } from 'react';
import { signIn } from 'next-auth/react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    const res = await signIn('credentials', {
      email,
      password,
      redirect: false, // Manejamos la redirección manualmente
    });
    if (res?.ok) {
        window.location.href = '/dashboard'; 
    } else {
        setError(res.error.message);
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
          <button type="submit" className="btn-primary" >Entrar</button>
        </form>
        <p>¿No tienes cuenta? <a href="/register">Regístrate aquí</a></p>
      </div>
    </div>
  );
}
