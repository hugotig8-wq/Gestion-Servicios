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
                setMensaje(obtenerMensaje('confPassword', nuevoFormData));
                nuevoFormData[name]=true;
                nuevoFormData['confPassword']= esValido.coincide;}
            else{setMensaje({texto:'', tipo:''});
                 nuevoFormData[name]= true;
                 nuevoFormData['confPassword']= esValido.coincide;
                }
        }else{ setMensaje(obtenerMensaje(name, nuevoFormData));
               nuevoFormData[name]=false;
               nuevoFormData['confPassword']= esValido.coincide;
        }
        console.log(formData);
        console.log(nuevoFormData);
        setValidForm(nuevoValidForm);
        setFormData(nuevoFormData);
        console.log(formData);
        condole.log(nuevoFormData);
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
