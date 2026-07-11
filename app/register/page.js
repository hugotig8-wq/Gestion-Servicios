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

    const validadores = {
    nombre: validaRegExpNombre,
    apellidos: validaRegExpApellidos,
    email: validaRegExpCorreo,
    password: validaRegExpPassword,
    identificacion: validaRegExpId,
    confPassword: validaRegExpConfPassword
    };

    const [mensaje, setMensaje] = useState({ texto: '', tipo: '' });
    const [enviando, setEnviando] = useState(false);
    const [formValidado,setFormValidado] = useState(false);
    
    // 2. Función de manejo de cambios (Meticulosa y limpia)
    const handleChange1 = (e) => {
        const { name, value } = e.target;
        if (name==='tipoId') {setFormData(prev => ({ ...prev, [name]: value.toLowerCase() }));}
        else if (name==='identificacion') {setFormData(prev => ({ ...prev, [name]: value.toLowerCase() }));validaRegExpId1()}
        else if (name==='nombre'){setFormData(prev => ({ ...prev, [name]: value.toLowerCase() }));validaRegExpNombre1();}
        else if (name==='apellidos'){setFormData(prev => ({ ...prev, [name]: value.toLowerCase() }));validaRegExpApellidos1();}
        else if (name==='email') {setFormData(prev => ({ ...prev, [name]: value.toLowerCase() }));validaRegExpCorreo1();}
        else if (name==='password') {setFormData(prev => ({ ...prev, [name]: value }));validaRegExpPassword1();}
        else if (name==='confPassword') {setFormData(prev => ({ ...prev, [name]: value }));validaRegExpConfPassword1();}
       
        if (validForm['tipoId']&& validForm['identificacion']&&validForm['nombre']&& validForm['apellidos']&& validForm['email']&& validForm['password']&& validForm['confPassword']){setFormValidado(true);}
    };

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
            case 'nombre': esValido = validaRegExpNombre(nuevoFormData.nombre); setMensaje({texto:'Nombres debe ser en letras no especiales y separados por sólo 1 espacio.', tipo: 'validationError'});
            break;
            case 'apellidos': esValido = validaRegExpApellidos(nuevoFormData.apellidos); setMensaje({texto:'Apellidos debe ser en letras no especiales y separados por sólo 1 espacio.', tipo: 'validationError'});
            break;
            case 'email': esValido = validaRegExpCorreo(nuevoFormData.email); setMensaje({texto:'Correo debe tener formato xxx@yyy.zz sin espacios, subdominios o dominios deben iniciar y terminar en letra o numero pero pueden contener -', tipo: 'validationError'});
            break;
            case 'password': esValido = validaRegExpPassword(nuevoFormData.password); setMensaje({texto:'Debe tener al menos 1 mayúscula, 1 minúscula y al menos 1 caracter especial, no letras especiales y de 8 a 15 caracteres.', tipo: 'validationError'});
            break;
            case 'confPassword': esValido = validaRegExpConfPassword(nuevoFormData.confPassword); setMensaje({texto:'Confirmar contraseña debe ser igual contraseña.', tipo: 'validationError'});
            break;
            case 'identificacion': esValido = validaRegExpId(nuevoFormData.identificacion); 
                if(!esValido && nuevoFormData.tipoId==='nie'){ 
                    setMensaje({texto:'Nie es 1 letra (x, y ó z) seguido de 7 números y finaliza en 1 letra sin espacios.', tipo: 'validationError'});}
                else if (!esValido && nuevoFormData.tipoId==='dni') {
                    setMensaje({texto:'Dni es 8 numeros y finaliza en 1 letra sin espacios. Rellenar con 0 al inicio si 7 números', tipo: 'validationError'});}
                else if (!esValido && nuevoFormData.tipoId==='pasaporte'){ setMensaje({texto:'Pasaporte inicia en letra y tiene al menos 1 número después sin espacios', tipo: 'validationError'});}; 
            break;
        }
        setValidForm(prev => ({...prev, [name]:esValido}));
        
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
       if (!regExpMin.test(formData.password)){setMensaje({texto:'Contraseña debe tener 1 minúscula', tipo:'validationError'}; setValidForm(prev => ({...prev, ['password']: false}));}
       if (!regExpMay.test(formData.password)){setMensaje({texto:'Contraseña debe tener 1 mayúscula', tipo:'validationError'}; setValidForm(prev => ({...prev, ['password']: false}));}
       if (!regExpEsp.test(formData.password)){setMensaje({texto:'Contraseña debe tener 1 caracter especial, no letra especial', tipo:'validationError'}; setValidForm(prev => ({...prev, ['password']: false}));}
       if (!regExpTamano.test(formData.password)){setMensaje({texto:'Contraseña debe tener de 8 a 15 caracteres', tipo:'validationError'}; setValidForm(prev => ({...prev, ['password']: false}));} else {setValidForm(prev => ({...prev, ['password']:true}));}
       if (formData.password!==formData.confPassword){setMensaje({texto:'Debe ser igual la confirmacion del password.', tipo:'validationError'}); setValidForm(prev => ({...prev, ['confPassword']: false}));} else {setValidForm(prev => ({...prev, ['confPassword']:true}));}
        
    };

    const validaRegExpPassword1 = () => {
       const regExpPassword = /^(?=[A-Za-z])(?=.*[0-9])(?=.*[A-Z])(?=.*[a-z])(?=.*[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?`~])[A-Za-z0-9!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?`~]{8,15}$/;
       if (!regExpPassword.test(formData.password){setMensaje({texto:'Debe tener al menos 1 mayúscula, 1 minúscula y al menos 1 caracter especial, no letras especiales y de 8 a 15 caracteres.', tipo: 'validationError'}); setValidForm(prev => ({...prev, ['password']: false}));} else {setValidForm(prev => ({...prev, ['password']:true}));}
    }

    const validaRegExpPassword = (passw) => {
        const regExpPassword = /^(?=[A-Za-z])(?=.*[0-9])(?=.*[A-Z])(?=.*[a-z])(?=.*[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?`~])[A-Za-z0-9!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?`~]{8,15}$/;
        return regExpPassword.test(passw);
    }

    const validaRegExpConfPassword1 = () => {
       if (formData.password!==formData.confPassword){setMensaje({texto:'Confirmar contraseña debe ser igual contraseña.', tipo: 'validationError'}); setValidForm(prev => ({...prev, ['confPassword']: false}));} else {setValidForm(prev => ({...prev, ['confPassword']:true}));}
    }

    const validaRegExpConfPassword = () => {
       if (formData.password!==formData.confPassword){setMensaje({texto:'Confirmar contraseña debe ser igual contraseña.', tipo: 'validationError'}); setValidForm(prev => ({...prev, ['confPassword']: false})); return false} else {setValidForm(prev => ({...prev, ['confPassword']:true}));return true}
    }
       

    const validaRegExpNombre1 = () => {
        const regExpNombre = /^(?=.{1,20}$)[A-Za-zÑñ]+(?:\s[A-Za-zñÑ]+)*$/;
        if (!regExpNombre.test(formData.nombre)){setMensaje({texto:'Nombres debe ser en letras no especiales y separados por sólo 1 espacio.', tipo: 'validationError'}); setValidForm(prev => ({...prev, ['nombre']: false}));} else {setValidForm(prev => ({...prev, ['nombre']:true}));}
    }

    const validaRegExpNombre = (nombre) => {
        const regExpNombre = /^(?=.{1,20}$)[A-Za-zÑñ]+(?:\s[A-Za-zñÑ]+)*$/;
        return regExpNombre.test(nombre);
    }

    const validaRegExpApellidos1 = () => {
        const regExpApellidos = /^(?=.{1,40}$)[A-Za-zÑñ]+(?:\s[A-Za-zñÑ]+)*$/;
        if (!regExpApellidos.test(formData.apellidos)){setMensaje({texto:'Nombres debe ser en letras no especiales y separados por sólo 1 espacio.', tipo: 'validationError'}); setValidForm(prev => ({...prev, ['apellidos']: false}));} else {setValidForm(prev => ({...prev, ['apellidos']:true}));}  
    }

    const validaRegExpApellidos = (ap) => {
        const regExpApellidos = /^(?=.{1,40}$)[A-Za-zÑñ]+(?:\s[A-Za-zñÑ]+)*$/;
        return regExpApellidos.test(ap);
    }

    const validaRegExpCorreo1 = () => {
        const regExpCorreo = /^(?=.{3,254}$)(?=[^@]{1,64}@)[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
        if (!regExpCorreo.test(formData.email)){setMensaje({texto:'Correo debe tener formato xxx@yyy.zz sin espacios, subdominios o dominios deben iniciar y terminar en letra o numero pero pueden contener -', tipo: 'validationError'}); setValidForm(prev => ({...prev, ['email']: false}));} else {setValidForm(prev => ({...prev, ['email']:true}));}  
    }

    const validaRegExpCorreo = (email) => {
        const regExpCorreo = /^(?=.{3,254}$)(?=[^@]{1,64}@)[a-zA-A0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
        return regExpCorreo.test(email);
    }

    const validaRegExpNie1 = () => {
        const regExpNie = /^[XYZxyz][0-9]{7}[A-Za-z]$/;
        if (!regExpNie.test(formData.identificacion)){setMensaje({texto:'Nie es 1 letra seguido de 7 números y finaliza en 1 letra sin espacios.', tipo: 'validationError'}); setValidForm(prev => ({...prev, ['identificacion']: false}));} else {setValidForm(prev => ({...prev, ['identificacion']:true}));}  
    }

    const validaRegExpNie = (nie) => {
        const regExpNie = /^[XYZxyz][0-9]{7}[A-Za-z]$/;
        return regExpNie.test(nie);
    }

    const validaRegExpDni1 = () => {
        const regExpDni = /^[0-9]{8}[A-Za-z]$/;
        if (!regExpDni.test(formData.identificacion)){setMensaje({texto:'Dni debe tener 8 números y finalizar en 1 letra sin espacios', tipo: 'validationError'}); setValidForm(prev => ({...prev, ['identificacion']: false}));} else {setValidForm(prev => ({...prev, ['identificacion']:true}));}    
    }

    const validaRegExpDni = (dni) => {
        const regExpDni = /^[0-9]{8}[A-Za-z]$/;
        return regExpDni.test(dni);
    }

    const validaRegExpPasaporte1 = () => {
        const regExpPasaporte = /^[A-Za-z](?=.*\d)[A-Za-z0-9]{6,20}$/;
        if (!regExpPasaporte.test(formData.identificacion)){setMensaje({texto:'Pasaporte inicia en letra y tiene al menos 1 número después sin espacios', tipo: 'validationError'}); setValidForm(prev => ({...prev, ['identificacion']: false}));} else {setValidForm(prev => ({...prev, ['identificacion']:true}));}  
    }

    const validaRegExpPasaporte = (pas) => {
        const regExpPasaporte = /^[A-Za-z](?=.*\d)[A-Za-z0-9]{6,20}$/;
        return regExpPasaporte.test(pas);
    }

    const validaRegExpId1 = () => {
        if(formData.tipoId==='dni'){if(validaRegExpDni()){return true;}else{return false;}}
        else if(formData.tipoId==='nie'){if(validaRegExpNie()){return true;}else{return false;}}
        else if(formData.tipoId==='pasaporte'){if(validaRegExpPasaporte()){return true;}else{return false;}}
    }

    const validaRegExpId = (tipoId, id) => {
        if(tipoId==='dni'){if(validaRegExpDni(id)){return true;}else{return false;}}
        else if(tipoId==='nie'){if(validaRegExpNie(id)){return true;}else{return false;}}
        else if(tipoId==='pasaporte'){if(validaRegExpPasaporte(id)){return true;}else{return false;}}
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

                                                    
