
import { NextResponse } from 'next/server';
import { BedrockAgentRuntimeClient, RetrieveAndGenerateCommand } from "@aws-sdk/client-bedrock-agent-runtime";


export const maxDuration = 10000;

async function preguntarAlDocumento(prompt, knowledgeBaseId) {
  const command = new RetrieveAndGenerateCommand({
    input: {
      text: prompt,
    },
    retrieveAndGenerateConfiguration: {
      type: "KNOWLEDGE_BASE",
      knowledgeBaseConfiguration: {
        knowledgeBaseId: knowledgeBaseId, // ID de tu Base de Conocimiento
        modelArn: "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0", // O el modelo que prefieras
      },
    },
  });
  try {
      const response = await client.send(command);
      console.log("Respuesta:", response.output.text);
      setTimeout(10000);
      //const data = await res.json();
      return NextResponse.json({ response: response.output.text });
    } catch (error) {
      console.error("Error al consultar Bedrock:", error);
    }
}

export async function POST(request) {
  try{
    const client = new BedrockAgentRuntimeClient({ region: "us-east-1" }); 
    const {prompt, model, stream} = await request.json();

    

  // Ejemplo de uso
    const KB_ID = "EMNEPM6FNC"; 
    preguntarAlDocumento("Saber si no pagaron la retroactividad de los primeros meses de 2024.", KB_ID);
  }catch(error){
    console.log("DETALLE ERROR 500: ",error);
    return NextResponse.json({ error:error.message }, { status: 500 });
  }


    
   /* const res = await client.send(new InvokeModelCommand({ 
        modelId: "us.anthropic.claude-haiku-4-5-20251001-v1:0", 
        body: JSON.stringify({ 
            anthropic_version: "bedrock-2023-05-31", 
            max_tokens: 1024, 
            messages: [{ 
                role: "user", 
                content: prompt
            }] 
        }) 
    })); 

    if(!res.ok) {
            const errorData = await res.text();
            console.error("Error de Bedrock:", errorData);
            return NextResponse.json({ error: "Bedrock tardó demasiado o falló" }, { status: res.status });
    }

    const result = JSON.parse(new TextDecoder().decode(res.body)); 
    setTimeout(10000);
    //const data = await res.json();
    return NextResponse.json({ response: result.content[0].text });
}catch(error){
    console.log("DETALLE ERROR 500: ",error);
    return NextResponse.json({ error:error.message }, { status: 500 });
}*/
}
/*https://geoportal.minetur.gob.es/VCTEL/vcne.do debe ser checkeada junto con dirección del cliente y lugares de interés
y rutas de google maps usando su api.*/
