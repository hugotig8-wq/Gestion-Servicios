
import { NextResponse } from 'next/server';

import { BedrockRuntimeClient, InvokeModelCommand } from "@aws-sdk/client-bedrock-runtime";


export const maxDuration = 10000;

/*async function preguntarAlDocumento(prompt, knowledgeBaseId) {
  try {
    const client = new BedrockRuntimeClient(
      {region: "us-east-1", credentials: {
         accessKeyId: process.env.AWS_ACCESS_KEY_ID,
         secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
    },});
    const credentials = await client.config.credentials();
    console.log('Credentials loaded:', !!credentials.accessKeyId);
    const command = new RetrieveAndGenerateCommand({
      input: {
        text: prompt,
      },
      retrieveAndGenerateConfiguration: {
        type: "KNOWLEDGE_BASE",
        knowledgeBaseConfiguration: {
          knowledgeBaseId: knowledgeBaseId, // ID de tu Base de Conocimiento
          modelArn:process.env.BEDROCK_MODEL_ARN,
        },
      },
     });
      const response = await client.send(command);
      console.log("Respuesta:", response.output.text);
      
      return NextResponse.json({ response: response.output.text });
    } catch (error) {
      console.error("Error al consultar Bedrock:", error);
      return NextResponse.json({ error:error.message }, { status: 500 });
   }
}*/


export async function POST(request) {
  try{
    const payload = {
            system: [
                { text: "Eres un asistente experto en coberturas, ofertas y reclamaciones por zona la empresa que tengo contratada, convenceme de renovar o cambiarme de compañía." }
            ],

            messages: [
                {
                  role: "user",
                  content: [
                    { text: prompt}
                  ]
                }
            ],
            inferenceConfig: {
               maxTokens: 1024,
               temperature: 0.7,
               topP: 0.9
            },   
    };
    
    const {prompt, model, stream} = await request.json();
    const client = new BedrockRuntimeClient(
      {region: "us-east-1", credentials: {
         accessKeyId: process.env.AWS_ACCESS_KEY_ID,
         secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
    },});

    const credentials = await client.config.credentials();
    console.log('Credentials loaded:', !!credentials.accessKeyId);

    /*  return preguntarAlDocumento("Saber si no pagaron la retroactividad de los primeros meses de 2024.", process.env.BEDROCK_KNOWLEDGE_BASE_ID);
  }catch(error){
    console.log("DETALLE ERROR 500: ",error);
    return NextResponse.json({ error:error.message }, { status: 500 });
  }*/

    
    const res = await client.send(new InvokeModelCommand({ 
    
        modelId:"amazon.nova-2-lite-v1:0", 
        body: JSON.stringify(payload), // ✅ Convertir a JSON string
        contentType: "application/json",
        accept: "application/json",
    })); 

   /* if(!res.ok) {
            const errorData = await res.text();
            console.error("Error de Bedrock:", errorData);
            return NextResponse.json({ error: "Bedrock tardó demasiado o falló" }, { status: res.status });
    }*/
    console.log("Respuesta:", res.output.text);
      
    return NextResponse.json({ response: res.output.text });

}catch(error){
    console.log("DETALLE ERROR 500: ",error);
    return NextResponse.json({ error:error.message }, { status: 500 });
}
}
/*https://geoportal.minetur.gob.es/VCTEL/vcne.do debe ser checkeada junto con dirección del cliente y lugares de interés
y rutas de google maps usando su api.*/
