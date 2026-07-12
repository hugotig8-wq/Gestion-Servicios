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
                ? value.toLowerCase()
                : value;

        const nuevoFormData = {
            ...formData,
            [name]: nuevoValor
        };

        setFormData(nuevoFormData);

        if (!validadores[name]) return;

        const nuevoValidForm = {
            ...validForm
        };

        nuevoValidForm[name] = validadores[name](nuevoFormData);

        const esValido= nuevoValidForm[name];
        if(esValido && typeOf(esValido)==='boolean') {setMensaje({texto:'', tipo:''}}
        else if (typeOf(esValido)==='boolean'){setMensaje(obtenerMensaje(name,nuevoFormData))}
        else if (esValido.boolRegExp){
            setMensaje({texto:'', tipo:''});
            if(!esValido.coincide){setMessage(obtenerMensaje('confPassword', nuevoFormData)); nuevoFormData[name]=true}
            else{setMessage({texto:'', tipo:''}); nuevoFormData[name]= true}
        }else{ setMessage(obtenerMensaje(name, nuevoFormData)); nuevoFormData[name]=false}
        
        if(typeOf(esValido)!=='boolean') nuevoFormData['confPassword']= esValido.coincide;
        setValidForm(nuevoValidForm);
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
