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
        const { etiqueta, valor } = e.target;
        setFormData(prev => ({ ...prev, [etiqueta]: valor }));
    };

    const handleChangeNameOrId = (e) => {
        const { etiqueta, valor } = e.target;
        setFormData(prev => ({ ...prev, [etiqueta]: valor.toLowerCase() }));
    };
    
    //2 validaciones de regExp para password, una particionada que hizo la curva y la otra condensada pero bastante nutriente.
    const ValidaRegExpPassword = () => {
       const regExpIni = /^[A-Z]/;
       const regExpEsp = /[~`|•√π÷×§∆£¢€¥^°={}\\%[\]<>@#$_&-+()/*"':;!?,.]/;
       const regExpMin = /[a-z]/;
       const regExpMay = /[A-Z]/;
       const regExpTamano = /.*{8,15}/;
       const regExpCorreo = /(?=[A-Z0-9a-z]+)[@]/; //Falta pulirlo
       //validar nombre, minimo 2 palabras sin caracteres especiales ni letras especiales.
       
       if (!regExpIni.test(formData.password)){setMensaje{texto:'Debe iniciar con mayúscula no especial', tipo:'validationError'}; return false;}
       if (!regExpEsp.test(formData.password)){setMensaje{texto:'Debe tener 1 caracter especial, no letra especial', tipo:'validationError'}; return false;}
       if (!regExpMin.test(formData.password)){setMensaje{texto:'Debe tener 1 minuscula', tipo:'validationError'}; return false;}
       if (!regExpMay.test(formData.password)){setMensaje{texto:'Debe tener 1 mayuscula', tipo:'validationError'}; return false;}
       if (!regExpTamano.test(formData.password)){setMensaje{texto:'Debe tener de 8 a 15 caracteres', tipo:'validationError'}; return false;}
       if (formData.password!==formData.confPassword){setMensaje{texto:'Debe ser igual la confirmacion del password.', tipo:'validationError'}; return false;}
       if (regExpCorreo.test(formData.correo){
        
       return true;
    };
    
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
                    name="identificacion" //Al usar name="identificacion", la función handleChange sabe exactamente qué parte del "Estado" actualizar.
                    type="text" 
                    placeholder="DNI, NIE o Pasaporte" 
                    onChange={handleChangeNameOrId} 
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
                    {enviando ? 'Cargando...' : validaRegExpPassword() ?  'Enviar' : 'Error validacion'}
                </button>
                <p>{mensaje.texto} {mensaje.tipo}</p>
            </form>
        </div>
    );
}
