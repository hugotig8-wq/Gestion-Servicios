// app/page.js
'use client';

import { useState } from 'react';
import { signIn } from 'next-auth/react';
import { validaRegExpCorreo, validadores } from "@/lib/validators";
import { mensajesValidacion } from "@/lib/validationMessages";

export default function LoginPage() {
  const [formData, setFormData] = useState({email:'', password:'', confPassword:''});
  const [error, setError] = useState('');
  const [formValidado, setFormValidado] = useState({email:false, password:false});


  const handleChange = (e) => {
      const nuevoFormData = {...formData};
      const nuevoFormValidado = {...formValidado};
      if(e.target.name==='password'){
          nuevoFormData[e.target.name]=e.target.value;
          nuevoFormData['confPassword']=e.target.value;
          setFormData(nuevoFormData);
          if(validadores[e.target.name]) return;
          if(validadores[e.target.name](nuevoFormData)){setError('');nuevoFormValidado[e.target.name]=true;}
          else {setError(mensajesValidacion[e.target.name]); nuevoFormValidado[e.target.name]=false;}
          setFormValidado(nuevoFormValidado);
      }
      if(e.target.name==='email'){
          nuevoFormData[e.target.name]=e.target.value.toLowerCase();
          setFormData(nuevoFormData);
          if(validadores[e.target.name]) return;
          if(validadores[e.target.name](nuevoFormData)){setError('');nuevoFormValidado[e.target.value]=true;}
          else {setError(mensajesValidacion[e.target.name]); nuevoFormValidado[e.target.name]=false;}
          setFormValidado(nuevoFormValidado);
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
  const validado = Object.values(formValidado).every(Boolean);
  return (
    <div className='fullPage'>
      <div className='card'>
        <h1>GESTSEGUROS</h1>
        <form className="formLogin" onSubmit={handleLogin}>
          <input
            name="email"
            type="email" 
            placeholder="Email" 
            value={formData.email}
            onChange={handleChange}
            className="auth-input"
          />
          <input
            name="password"
            type="password" 
            placeholder="Contraseña" 
            value={formData.password}
            onChange={handleChange}
            className="auth-input"
          />
          {error && <p className="error-text">{error}</p>}
          <button type="submit" className="btn-primary" disabled={validado} >{validado? 'Entrar' : 'Error'}</button>
        </form>
        <p>¿No tienes cuenta? <a href="/register">Regístrate aquí</a></p>
      </div>
    </div>
  );
}
