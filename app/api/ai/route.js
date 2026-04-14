import { BedrockRuntimeClient, InvokeModelCommand } from "@aws-sdk/client-bedrock-runtime";
import { NextResponse } from 'next/server';

export const maxDuration = 120;

export async function POST(request) {
  try{
    const client = new BedrockRuntimeClient({ region: "us-east-1" }); 
    const {prompt, model, stream} = await request.json();
    const res = await client.send(new InvokeModelCommand({ 
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

    /*if(!res.ok) {
            const errorData = await res.text();
            console.error("Error de Bedrock:", errorData);
            return NextResponse.json({ error: "Bedrock tardó demasiado o falló" }, { status: res.status });
    }*/

    const result = JSON.parse(new TextDecoder().decode(res.body)); 

    //const data = await res.json();
    return NextResponse.json({ response: result.content[0].text });
}catch(error){
    console.log("DETALLE ERROR 500: ",error);
    return NextResponse.json({ error: "Fallo de conexión con AWS" }, { status: 500 });
}
}