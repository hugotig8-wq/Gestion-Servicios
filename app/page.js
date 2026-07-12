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
  let validado=false;

  const handleChange = (e) => {
      const nuevoFormData = {...formData};
      const nuevoFormValidado = {...formValidado};
      if(e.target.name==='password'){
          nuevoFormData[e.target.name]=e.target.value;
          nuevoFormData['confPassword']=e.target.value;
          if(!validadores[e.target.name]) return;
          if(validadores[e.target.name](nuevoFormData).boolRegExp){setError('');nuevoFormValidado[e.target.name]=true; }
          else {setError(mensajesValidacion[e.target.name].texto); nuevoFormValidado[e.target.name]=false;}
          setFormData(nuevoFormData);
          setFormValidado(nuevoFormValidado);
      }
      if(e.target.name==='email'){
          nuevoFormData[e.target.name]=e.target.value.toLowerCase();
          if(!validadores[e.target.name]) return;
          if(validadores[e.target.name](nuevoFormData)){setError('');nuevoFormValidado[e.target.name]=true;}
          else {setError(mensajesValidacion[e.target.name].texto); nuevoFormValidado[e.target.name]=false;}
          setFormData(nuevoFormData);
          setFormValidado(nuevoFormValidado);
      }
      validado = Object.values(nuevoFormValidado).every(Boolean);

  };
  
  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    const res = await signIn('credentials', {
      email:formData['email'],
      password:formData['password'],
      redirect: false,// , obligada por comentario Manejamos la redirección manualmente
    });
    if (res?.ok) {
        window.location.href = '/dashboard'; 
    } else {
        setError(res?.error || 'No se pudo iniciar sesión');
    }    
  };
  validado = Object.values(formValidado).every(Boolean);
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
          <button type="submit" className="btn-primary" disabled=true >{validado? 'Entrar' : 'Error'}</button>
        </form>
        <p>¿No tienes cuenta? <a href="/register">Regístrate aquí</a></p>
      </div>
    </div>
  );
}
