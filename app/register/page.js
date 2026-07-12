    /*
Una visión de Humberto Gonzalez Tigreros
Potenciado por Git y Copilot.
*/


'use client'; // Indica que este componente tiene interacción (botones, inputs)

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { validaRegExpId, validaRegExpNombre, validaRegExpApellidos, validaRegExpCorreo, validaRegExpPassword, validaRegExpConfPassword } from "@/app/lib/validators";
import { mensajesValidacion } from "@/app/lib/validationMessages";

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
    let formValidado = Object.values(validForm).every(Boolean);
    
    // 2. Función de manejo de cambios (Meticulosa y limpia)
    const handleChange = (e) => {
        const { name, value } = e.target;
        //Hay que actualizar el formData haciendo un nuevoFormData con la actualizacion o trabajaría desactualizado
        const nuevoValor = ["tipoId","identificacion","nombre","apellidos","email"].includes(name) ? value.toLowerCase() : value;
        const nuevoFormData = {
            ...formData,
            [name]: nuevoValor
        };
        setFormData(nuevoFormData);
        let esValido = true;

        switch(name){
            case 'nombre': esValido = validaRegExpNombre(nuevoFormData.nombre); setMensaje(mensajesValidacion[name]);
            break;
            case 'apellidos': esValido = validaRegExpApellidos(nuevoFormData.apellidos); setMensaje(mensajesValidacion[name]);
            break;
            case 'email': esValido = validaRegExpCorreo(nuevoFormData.email); if (!esValido) setMensaje(mensajesValidacion[name]);
            break;
            case 'password': esValido = validaRegExpPassword(nuevoFormData.password); if(!esValido) setMensaje(mensajesValidacion[name]);
            break;
            case 'confPassword': esValido = validaRegExpConfPassword(nuevoFormData.password,nuevoFormData.confPassword); if (!esValido) setMensaje(mensajesValidacion[name]);
            break;
            case 'identificacion': esValido = validaRegExpId(nuevoFormData.tipoId,nuevoFormData.identificacion); if (!esValido) setMensaje(mensajesValidacion[nuevoFormData.tipoId]);
            break;
        }
        setValidForm(prev => ({...prev, [name]:esValido}));
        formValidado = Object.values(validForm).every(Boolean);
    
    };
    
    //2 validaciones de regExp para password, una particionada que hizo la curva y la otra condensada pero bastante nutriente.
    const ValidaRegExpPasswordPrecisa = () => {
       const regExpIni = /^(?=[A-Za-z])/;
       const regExpEsp = /(?=.*[~`|•√π÷×§∆£¢€¥^°={}\\%[\]<>@#$_&-+()/*"':;!?,.])/;
       const regExpMin = /(?=.*[a-z])/;
       const regExpMay = /(?=.*[A-Z])/;
       const regExpTamano = /^.{8,15}$/;// o /.{8,15}/
       
       if (!regExpIni.test(formData.password)){setMensaje({texto:'Contraseña debe iniciar con letra no especial', tipo:'validationError'}; setValidForm(prev => ({...prev, ['password']: false}));}
       if (!regExpMin.test(formData.password)){setMensaje({texto:'Contraseña debe tener 1 minúscula', tipo:'validationError'}; setValidForm(prev => ({...prev, ['password']: false}));}
       if (!regExpMay.test(formData.password)){setMensaje({texto:'Contraseña debe tener 1 mayúscula', tipo:'validationError'}; setValidForm(prev => ({...prev, ['password']: false}));}
       if (!regExpEsp.test(formData.password)){setMensaje({texto:'Contraseña debe tener 1 caracter especial, no letra especial', tipo:'validationError'}; setValidForm(prev => ({...prev, ['password']: false}));}
       if (!regExpTamano.test(formData.password)){setMensaje({texto:'Contraseña debe tener de 8 a 15 caracteres', tipo:'validationError'}; setValidForm(prev => ({...prev, ['password']: false}));} else {setValidForm(prev => ({...prev, ['password']:true}));}
       if (formData.password!==formData.confPassword){setMensaje({texto:'Debe ser igual la confirmacion del password.', tipo:'validationError'}); setValidForm(prev => ({...prev, ['confPassword']: false}));} else {setValidForm(prev => ({...prev, ['confPassword']:true}));}
        
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

                                                    
