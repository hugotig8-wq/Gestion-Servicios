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

    const validadores = {
        nombre: (data)=>validaRegExpNombre(data.nombre),

        apellidos: (data)=>validaRegExpApellidos(data.apellidos),

        email: (data)=>validaRegExpCorreo(data.email),

        password: (data)=>validaRegExpPassword(data.password),

        confPassword:(data)=>
            validaRegExpConfPassword(
                data.password,
                data.confPassword
            ),

        identificacion:(data)=>
            validaRegExpId(
                data.tipoId,
                data.identificacion
            )
    };
    
    const [mensaje, setMensaje] = useState({ texto: '', tipo: '' });
    const [enviando, setEnviando] = useState(false);
    
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
        const esValido = validadores[name](nuevoFormData);
        if(!esValido) {if(name==='identificacion'){setMensaje(mensajesValidacion[nuevoFormData.tipoId]); setValidForm(prev => ({...prev, [name]:false}))} else{setMensaje(mensajesValidacion[name]); setValidForm(prev => ({...prev, [name]:false}))} }
        else {setMensaje({texto:'', tipo:''}); setValidForm(prev => ({...prev, [name]:true}))}
                         
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
    
    const formValidado = Object.values(validForm).every(Boolean);
    
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

                                                    
