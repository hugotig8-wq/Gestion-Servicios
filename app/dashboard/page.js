'use client';
import { useState, useEffect } from 'react';
//import { cookies } from 'next/headers';
import { useSession } from 'next-auth/react'; // Cambiado de cookies manuales

export default function Dashboard() {
  const { data: session, status } = useSession();
  const [servicios, setServicios] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [filterText, setFilterText] = useState('');
  const [inStockOnly, setInStockOnly] = useState(false);
  //const [userId, setUserId] = useState(null);
  //const userId = cookies().get('userId')?.value //No se puede en un use-cient
  //const sessionId = cookies().get('session-id')?.value
  // El "Vigilante" que trae los datos
  useEffect(() => {
    if (status=="authenticated"){
      const fetchServicios = async () => {
        try {
          // En una app real, el ID vendría de la sesión (cookie)
          /*if (sessionId) {await fetch('/api/servicios', {method: POST, headers: {'Content-Type':'application/json', 'X-Session-ID': sessionId} body: JSON.stringify({key: 'value'}) });}*/
          //const value = document.cookie.split('; ').find(row => row.startsWith('userId='))?.split('=')[1]; //NextAuth se encarga de enviar la cookie de sesión en cada fetch
          const res = await fetch('/api/servicios'); // Next enviará la cookie automáticamente
          const json = await res.json();
          if (res.ok) setServicios(json.data || []);
          /*setUserId(value);
          const response = await fetch("/api/servicios", { // Ruta interna de Next.js
                  method: 'GET',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify(formData)
              });
          const data = await response.json();
          setServicios(data);*/
        } catch (err) {
          console.error("Error cargando datos");
        } finally {
          setCargando(false);
        }
      };
      fetchServicios();
    }
  }, [status]); //Se dispara cuando el estado de la sesion cambia //Probar con vacío vacío, "", null, undefiined, 0.  

  if (status === "loading" || (status === "authenticated" && cargando)) {
    return <p>Cargando sesión y servicios...</p>;
  }
  
  if (status === "unauthenticated") {
    return <p>Acceso denegado. Por favor inicia sesión.</p>;
  }

  return (
  <div>
    <div id="loading-overlay" className={'hidden flex flex-wrap w-full justify-center fixed inset-0 gap-4 p-4 z-50 bg-opacity-50 backdrop-blur-sm'}>
      {/* DIV 1: Filtro por Nombre de Empresa (Mantenido) */}
      <div className="relative p-8 rounded-lg shadow-xl flex flex-col items-center">
        {/*<div id="loading-overlay" className="`${cargando ? 'hidden w-12 h-12 fixed inset-0 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin' : 'invisible'}`" >*/}
        <div className="w-12 md:w-24 lg:w-48 h-12 md:w-24 lg:h-48 border-4 hover:border-blue-200 border-t-blue-600 rounded-full animate-spin" > 
        </div>
        <p className="mt-4 text-gray-700 font-medium">Cargando tus servicios contratados desde AWS...</p>
      </div>
    </div>
    <div>
      <div className="p-4 bg-gray-100 flex justify-left">
        <p>Usuario: <strong>{session?.user?.email}</strong></p> 
        <button onClick={() => signOut()}>Cerrar Sesión</button>
      </div>
      
      <FilterableProductTable products={{ rows: servicios }} />
    </div>
  </div>
  );
}

function FilterableProductTable({ products }) {
  const [filterText, setFilterText] = useState('');
  const [inStockOnly, setInStockOnly] = useState(false);
  
  // Tu lógica de empresas única
  const empresas = [...new Set(products.rows.map(i => i.empresa))];
  const [seleccionEmpresas, setSeleccionEmpresas] = useState([...empresas].map(() => true));

  const [razonamiento, setRazonamiento] = useState('Da click sobre el nombre del seguro a analizar...');

  return (
    <div className='container'>
      {/* DIV 1: Lógica de selección de empresas */}
      <div className="sidebar">
        <h3>Compañías</h3>
        {empresas.map((emp, index) => (
          <label key={emp}>
            <input 
              type="checkbox" 
              checked={seleccionEmpresas[index]}
              onChange={() => {
                const newSelection = [...seleccionEmpresas];
                newSelection[index] = !newSelection[index];
                setSeleccionEmpresas(newSelection);
              }}
            /> {emp}
          </label>
        ))}
      </div>

      {/* DIV 2: SearchBar y ProductTable */}
      <div className="content">
        <h3>SERVICIOS POR CATEGORÍA</h3>
        <SearchBar 
          filterText={filterText} 
          inStockOnly={inStockOnly} 
          onFilterTextChange={setFilterText} 
          onInStockOnlyChange={setInStockOnly} 
        />
        <ProductTable 
          products={products} 
          filterText={filterText} 
          inStockOnly={inStockOnly}
          seleccionEmpresas={seleccionEmpresas}
          empresas={empresas}
          setRazonamiento={setRazonamiento}
        />
      </div>

      {/* DIV 3: Tercer div vacío (Reservado para futuro Analizar/Crawler) */}
      <div className="div-analisis">
        <h2>Análisis de Cloude haiku 4-5:</h2>
            <p>{razonamiento}</p>
      </div>
    </div>
  );
}

