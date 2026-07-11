/*
Una visión de Humberto Gonzalez Tigreros
Potenciado por Git y Copilot.
*/


'use client'; // Indica que este componente tiene interacción (botones, inputs)

import { useState } from 'react';
import { useRouter } from 'next/navigation';


export default function RegisterPage() {
    // 1. Estado: Aquí guardamos lo que el usuario escribe
    const [formData, setFormData] = useState({
        identificacion:'',
        nombre:'',
        email: '',
        password: '',
        confPassword: ''
    });
    const [mensaje, setMensaje] = useState({ texto: '', tipo: '' });
    const [enviando, setEnviando] = useState(false);
    const router = useRouter();

    // 2. Función de manejo de cambios (Meticulosa y limpia)
    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
        if (name==='nombre') validaRegExpNombre();
    };

    const handleChangeNameOrId = (e) => {
        const { etiqueta, valor } = e.target;
        setFormData(prev => ({ ...prev, [etiqueta]: valor.toLowerCase() }));
    };

    const handleChangeName = (e) => {
        const { etiqueta, valor } = e.target;
        validaRegExpName();
        setFormData(prev => ({ ...prev, [etiqueta]: valor.toLowerCase() }));
    };
    
    //2 validaciones de regExp para password, una particionada que hizo la curva y la otra condensada pero bastante nutriente.
    const ValidaRegExpPasswordPrecisa = () => {
       const regExpIni = /^(?=.*[A-Za-z])/;
       const regExpEsp = /(?=.*[~`|•√π÷×§∆£¢€¥^°={}\\%[\]<>@#$_&-+()/*"':;!?,.])/;
       const regExpMin = /(?=.*[a-z])/;
       const regExpMay = /(?=.*[A-Z])/;
       const regExpTamano = /.*{8,15}$/;
       const regExpCorreo = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}$/;
       
       
       if (!regExpIni.test(formData.password)){setMensaje({texto:'Contraseña debe iniciar con letra no especial', tipo:'validationError'}; return false;}
       if (!regExpEsp.test(formData.password)){setMensaje({texto:'Contraseña debe tener 1 caracter especial, no letra especial', tipo:'validationError'}; return false;}
       if (!regExpMin.test(formData.password)){setMensaje({texto:'Contraseña debe tener 1 minúscula', tipo:'validationError'}; return false;}
       if (!regExpMay.test(formData.password)){setMensaje({texto:'Contraseña debe tener 1 mayúscula', tipo:'validationError'}; return false;}
       if (!regExpTamano.test(formData.password)){setMensaje({texto:'Contraseña debe tener de 8 a 15 caracteres', tipo:'validationError'}; return false;}
       if (formData.password!==formData.confPassword){setMensaje({texto:'Debe ser igual la confirmacion del password.', tipo:'validationError'}); return false;}
       if (regExpCorreo.test(formData.correo){setMensaje({texto:'Correo debe tener formato de correo', tipo:'validationError'}); return false;}
        
       return true;
    };

    const validaRegExpPassword = () => {
       const regExpPassword = /^(?=[A-Z])(?=.*[a-z])(?=.*[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?`~])[A-Za-z0-9!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?`~]{8,15}$/;
       if (regExpPassword.test(formData.password){setMensaje({texto:'Debe tener al menos 1 caracter especial, no letras especiales y de 8 a 15 caracteres.', tipo: 'validationError'}); return false;}
       if (regExpCorreo.test(formData.correo){setMensaje({texto:'Correo debe tener formato de correo', tipo:'validationError'}); return false;}
      
       return true;
    }

    const validaRegExpNombre = () => {
        const regExpNombre = /^[A-Za-z]+(?:\s[A-Za-z]+)*$/;
        if (regExpNombre.test(formData.nombre)){setMensaje({texto:'Nombres debe ser en letras no especiales y separados por sólo 1 espacio.', tipo: 'validationError'}); return false;}    
    }

    const validaRegExpCorreo = () => {
        const regExpCorreo = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}$/;
        if (regExpCorreo.test(formData.email)){setMensaje({texto:'Correo debe tener formato xxx@yyy.zz', tipo: 'validationError'}); return false;}    
    }

    const validaRegExpId = () => {
        const regExpNie = /^[A-Za-z]([0-9]{7})[A-Za-z]$/;
        if (regExpNombre.test(formData.identificacion)){setMensaje({texto:'Nie', tipo: 'validationError'}); return false;}    
    }

    

        
    
    // 3. El envío al servidor (Conectividad)
    const handleSubmit = async (e) => {
        e.preventDefault(); // Evita que la página se recargue (comportamiento por defecto del DOM)
        setEnviando(true);

        try {
            const response = await fetch("/api/auth/register", { // Ruta interna de Next.js
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            const data = await response.json(); //response.body desde el flujo TCP es op asincrona.
            //Sin el await almacena objeto Promise {<pending>} en lugar de datos reales.
            setMensaje({ texto: data.message, tipo: response.ok ? 'success' : 'error' });
            if (response.ok) setTimeout(() => router.push('/'), 3000);
        } catch (error) {
            setMensaje({ texto:error.message, tipo: 'error' });
        } finally {
            setEnviando(false);
        }
    };

    return (
        <div className="fullPage">
            <form className="card" onSubmit={handleSubmit}>
                <h1>Crea tu cuenta</h1>
                <input 
                    name="tipoId"
                    type="check"
                <input 
                    name="identificacion" //Al usar name="identificacion", la función handleChange sabe exactamente qué parte del "Estado" actualizar.
                    type="text" 
                    placeholder="DNI, NIE o Pasaporte" 
                    onChange=()=>{handleChangeName()} 
                    className="auth-input"
                />
                <input 
                    name="nombre" //la función handleChange sabe exactamente qué parte del "Estado" actualizar.
                    type="text" 
                    placeholder="Nombre completo" 
                    onChange={handleChangeNameOrId} 
                    className="auth-input"
                />
                <input 
                    name="email" //la handleChange sabe exactamente qué parte del "Estado" actualizar.
                    type="email" 
                    placeholder="Email" 
                    onChange={handleChangeNameOrId} 
                    className="auth-input"
                />
                <input 
                    name="password" 
                    type="password" 
                    placeholder="Contraseña" 
                    onChange={handleChange} 
                    className="auth-input"
                />
                <input 
                    name="confPassword" 
                    type="password" 
                    placeholder="Confirmar Contraseña" 
                    onChange={handleChange} 
                    className="auth-input"
                />    
                <button type="submit" className="btn-primary" disabled={enviando}>
                    {enviando ? 'Cargando...' : 'Enviar'}
                </button>
                <p>{mensaje.texto} {mensaje.tipo}</p>
            </form>
        </div>
    );
}
