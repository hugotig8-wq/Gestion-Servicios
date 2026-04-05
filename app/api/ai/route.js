
import { NextResponse } from 'next/server';

export const maxDuration = 120;

export async function POST(request) {
  try{  
    const {prompt, model, stream} = await request.json();
    const res = await fetch("https://hottish-cathy-hemelytral.ngrok-free.dev/api/generate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "ngrok-skip-browser-warning": "true"
        },        body: JSON.stringify({
            model: model,
            prompt: prompt,
            stream: stream
        }),
    });

    if(!res.ok) {
            const errorData = await res.text();
            console.error("Error de Ollama/Ngrok:", errorData);
            return NextResponse.json({ error: "Ollama tardó demasiado o falló" }, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json({ response: data.response });
}catch(error){
    console.log("DETALLE ERROR 500: ",error);
    return NextResponse.json({ error: "Fallo de conexión con el túnel ngrok" }, { status: 500 });
}
}