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
        tipoId:'dni',
        identificacion:'',
        nombre:'',
        apellidos:'',
        email: '',
        password: '',
        confPassword: ''
    });
    const [validForm, setValidForm] = useState({
        tipoId:true,
        identificacion:false,
        nombre:false,
        apellidos:false,
        email: false,
        password: false,
        confPassword: false
    });

    const [mensaje, setMensaje] = useState({ texto: '', tipo: '' });
    const [enviando, setEnviando] = useState(false);
    const [formValidado,setFormValidado] = useState(false);
    
    // 2. Función de manejo de cambios (Meticulosa y limpia)
    const handleChange = (e) => {
        const { name, value } = e.target;
        if (name==='identificacion') {setFormData(prev => ({ ...prev, [name]: value.toLowerCase() }));validaRegExpId()}
        if (name==='nombre'){setFormData(prev => ({ ...prev, [name]: value.toLowerCase() }));validaRegExpNombre();}
        if (name==='apellidos'){setFormData(prev => ({ ...prev, [name]: value.toLowerCase() }));validaRegExpApellidos();}
        if (name==='email') {setFormData(prev => ({ ...prev, [name]: value.toLowerCase() }));validaRegExpCorreo();}
        if (name==='tipoId') {setFormData(prev => ({ ...prev, [name]: value.toLowerCase() }));}
        if (name==='password') {setFormData(prev => ({ ...prev, [name]: value }));validaRegExpPassword();}
        if (name==='confPassword') {setFormData(prev => ({ ...prev, [name]: value }));validaRegExpConfPassword();}
       
       if (validForm['tipoId']&& validForm['identificacion']&&validForm['nombre']&& validForm['apellidos']&& validForm['email']&& validForm['password']&& validForm['confPassword']){setFormValidado(true);}
    };
    
    //2 validaciones de regExp para password, una particionada que hizo la curva y la otra condensada pero bastante nutriente.
    const ValidaRegExpPasswordPrecisa = () => {
       const regExpIni = /^(?=[A-Za-z])/;
       const regExpEsp = /(?=.*[~`|•√π÷×§∆£¢€¥^°={}\\%[\]<>@#$_&-+()/*"':;!?,.])/;
       const regExpMin = /(?=.*[a-z])/;
       const regExpMay = /(?=.*[A-Z])/;
       const regExpTamano = /^.{8,15}$/;// o /.{8,15}/
       
       if (!regExpIni.test(formData.password)){setMensaje({texto:'Contraseña debe iniciar con letra no especial', tipo:'validationError'}; setValidForm(prev => ({...prev, ['password']: false}));}
       if (!regExpEsp.test(formData.password)){setMensaje({texto:'Contraseña debe tener 1 caracter especial, no letra especial', tipo:'validationError'}; setValidForm(prev => ({...prev, ['password']: false}));}
       if (!regExpMin.test(formData.password)){setMensaje({texto:'Contraseña debe tener 1 minúscula', tipo:'validationError'}; setValidForm(prev => ({...prev, ['password']: false}));}
       if (!regExpMay.test(formData.password)){setMensaje({texto:'Contraseña debe tener 1 mayúscula', tipo:'validationError'}; setValidForm(prev => ({...prev, ['password']: false}));}
       if (!regExpTamano.test(formData.password)){setMensaje({texto:'Contraseña debe tener de 8 a 15 caracteres', tipo:'validationError'}; setValidForm(prev => ({...prev, ['password']: false}));}
       if (formData.password!==formData.confPassword){setMensaje({texto:'Debe ser igual la confirmacion del password.', tipo:'validationError'}); setValidForm(prev => ({...prev, ['confPassword']: false}));}
    };

    const validaRegExpPassword = () => {
       const regExpPassword = /^(?=[A-Za-z])(?=.*[0-9])(?=.*[A-Z])(?=.*[a-z])(?=.*[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?`~])[A-Za-z0-9!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?`~]{8,15}$/;
       if (!regExpPassword.test(formData.password){setMensaje({texto:'Debe tener al menos 1 caracter especial, no letras especiales y de 8 a 15 caracteres.', tipo: 'validationError'}); setValidForm(prev => ({...prev, ['password']: false}));}
    }

    const validaRegExpConfPassword = () => {
       if (formData.password!==formData.confPassword){setMensaje({texto:'Confirmar contraseña debe ser igual contraseña.', tipo: 'validationError'}); setValidForm(prev => ({...prev, ['confPassword']: false}));}
    }

    const validaRegExpNombre = () => {
        const regExpNombre = /^(?=.{1,20}$)[A-Za-zÑñ]+(?:\s[A-Za-zñÑ]+)*$/;
        if (!regExpNombre.test(formData.nombre)){setMensaje({texto:'Nombres debe ser en letras no especiales y separados por sólo 1 espacio.', tipo: 'validationError'}); setValidForm(prev => ({...prev, ['nombre']: false}));}   
    }

    const validaRegExpApellidos = () => {
        const regExpApellidos = /^(?=.{1,40}$)[A-Za-zÑñ]+(?:\s[A-Za-zñÑ]+)*$/;
        if (!regExpApellidos.test(formData.nombre)){setMensaje({texto:'Nombres debe ser en letras no especiales y separados por sólo 1 espacio.', tipo: 'validationError'}); setValidForm(prev => ({...prev, ['apellidos']: false}));}    
    }

    const validaRegExpCorreo = () => {
        const regExpCorreo = /^(?=.{3,254}$)(?=[^@]{1,64}@)[a-zA-A0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
        if (!regExpCorreo.test(formData.email)){setMensaje({texto:'Correo debe tener formato xxx@yyy.zz sin espacios, subdominios o dominios deben iniciar y terminar en letra o numero pero pueden contener -', tipo: 'validationError'}); setValidForm(prev => ({...prev, ['email']: false}));}    
    }

    const validaRegExpNie = () => {
        const regExpNie = /^[XYZxyz][0-9]{7}[A-Za-z]$/;
        if (!regExpNombre.test(formData.identificacion)){setMensaje({texto:'Nie es 1 letra seguido de 7 números y finaliza en 1 letra sin espacios.', tipo: 'validationError'}); setValidForm(prev => ({...prev, ['identificacion']: false}));}    
    }

    const validaRegExpDni = () => {
        const regExpDni = /^[0-9]{8}[A-Za-z]$/;
        if (!regExpDni.test(formData.identificacion)){setMensaje({texto:'Dni debe tener 8 números y finalizar en 1 letra sin espacios', tipo: 'validationError'}); setValidForm(prev => ({...prev, ['identificacion']: false}));}    
    }

    const validaRegExpPasaporte = () => {
        const regExpPasaporte = /^[A-Za-z](?=.*\d)[A-Za-z0-9]{6,20}$/;
        if (!regExpPasaporte.test(formData.identificacion)){setMensaje({texto:'Pasaporte inicia en letra y tiene al menos 1 número después sin espacios', tipo: 'validationError'}); setValidForm(prev => ({...prev, ['identificacion']: false}));}    
    }

    const validaRegExpId = () => {
        if(formData.tipoId==='dni'){validaRegExpDni();}
        if(formData.tipoId==='nie'){validaRegExpNie();}
        if(formData.tipoId==='pasaporte'){validaRegExpPasaporte();}
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
                <select
                    name="tipoId"
                    value={formData.tipoId}
                    onChange={handleChange}
                >
                    <option value="dni">DNI</option>
                    <option value="nie">NIE</option>
                    <option value="pasaporte">Pasaporte</option>
                </select>   
                <input 
                    name="identificacion" //Al usar name="identificacion", la función handleChange sabe exactamente qué parte del "Estado" actualizar.
                    type="text" 
                    placeholder="Identificación." 
                    onChange={handleChange} 
                    className="auth-input"
                />
                <input 
                    name="nombre" //la función handleChange sabe exactamente qué parte del "Estado" actualizar.
                    type="text" 
                    placeholder="Nombre completo" 
                    onChange={handleChange} 
                    className="auth-input"
                />
                <input 
                    name="apellidos" //la función handleChange sabe exactamente qué parte del "Estado" actualizar.
                    type="text" 
                    placeholder="Apellidos" 
                    onChange={handleChange} 
                    className="auth-input"
                />
                <input 
                    name="email" //la handleChange sabe exactamente qué parte del "Estado" actualizar.
                    type="email" 
                    placeholder="Email" 
                    onChange={handleChange} 
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
                <button type="submit" className="btn-primary" disabled={enviando||!formValidado}>
                    {enviando ? 'Cargando...' : formValidado ? 'Enviar': 'ValidError'}
                </button>
                <p>{mensaje.texto} {mensaje.tipo}</p>
            </form>
        </div>
    );
}

                                                    
