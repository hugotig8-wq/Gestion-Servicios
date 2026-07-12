
export function validaRegExpPassword (passw){
        const regExpPassword = /^(?=[A-Za-z])(?=.*[0-9])(?=.*[A-Z])(?=.*[a-z])(?=.*[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?`~])[A-Za-z0-9!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?`~]{8,26}$/;
        return regExpPassword.test(passw);
    }

export function validaRegExpConfPassword(pass, conf) {
       return pass===conf;
    }

export function validaRegExpNombre(nombre){
        const regExpNombre = /^(?=.{1,20}$)[A-Za-zÑñ]+(?:\s[A-Za-zñÑ]+)*$/;
        return regExpNombre.test(nombre);
    }

export function validaRegExpApellidos(ap){
        const regExpApellidos = /^(?=.{1,40}$)[A-Za-zÑñ]+(?:\s[A-Za-zñÑ]+)*$/;
        return regExpApellidos.test(ap);
    }

export function validaRegExpCorreo(email){
        const regExpCorreo = /^(?=.{3,254}$)(?=[^@]{1,64}@)[a-zA-A0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
        return regExpCorreo.test(email);
    }

export function validaRegExpNie(nie){
        const regExpNie = /^[XYZxyz][0-9]{7}[A-Za-z]$/;
        return regExpNie.test(nie);
    }

export function validaRegExpDni(dni){
        const regExpDni = /^[0-9]{8}[A-Za-z]$/;
        return regExpDni.test(dni);
    }

export function validaRegExpPasaporte(pas){
        const regExpPasaporte = /^[A-Za-z](?=.*\d)[A-Za-z0-9]{6,20}$/;
        return regExpPasaporte.test(pas);
    }

export function validaRegExpId(tipoId, id){
        if(tipoId==='dni'){return(validaRegExpDni(id));}
        else if(tipoId==='nie'){return(validaRegExpNie(id))}
        else if(tipoId==='pasaporte'){return(validaRegExpPasaporte(id))}
        else {return false;}
    }
                                                                                                                                                                             }
