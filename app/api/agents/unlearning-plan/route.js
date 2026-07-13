import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';

export async function POST(req) {
    try {
        const { repo_path } = await req.json();
        
        const pythonScript = path.join(process.cwd(), 'agents', 'smollm_unlearning_agent.py');
        
        return new Promise((resolve) => {
            const python = spawn('python3', [
                pythonScript,
                JSON.stringify({ repo_path })
            ]);

            let output = '';
            let error = '';

            python.stdout.on('data', (data) => {
                output += data.toString();
                console.log(`[Agent] ${data.toString()}`);
            });

            python.stderr.on('data', (data) => {
                error += data.toString();
                console.error(`[Error] ${data.toString()}`);
            });

            python.on('close', (code) => {
                if (code === 0) {
                    const reportFile = path.join(process.cwd(), 'plan_unlearning_completo.json');
                    
                    if (fs.existsSync(reportFile)) {
                        const reporte = JSON.parse(fs.readFileSync(reportFile, 'utf-8'));
                        
                        resolve(new Response(JSON.stringify({
                            status: 'success',
                            reporte,
                            output
                        }), {
                            headers: { 'Content-Type': 'application/json' }
                        }));
                    } else {
                        resolve(new Response(JSON.stringify({
                            status: 'error',
                            message: 'Reporte no generado',
                            output
                        }), {
                            status: 500,
                            headers: { 'Content-Type': 'application/json' }
                        }));
                    }
                } else {
                    resolve(new Response(JSON.stringify({
                        status: 'error',
                        error,
                        code
                    }), {
                        status: 500,
                        headers: { 'Content-Type': 'application/json' }
                    }));
                }
            });
        });
    } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}
