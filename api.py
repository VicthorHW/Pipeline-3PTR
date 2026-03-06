from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List
import os
import json
import shutil
import subprocess
from datetime import datetime
import glob
import zipfile
import io

app = FastAPI(title="3PTR Studio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PASTA_TEMP = "temp_uploads"
os.makedirs(PASTA_TEMP, exist_ok=True)
JSON_CONFIG = "render_profiles.json"

class RenderTask(BaseModel):
    modelo_nome: str
    materiais: List[str]
    cenarios: List[str]
    s_tx: float; s_ty: float; s_tz: float
    s_rx: float; s_ry: float; s_rz: float
    s_sx: float; s_sy: float; s_sz: float
    r_tx: float; r_ty: float; r_tz: float
    r_rx: float; r_ry: float; r_rz: float
    r_sx: float; r_sy: float; r_sz: float
    perfil: str

class RenderRequest(BaseModel):
    tasks: List[RenderTask]
    is_preview: bool
    samples: int
    resolucao: int
    auto_orient: bool

class ZipRequest(BaseModel):
    paths: List[str]

@app.get("/config")
def get_config():
    cenarios_disponiveis = glob.glob("*.blend")
    if not cenarios_disponiveis: cenarios_disponiveis = ["template_ecommerce.blend"]
        
    config_data = {"materiais": {}, "config_app": {}, "cenarios_disponiveis": cenarios_disponiveis}
    
    if os.path.exists(JSON_CONFIG):
        with open(JSON_CONFIG, 'r', encoding='utf-8') as f:
            salvo = json.load(f)
            if "materiais" in salvo: config_data["materiais"] = salvo["materiais"]
            if "config_app" in salvo: config_data["config_app"] = salvo["config_app"]
            
    return config_data

@app.post("/save_config")
def save_config(dados: dict):
    with open(JSON_CONFIG, 'w', encoding='utf-8') as f: json.dump(dados, f, indent=4)
    return {"status": "success"}

@app.post("/upload")
async def upload_stl(file: UploadFile = File(...)):
    caminho_salvar = os.path.join(PASTA_TEMP, file.filename)
    with open(caminho_salvar, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename}

@app.get("/image")
def serve_image(path: str):
    if os.path.exists(path): return FileResponse(path)
    return {"error": "Image not found"}

# --- NOVA ROTA: GERADOR DE ARQUIVO ZIP ---
@app.post("/download-zip")
def download_zip(payload: ZipRequest):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for file_path in payload.paths:
            if os.path.exists(file_path):
                # Guarda apenas o nome do arquivo, ignorando a estrutura de pastas do HD
                zip_file.write(file_path, arcname=os.path.basename(file_path))
    
    zip_buffer.seek(0)
    nome_zip = f"Renders_3PTR_{datetime.now().strftime('%H%M%S')}.zip"
    
    return StreamingResponse(
        zip_buffer, 
        media_type="application/zip", 
        headers={"Content-Disposition": f"attachment; filename={nome_zip}"}
    )

@app.post("/render")
def iniciar_render(payload: RenderRequest):
    def log_generator():
        yield f"data: {json.dumps({'type': 'log', 'text': f'=== INICIANDO MOTOR DE RENDER ===\\n'})}\n\n"
        for task in payload.tasks:
            for cenario in task.cenarios:
                for mat in task.materiais:
                    caminho_base = os.path.join(PASTA_TEMP, task.modelo_nome)
                    cameras_exec = "Cam_Frente,Cam_Macro" if payload.is_preview else "Cam_Frente,Cam_45,Cam_Topo,Cam_Macro"
                    
                    comando = [
                        "python", "pipeline.py", "--file", caminho_base, "--profile", task.perfil,
                        "--material", mat, "--scale", "1.0", "--samples", str(payload.samples), 
                        "--scene", cenario, "--res", str(payload.resolucao), "--cameras", cameras_exec,
                        "--s_tx", str(task.s_tx), "--s_ty", str(task.s_ty), "--s_tz", str(task.s_tz),
                        "--s_rx", str(task.s_rx), "--s_ry", str(task.s_ry), "--s_rz", str(task.s_rz),
                        "--s_sx", str(task.s_sx), "--s_sy", str(task.s_sy), "--s_sz", str(task.s_sz),
                        "--r_tx", str(task.r_tx), "--r_ty", str(task.r_ty), "--r_tz", str(task.r_tz),
                        "--r_rx", str(task.r_rx), "--r_ry", str(task.r_ry), "--r_rz", str(task.r_rz),
                        "--r_sx", str(task.r_sx), "--r_sy", str(task.r_sy), "--r_sz", str(task.r_sz)
                    ]
                    if payload.auto_orient: comando.append("-ao")
                    if payload.is_preview: comando.append("--is_preview") 
                    
                    processo = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', bufsize=1)
                    
                    for linha in processo.stdout:
                        yield f"data: {json.dumps({'type': 'log', 'text': linha})}\n\n"
                        if "###SAVED_IMG_PATH###" in linha:
                            partes = linha.strip().split("###")
                            if len(partes) >= 4:
                                cam_code = partes[2].strip()
                                img_path = partes[3].strip()
                                yield f"data: {json.dumps({'type': 'image', 'camera': cam_code, 'path': img_path, 'material': mat, 'cenario': cenario})}\n\n"
                    processo.wait()
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    return StreamingResponse(log_generator(), media_type="text/event-stream")