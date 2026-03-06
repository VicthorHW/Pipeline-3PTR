import subprocess
import os
import argparse
import json
import datetime
import sys

sys.stdout.reconfigure(encoding='utf-8')

PRUSA_PATH = r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe"
BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
JSON_CONFIG = "render_profiles.json"

def criar_estrutura_diretorios():
    agora = datetime.datetime.now()
    meses = {1:"Janeiro", 2:"Fevereiro", 3:"Março", 4:"Abril", 5:"Maio", 6:"Junho", 
             7:"Julho", 8:"Agosto", 9:"Setembro", 10:"Outubro", 11:"Novembro", 12:"Dezembro"}
    ano_dir = str(agora.year)
    mes_dir = f"{agora.month:02d} - {meses[agora.month]}"
    dia_dir = f"{agora.day:02d}"
    hora_min_prefixo = agora.strftime("%H_%M")
    dir_atual = os.path.abspath(os.path.dirname(__file__))
    pasta_saida = os.path.join(dir_atual, ano_dir, mes_dir, dia_dir)
    os.makedirs(pasta_saida, exist_ok=True)
    json_path = os.path.join(dir_atual, JSON_CONFIG)
    return pasta_saida, hora_min_prefixo, json_path

def run_pipeline(stl_file_path, profile_name, material_nome, escala, cena_blender, quality_mesh=4, 
                 s_tx=0, s_ty=0, s_tz=0, s_rx=0, s_ry=0, s_rz=0, s_sx=1, s_sy=1, s_sz=1, 
                 r_tx=0, r_ty=0, r_tz=0, r_rx=0, r_ry=0, r_rz=0, r_sx=1, r_sy=1, r_sz=1, 
                 auto_orient=False, render_samples=32, max_time=0, res_percent=100, cameras="Cam_Frente,Cam_Macro", is_preview=False, is_thumb=False):
    
    pasta_saida, prefixo_tempo, json_path = criar_estrutura_diretorios()
    nome_base = os.path.splitext(os.path.basename(stl_file_path))[0]
    
    if is_thumb:
        thumbs_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "temp_uploads", "thumbs")
        os.makedirs(thumbs_dir, exist_ok=True)
        output_img_prefix = os.path.join(thumbs_dir, f"thumb_{nome_base}")
        final_stl_mesh = stl_file_path # Direto pro Blender
        blender_project_path = "null.blend" 

    else:
        # O NOME DO CACHE DEPENDE APENAS DO SLICER! (r_tx, etc não entram aqui)
        sufixo_transf = "auto" if auto_orient else f"sr{s_rx}_{s_ry}_{s_rz}_ss{s_sx}_{s_sy}_{s_sz}_st{s_tx}_{s_ty}_{s_tz}"
        
        stl_orientado = os.path.join(pasta_saida, f"{nome_base}_oriented_{sufixo_transf}.stl")
        gcode_file = os.path.join(pasta_saida, f"{nome_base}_{profile_name}_{sufixo_transf}.gcode")
        final_stl_mesh = os.path.join(pasta_saida, f"{nome_base}_mesh_{profile_name}_{sufixo_transf}.stl")
        
        tipo_str = "preview" if is_preview else "render"
        output_img_prefix = os.path.join(pasta_saida, f"{prefixo_tempo}_{nome_base}_{tipo_str}_{profile_name}_{material_nome}")
        blender_project_path = os.path.join(pasta_saida, f"{prefixo_tempo}_{nome_base}_{tipo_str}_diag_{profile_name}_{material_nome}.blend")

        # MAGIA DO CACHE: Se você mexer na "Cena do Blender", ele acha a malha fatiada instantaneamente!
        if os.path.exists(final_stl_mesh):
            print(f"\n[CACHE] ♻️ Gêmeo Digital fatiado idêntico encontrado! Pulando o PrusaSlicer e indo direto para o Render...")
        else:
            print(f"\n[STAGE 1] 🔄 Aplicando Transformações do Fatiador (Trimesh)...")
            cmd_orient = [
                "python", "orient_stl.py", stl_file_path, stl_orientado,
                "--tx", str(s_tx), "--ty", str(s_ty), "--tz", str(s_tz),
                "--rx", str(s_rx), "--ry", str(s_ry), "--rz", str(s_rz),
                "--sx", str(s_sx), "--sy", str(s_sy), "--sz", str(s_sz)
            ]
            if auto_orient: cmd_orient.append("--auto")
            subprocess.run(cmd_orient, check=True)
            
            print(f"[STAGE 2] 🔪 Fatiando fisicamente no PrusaSlicer (Perfil: {profile_name})...")
            subprocess.run([PRUSA_PATH, "--export-gcode", "--load", f"profiles/{profile_name}.ini", stl_orientado, "--output", gcode_file], check=True)

            print(f"[STAGE 3] 🧶 Construindo Gêmeo Digital (GCode-to-Mesh)...")
            subprocess.run(["python", "gcode_to_mesh.py", "--input", gcode_file, "--output", final_stl_mesh, "--quality", str(quality_mesh)], check=True)
    
    if not is_thumb: print(f"[STAGE 4] 📷 Aplicando Pose de Cena e Renderizando: [{material_nome.upper()}]")
    
    cmd_blender = [
        BLENDER_PATH, "-b", cena_blender, "-P", "blender_render.py", "--", 
        final_stl_mesh, material_nome, output_img_prefix, str(render_samples), str(max_time), 
        blender_project_path, str(escala), json_path, str(res_percent), cameras, str(is_thumb),
        # Passa os 9 parâmetros de render para o Blender
        str(r_tx), str(r_ty), str(r_tz), str(r_rx), str(r_ry), str(r_rz), str(r_sx), str(r_sy), str(r_sz)
    ]
    
    subprocess.run(cmd_blender, check=True)
    
    if is_thumb:
        thumb_caminho_final = f"{output_img_prefix}_{cameras.split(',')[0]}.png"
        if os.path.exists(thumb_caminho_final):
            print(f"###THUMB_GERADA###{thumb_caminho_final}")
    else:
        print(f"\n✨ SUCESSO! Pasta do render: {pasta_saida}")
        print(f"###OUT_DIR###{pasta_saida}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--profile", default="020_standard")
    parser.add_argument("--material", default="PLA - Preto")
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--scene", default="template_ecommerce.blend")
    
    # Slicer
    parser.add_argument("--s_tx", type=float, default=0.0); parser.add_argument("--s_ty", type=float, default=0.0); parser.add_argument("--s_tz", type=float, default=0.0)
    parser.add_argument("--s_rx", type=float, default=0.0); parser.add_argument("--s_ry", type=float, default=0.0); parser.add_argument("--s_rz", type=float, default=0.0)
    parser.add_argument("--s_sx", type=float, default=1.0); parser.add_argument("--s_sy", type=float, default=1.0); parser.add_argument("--s_sz", type=float, default=1.0)
    
    # Render Blender
    parser.add_argument("--r_tx", type=float, default=0.0); parser.add_argument("--r_ty", type=float, default=0.0); parser.add_argument("--r_tz", type=float, default=0.0)
    parser.add_argument("--r_rx", type=float, default=0.0); parser.add_argument("--r_ry", type=float, default=0.0); parser.add_argument("--r_rz", type=float, default=0.0)
    parser.add_argument("--r_sx", type=float, default=1.0); parser.add_argument("--r_sy", type=float, default=1.0); parser.add_argument("--r_sz", type=float, default=1.0)
    
    parser.add_argument("-ao", "--auto-orient", action="store_true")
    parser.add_argument("--samples", type=int, default=32)
    parser.add_argument("--time", type=int, default=0)
    parser.add_argument("--res", type=int, default=100)
    parser.add_argument("--cameras", type=str, default="Cam_Frente,Cam_Macro")
    parser.add_argument("--is_preview", action="store_true")
    parser.add_argument("--is_thumb", action="store_true") 
    
    args = parser.parse_args()
    try:
        run_pipeline(
            stl_file_path=args.file, profile_name=args.profile, material_nome=args.material, 
            escala=args.scale, cena_blender=args.scene, quality_mesh=4, 
            s_tx=args.s_tx, s_ty=args.s_ty, s_tz=args.s_tz, s_rx=args.s_rx, s_ry=args.s_ry, s_rz=args.s_rz, s_sx=args.s_sx, s_sy=args.s_sy, s_sz=args.s_sz,
            r_tx=args.r_tx, r_ty=args.r_ty, r_tz=args.r_tz, r_rx=args.r_rx, r_ry=args.r_ry, r_rz=args.r_rz, r_sx=args.r_sx, r_sy=args.r_sy, r_sz=args.r_sz,
            auto_orient=args.auto_orient, render_samples=args.samples, 
            max_time=args.time, res_percent=args.res, cameras=args.cameras, is_preview=args.is_preview, is_thumb=args.is_thumb
        )
    except Exception as e:
        print(f"\n❌ ERRO FATAL no pipeline: {e}")