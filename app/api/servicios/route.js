import { getServerSession } from "next-auth/next";
import { NextResponse } from 'next/server';
import { authOptions } from "@/app/api/auth/[...nextauth]/options";
//import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
//import { DynamoDBDocumentClient, PutCommand } from "@aws-sdk/lib-dynamodb";
//import { v4 as uuidv4 } from 'uuid'; // Para generar IDs únicos

// 1. Configuración de DynamoDB
//const client = new DynamoDBClient({ region: "us-east-1" });
//const docClient = DynamoDBDocumentClient.from(client);
//import { cookies } from 'next/headers';

export async function GET() {
  
  try {
    // 1. Obtener el ID del usuario de la URL (por ahora lo haremos simple)
    //const { searchParams } = new URL(request.url);
    /*const response = await fetch('/api/auth/login', {method: 'POST' });
    const data = await response.json(); */
    //const userId = searchParams.get('id');
    //const userId =data.user.id;
    //const cookieStore = cookies();
    //const userId = cookieStore.get('userId')?.value;
    const session = await getServerSession(authOptions); // Obtiene la sesión segura
    
    if (!session || !session.user || !session.user.id) {
      return NextResponse.json({ message: "No autorizado" }, { status: 401 });
    }

    const { query } = await import('@/lib/db'); // Nuestra librería de Postgres

    //const userId = session.user.id;

    // 2. Consultar solo los seguros de ese usuario
    /*const sql = `
      SELECT
        t2.descripcion1,
        t2.descripcion2,
        t2.descripcion3,
        t3.nombre,
        s.empresa,
        s.precio,
        s.novedad,
        s.dynamo_id,
        s.s3_folder_path,
      FROM descripciones t2
      JOIN (SELECT empresa, precio, novedad, dynamo_id, s3_folder_path
            FROM servicios ) AS s ON s.user_id = $1
      JOIN (categorias t3 ON s.categoria_id=t3.id) GROUP BY t3.nombre;
    `;*/
    const sql = `
      SELECT
        t2.descripcion1,
        t2.descripcion2,
        t2.descripcion3,
        t3.nombre as categoria,
        s.empresa,
        s.precio_mensual as precio,
        s.novedad
      FROM servicios s
      JOIN descripciones t2 ON s.descripciones_id = t2.descripciones_id
      JOIN categorias t3 ON s.categoria_id = t3.id
      WHERE s.user_id = $1
      ORDER BY t3.nombre;
    `;

    const result = await query(sql, [session.user.id]);

    return NextResponse.json({data:result.rows}, { status: 200 });
  } catch (error) {
    console.error('ERROR SERVICIOS:', error);
    return NextResponse.json({ message: error.message }, { status: 500 });
  }
}
/*
export async function POST(request) {
  try {
    const body = await request.json();
    const { userId, categoriaId, empresa, precio, crawlerData, s3AudioUrl } = body;

    // Generamos una "ID de Unión" única para este servicio
    const metadataId = uuidv4();

    // --- OPERACIÓN A: GUARDAR EN DYNAMODB (Metadatos pesados) ---
    const dynamoParams = {
      TableName: "ServiciosMetadata", // Nombre de tu tabla en AWS
      Item: {
        id_metadata: metadataId,
        audio_url: s3AudioUrl || null,
        scrapper_json: crawlerData || {},
        fecha_procesado: new Date().toISOString()
      }
    };
    await docClient.send(new PutCommand(dynamoParams));

    // --- OPERACIÓN B: GUARDAR EN RDS (Datos estructurados) ---
    const sql = `
      INSERT INTO servicios (user_id, categoria_id, empresa, precio, dynamo_id)
      VALUES ($1, $2, $3, $4, $5)
      RETURNING id;
    `;
    const rdsResult = await query(sql, [userId, categoriaId, empresa, precio, metadataId]);

    return NextResponse.json({
      message: "Servicio e Inteligencia guardados con éxito",
      serviceId: rdsResult.rows[0].id,
      metadataId: metadataId
    }, { status: 201 });

  } catch (error) {
    console.error("ERROR HÍBRIDO:", error);
    return NextResponse.json({ message: "Fallo en el guardado dual" }, { status: 500 });
  }
}
*/