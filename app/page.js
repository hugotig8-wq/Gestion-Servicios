// app/page.js
'use client';

import { useState } from 'react';
import { signIn } from 'next-auth/react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleChange = (e) => {
      if(e.target.name==='email'){
          setEmail(e.target.value.toLowerCase());
      }

  };
  
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
        setError(res?.error || 'No se pudo iniciar sesión');
    }    
  };

  return (
    <div className='fullPage'>
      <div className='card'>
        <h1>GESTSEGUROS</h1>
        <form className="formLogin" onSubmit={handleLogin}>
          <input
            name="email"
            type="email" 
            placeholder="Email" 
            value={email}
            onChange={handleChange}
            className="auth-input"
          />
          <input
            name="password"
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
