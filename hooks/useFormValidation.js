'use client';

import { useState } from 'react';
import {
    validaRegExpId,
    validaRegExpNombre,
    validaRegExpApellidos,
    validaRegExpCorreo,
    validaRegExpPassword,
    validaRegExpConfPassword,
    validadores
} from '@/lib/validators';

import { mensajesValidacion } from '@/lib/validationMessages';

export function useFormValidation(initialData) {

    const [formData, setFormData] = useState(initialData);

    const [validForm, setValidForm] = useState({
        tipoId: true,
        identificacion: false,
        nombre: false,
        apellidos: false,
        email: false,
        password: false,
        confPassword: false
    });

    const [mensaje, setMensaje] = useState({
        texto: '',
        tipo: ''
    });

    const obtenerMensaje = (campo, data) => {

        if (campo === 'identificacion')
            return mensajesValidacion[data.tipoId];

        return mensajesValidacion[campo];
    };

    const handleChange = e => {

        const { name, value } = e.target;

        const nuevoValor =
            ['tipoId', 'identificacion', 'nombre', 'apellidos', 'email']
                .includes(name)
                ? value.toLowerCase().replace(/\s+/g, ' ');
                : value;

        const nuevoFormData = {
            ...formData,
            [name]: nuevoValor
        };

        if (!validadores[name]) return;

        const nuevoValidForm = {
            ...validForm
        };
        //Posiblemente falle en los validsdores al haber validaciones cruzados necesarias
        nuevoValidForm[name] = validadores[name](nuevoFormData);

        const esValido= nuevoValidForm[name];
        
        if(esValido && typeof(esValido)==='boolean') {setMensaje({texto:'', tipo:''})}
        else if (typeof(esValido)==='boolean'){setMensaje(obtenerMensaje(name,nuevoFormData))}
        else if (esValido.boolRegExp){
            //setMensaje({texto:'', tipo:''});
            if(!esValido.coincide){
                nuevoValidForm[name]=true;
                setMensaje(obtenerMensaje('confPassword', nuevoFormData));
                nuevoValidForm['confPassword']= false;}
            else{setMensaje({texto:'', tipo:''});
                 nuevoValidForm[name]=true;
                 nuevoValidForm['confPassword']= esValido.coincide;
                }
        }else{ setMensaje(obtenerMensaje(name, nuevoFormData));
               nuevoValidForm[name]=false;
               nuevoValidForm['confPassword']= esValido.coincide;
        }
        console.log(JSON.stringify(formData));
        console.log(JSON.stringify(nuevoFormData));
        setValidForm(nuevoValidForm);
        setFormData(nuevoFormData);
        console.log(JSON.stringify(formData));
        console.log(JSON.stringify(nuevoFormData));
    };

    const formValidado =
        Object.values(validForm).every(Boolean);

    return {

        formData,
        validForm,
        mensaje,
        setMensaje,
        formValidado,
        handleChange

    };

}
