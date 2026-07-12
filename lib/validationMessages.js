export const mensajesValidacion= {
  nombre: {texto:'Nombres debe ser en letras no especiales, vale ñ o Ñ y separados por sólo 1 espacio.', tipo: 'validationError'},
  apellidos: {texto:'Apellidos debe ser en letras no especiales, vale ñ o Ñ y separados por sólo 1 espacio.', tipo: 'validationError'},
  email: {texto:'Email debe tener formato xxx@yyy.zz sin espacios, subdominios o dominios deben iniciar y terminar en letra o numero pero pueden contener -, antes del @ hasta 63 y en total hasta 255', tipo: 'validationError'},
  password: {texto:'Password debe tener al menos 1 mayúscula, 1 minúscula, 1 caracter especial no letra especial, sin espacios y ser de 8 a 25 en total.', tipo: 'validationError'},
  confPassword: {texto:'Confirmación de contraseña debe ser igual a contraseña', tipo: 'validationError'},
  nie: {texto:'Nie es 1 letra seguido de 7 números y finaliza en 1 letra sin espacios.', tipo: 'validationError'},
  dni: {texto:'Dni debe tener 8 números y finalizar en 1 letra sin espacios', tipo: 'validationError'},
  pasaporte: {texto:'Pasaporte inicia en letra y tiene al menos 1 número después sin espacios y de 6 a 20 en total.', tipo: 'validationError'}
}