function SearchBar({ filterText, inStockOnly, onFilterTextChange, onInStockOnlyChange }) {
  return (
    <form className="search-form">
      <input 
        type="text" 
        value={filterText} 
        placeholder="Buscar..." 
        onChange={(e) => onFilterTextChange(e.target.value)} 
      />
      <label>
        <input 
          type="checkbox" 
          checked={inStockOnly} 
          onChange={(e) => onInStockOnlyChange(e.target.checked)} 
        />
        {' '} Solo mostrar novedades
      </label>
    </form>
  );
}

function ProductTable({ products, filterText, inStockOnly, seleccionEmpresas, empresas, setRazonamiento}) {
  const rows = [];
  let lastCategory = null;

  products.rows.forEach((product) => {
   if ((
      product.descripcion1.toLowerCase().indexOf(
        filterText.toLowerCase()
      ) === -1) && (product.descripcion2.toLowerCase().indexOf(
        filterText.toLowerCase()
      ) === -1) && (product.descripcion3.toLowerCase().indexOf(
        filterText.toLowerCase()
      ) === -1) && (product.categoria.toLowerCase().indexOf(
        filterText.toLowerCase()
      ) === -1) && (product.empresa.toLowerCase().indexOf(
        filterText.toLowerCase()
      ) === -1) && (product.precio.toLowerCase().indexOf(
        filterText.toLowerCase()
      ) === -1)
    ) {
      return;
    }
    // 2. Lógica de filtro por novedad
    if (inStockOnly && !product.novedad) return;
    // 3. Lógica de filtro por empresa (tu lógica original)
    const empIndex = empresas.indexOf(product.empresa);
    if (!seleccionEmpresas[empIndex]) return;

    if (product.nombre !== lastCategory) {
      rows.push(
        <ProductCategoryRow category={product.categoria} key={product.categoria} />
      );
    }
    rows.push(
      <ProductRow product={product} key={product.descripcion3} setRazonamiento={setRazonamiento} />
    );
    lastCategory = product.nombre;
  });

  return (
    <table className="table">
      <thead>
        <tr>
          <th>Descripción</th>
          <th>(Empresa):</th>
          <th>Precio</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>

    </table>
  );
}

function ProductCategoryRow({ category }) {
  return (
    <tr>
      <th colSpan="2" className="category-header">{category}</th>
    </tr>
  );
}

function ProductRow({ product, setRazonamiento }) {
  const descrip = !product.novedad ? (<span>{product.descripcion1} {product.descripcion2} {product.descripcion3}</span>) :
    <span style={{ color: 'red' }}>
      {product.descripcion1}-{product.descripcion2}-{product.descripcion3}
    </span>;

  return (
    <tr>
      <td  className="seleccionable" onClick={ () => setRazonamiento( manejarClickSeguro(product, document.getElementById('loading-overlay')) )}>
        {/*<u><span style="cursor:pointer;">{descrip}</span></u>*/}
        {descrip}
      </td>
      <td>({product.empresa}): </td>
      <td>{product.precio}</td>
    </tr>
  );
}

const manejarClickSeguro = async (producto, loader) => {
  
  loader.classList.remove('hidden'); // Mostrar el loader
  try{
    const respuesta = await fetch('/api/ai', // Usa a Next.js como Proxy para evitar CORS al llamar la ngrok directamente desde el cliente.
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body:JSON.stringify({"model": "Cloude", "prompt": "Un dato sobre: "+ producto.empresa, "stream": false})
      }
    );

    if (!respuesta.ok) throw new Error('El servidor tardó mucho en responder.');

    const data = await respuesta.json();
    console.log("Datos recibidos.");
    return data.response;
  } catch (error) {
    console.error("Error en Dashboard:", error);
    return error.message + "Error: La IA de Bedrock está tardando demasiado. Revisa AWS";
  } finally {
    loader.classList.add('hidden');
  }
};

/*
const RIESGOS = [
  {Empresa: "Mapfre", Category:"Coche", precio: "$123", novedad: true, nroPoliza: "123", descripcion: "Mazda3", fechaVencimiento:"20/3/2026"},
  {Empresa: "Mapfre", Category:"Coche", precio: "$1432", novedad: false, nroPoliza: "123", descripcion: "Mazda2", fechaVencimiento:"20/3/2026"},
  {Empresa: "Verti", Category:"Coche", precio: "$12342", novedad: true, nroPoliza: "123", descripcion: "Dacia", fechaVencimiento:"20/3/2026"},
  {Empresa: "Linea directa", Category:"Coche", precio: "$12342", novedad: false, nroPoliza: "123", descripcion: "Range Rover", fechaVencimiento:"20/3/2026"},
  {Empresa: "Mapfre", Category:"Hogar", precio: "$1234", novedad: true, nroPoliza: "123", descripcion: "Calle maria 3", fechaVencimiento:"20/3/2026"},
  {Empresa: "Verti", Category:"Hogar", precio: "$1234", novedad: false, nroPoliza: "123", descripcion: "plaza sotelo 1", fechaVencimiento:"20/3/2026"},
  {Empresa: "Mutua", Category:"Hogar", precio: "$1234", novedad: true, nroPoliza: "123", descripcion: "ronda latina 5", fechaVencimiento:"20/3/2026"},
]*/
