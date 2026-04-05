
import { NextResponse } from 'next/server';
import { query } from '@/lib/db'; // Nuestra librería de Postgres
//import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
//import { DynamoDBDocumentClient, PutCommand } from "@aws-sdk/lib-dynamodb";
//import { v4 as uuidv4 } from 'uuid'; // Para generar IDs únicos

// 1. Configuración de DynamoDB
//const client = new DynamoDBClient({ region: "us-east-1" });
//const docClient = DynamoDBDocumentClient.from(client);

export async function GET(request) {
  try {
    // 1. Obtener el ID del usuario de la URL (por ahora lo haremos simple)
    const { searchParams } = new URL(request.url);
    const userId = searchParams.get('userId');

    if (!userId) {
      return NextResponse.json({ message: "No autorizado" }, { status: 401 });
    }

    // 2. Consultar solo los seguros de ese usuario
    const sql = `
      SELECT 
        s.id, 
        s.empresa as "Empresa", 
        c.nombre as "Category", 
        s.precio, 
        s.novedad, 
        s.nro_contrato as "nroPoliza", 
        s.descripcion, 
        s.fecha_vencimiento as "fechaVencimiento"
      FROM servicios s
      JOIN categorias c ON s.categoria_id = c.id
      WHERE s.user_id = $1
    `;
    const result = await query(sql, [userId]);

    return NextResponse.json(result.rows);
  } catch (error) {
    return NextResponse.json({ message: "Error al cargar servicios" }, { status: 500 });
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