// app/layout.js
import '../dist/output.css'; // Importamos tus estilos globales aquí

export const metadata = {
  title: 'GestSeguros V1',
  description: 'Gestión inteligente de servicios',
}

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <head>
        <meta charset="UTF-8"></meta>
        <meta name="viewport" content="width=device-width, initial-scale=1.0"></meta>
        
        {/*<link rel="stylesheet" href="../dist/output.css"></link>*/}

      </head>  
      <body>
        {/* Aquí es donde Next.js inyectará tus páginas (Login, Dashboard, etc.) */}
        {children}
      </body>
    </html>
  );
}