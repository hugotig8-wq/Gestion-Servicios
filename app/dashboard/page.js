'use client';

import { useEffect, useState } from 'react';
import { signOut, useSession } from 'next-auth/react';

export default function Dashboard() {
  const { data: session, status } = useSession();
  const [servicios, setServicios] = useState([]);
  const [cargandoServicios, setCargandoServicios] = useState(false);

  useEffect(() => {
    if (status !== 'authenticated') return;

    const fetchServicios = async () => {
      setCargandoServicios(true);
      try {
        const res = await fetch('/api/servicios');
        const json = await res.json();
        if (res.ok) {
          setServicios(json.data || []);
        } else {
          setServicios([]);
          console.error('Error cargando servicios:', json.message || res.statusText);
        }
      } catch (error) {
        console.error('Error cargando datos', error);
        setServicios([]);
      } finally {
        setCargandoServicios(false);
      }
    };

    fetchServicios();
  }, [status]);

  if (status === 'loading' || cargandoServicios) {
    return <p>Cargando sesión y servicios...</p>;
  }

  if (status === 'unauthenticated') {
    return <p>Acceso denegado. Por favor inicia sesión.</p>;
  }

  return (
    <div>
      <div
        id="loading-overlay"
        className="hidden flex flex-wrap w-full justify-center fixed inset-0 gap-4 p-4 z-50 bg-opacity-50 backdrop-blur-sm"
      >
        <div className="relative p-8 rounded-lg shadow-xl flex flex-col items-center">
          <div className="w-12 md:w-24 lg:w-48 h-12 md:w-24 lg:h-48 border-4 hover:border-blue-200 border-t-blue-600 rounded-full animate-spin" />
          <p className="mt-4 text-gray-700 font-medium">
            Cargando tus servicios contratados desde Git Codespaces
          </p>
        </div>
      </div>

      <div>
        <div className="bg-corporativo rounded-extra p-4 bg-gray-100 flex justify-left">
          <p>
            Usuario: <strong>{session?.user?.email}</strong>
          </p>
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
  const [razonamiento, setRazonamiento] = useState('Da click sobre el nombre del seguro a analizar...');

  const empresas = [...new Set(products.rows.map((item) => item.empresa))];
  const [seleccionEmpresas, setSeleccionEmpresas] = useState([...empresas].map(() => true));

  return (
    <div className="container">
      <div className="sidebar">
        <h3>Compañías</h3>
        {empresas.map((empresa, index) => (
          <label key={empresa}>
            <input
              type="checkbox"
              checked={seleccionEmpresas[index] ?? true}
              onChange={() => {
                const nuevaSeleccion = [...seleccionEmpresas];
                nuevaSeleccion[index] = !nuevaSeleccion[index];
                setSeleccionEmpresas(nuevaSeleccion);
              }}
            />{' '}
            {empresa}
          </label>
        ))}
      </div>

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

      <div className="div-analisis">
        <h2>Análisis de Nova:</h2>
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
        {' '}Solo mostrar novedades
      </label>
    </form>
  );
}

function ProductTable({ products, filterText, inStockOnly, seleccionEmpresas, empresas, setRazonamiento }) {
  const rows = [];
  let lastCategory = null;

  products.rows.forEach((product) => {
    const textoBusqueda = filterText.toLowerCase();
    const descripcion1 = String(product.descripcion1 ?? '').toLowerCase();
    const descripcion2 = String(product.descripcion2 ?? '').toLowerCase();
    const descripcion3 = String(product.descripcion3 ?? '').toLowerCase();
    const categoria = String(product.categoria ?? '').toLowerCase();
    const empresa = String(product.empresa ?? '').toLowerCase();
    const precio = String(product.precio ?? '').toLowerCase();

    if (
      descripcion1.indexOf(textoBusqueda) === -1 &&
      descripcion2.indexOf(textoBusqueda) === -1 &&
      descripcion3.indexOf(textoBusqueda) === -1 &&
      categoria.indexOf(textoBusqueda) === -1 &&
      empresa.indexOf(textoBusqueda) === -1 &&
      precio.indexOf(textoBusqueda) === -1
    ) {
      return;
    }

    if (inStockOnly && !product.novedad) return;

    const empIndex = empresas.indexOf(product.empresa);
    if (empIndex >= 0 && !seleccionEmpresas[empIndex]) return;

    if (product.categoria !== lastCategory) {
      rows.push(<ProductCategoryRow category={product.categoria} key={product.categoria} />);
    }

    rows.push(
      <ProductRow
        product={product}
        key={product.descripcion3}
        setRazonamiento={setRazonamiento}
      />
    );
    lastCategory = product.categoria;
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
  const descrip = !product.novedad ? (
    <span>{product.descripcion1} {product.descripcion2} {product.descripcion3}</span>
  ) : (
    <span style={{ color: 'red' }}>
      {product.descripcion1}-{product.descripcion2}-{product.descripcion3}
    </span>
  );

  return (
    <tr>
      <td
        className="seleccionable"
        onClick={async () => {
          const loader = document.getElementById('loading-overlay');
          const resultado = await manejarClickSeguro(product, loader);
          setRazonamiento(resultado);
        }}
      >
        {descrip}
      </td>
      <td>({product.empresa}): </td>
      <td>{product.precio}</td>
    </tr>
  );
}

const manejarClickSeguro = async (producto, loader) => {
  if (loader) loader.classList.remove('hidden');

  try {
    const respuesta = await fetch('/api/ai', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'Amazon.nova-lit-2-v1:0',
        prompt: `Convenceme de renovar con: ${producto.empresa} u ofreceme una alternativa lógica. Actualmente por mes pago: ${producto.precio}`,
        stream: true
      })
    });

    const data = await respuesta.json();
    console.log('Datos recibidos.');
    return data.answer;
  } catch (error) {
    console.error('Error en Dashboard:', error);
    return `${error.message} Error: La IA de Bedrock está tardando demasiado. Revisa AWS`;
  } finally {
    if (loader) loader.classList.add('hidden');
  }
};
