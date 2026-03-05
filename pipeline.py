import subprocess
import os
import argparse

# ==============================================================================
# CONFIGURAÇÕES GERAIS E CAMINHOS
# ==============================================================================
PRUSA_PATH = r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe"
BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
TEMPLATE_BLENDER = "template_ecommerce.blend"

CORES = {"branco": "#FFFFFF", "preto": "#1A1A1A", "cinza": "#808080"}

def preparar_pastas():
    for pasta in ["oriented_stls", "gcodes", "renders_mesh", "renders_final"]:
        os.makedirs(pasta, exist_ok=True)

def run_pipeline(stl_file_path, profile_name, cor_nome="cinza", quality=4, rx=0, ry=0, rz=0, auto=True, render_only=False):
    preparar_pastas()
    nome_base = os.path.splitext(os.path.basename(stl_file_path))[0]
    
    sufixo = "auto" if (auto and rx == 0 and ry == 0 and rz == 0) else f"rx{int(rx)}_ry{int(ry)}_rz{int(rz)}"
        
# Obtém o caminho absoluto da pasta raiz do seu projeto
    dir_atual = os.path.abspath(os.path.dirname(__file__))
    
    stl_orientado = os.path.join(dir_atual, "oriented_stls", f"oriented_{nome_base}_{sufixo}.stl")
    gcode_file = os.path.join(dir_atual, "gcodes", f"{nome_base}_{profile_name}_{sufixo}.gcode")
    final_stl_mesh = os.path.join(dir_atual, "renders_mesh", f"render_{nome_base}_{profile_name}_{sufixo}.stl")
    
    # Caminho absoluto para salvar a imagem no lugar certo
    output_img_prefix = os.path.join(dir_atual, "renders_final", f"{nome_base}_{profile_name}_{cor_nome}")
    cor_hex = CORES.get(cor_nome.lower(), "#808080")

    # ==============================================================================
    # CONTROLE DE FLUXO (RENDER ONLY)
    # ==============================================================================
    if render_only:
        print(f"\n⏭️ [MODO RENDER ONLY] Pulando fatiamento para {profile_name}...")
        if not os.path.exists(final_stl_mesh):
            print(f"⚠️ AVISO: A malha '{final_stl_mesh}' não existe. Rode o pipeline normal primeiro. Pulando...")
            return
    else:
        # STAGE 1: ORIENTAÇÃO
        if not os.path.exists(stl_orientado):
            print(f"\n[STAGE 1] 🔄 Orientando {nome_base}.stl ({sufixo})")
            cmd_orient = ["python", "orient_stl.py", stl_file_path, stl_orientado]
            if not auto: cmd_orient.append("--no-auto")
            if rx != 0 or ry != 0 or rz != 0:
                cmd_orient.extend(["--rx", str(rx), "--ry", str(ry), "--rz", str(rz)])
            subprocess.run(cmd_orient, check=True)
        else:
            print(f"\n[STAGE 1] ⏭️ Cache encontrado. STL já orientado ({sufixo}).")

        # STAGE 2: SLICING
        print(f"[STAGE 2] 🔪 Fatiando com o perfil: {profile_name}")
        subprocess.run([PRUSA_PATH, "--export-gcode", "--load", f"profiles/{profile_name}.ini", stl_orientado, "--output", gcode_file], check=True)

        # STAGE 3: G-CODE PARA MALHA
        print(f"[STAGE 3] 🧶 Convertendo Toolpath para Malha 3D (Qualidade: {quality})")
        subprocess.run(["python", "gcode_to_mesh.py", "--input", gcode_file, "--output", final_stl_mesh, "--quality", str(quality)], check=True)
    
    # ==============================================================================
    # STAGE 4: RENDERIZAÇÃO VIRTUAL NO BLENDER
    # ==============================================================================
    print(f"[STAGE 4] 📷 Iniciando Estúdio Virtual ({cor_nome.upper()}) para {profile_name}")
    cmd_blender = [
        BLENDER_PATH, "-b", TEMPLATE_BLENDER, "-P", "blender_render.py", "--", 
        final_stl_mesh, cor_hex, output_img_prefix
    ]
    subprocess.run(cmd_blender, check=True)
    print(f"✨ SUCESSO! Imagens de {profile_name} salvas em 'renders_final'.")

# ==============================================================================
# CLI
# ==============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="3PTR: Pipeline de Renderização de Impressão 3D")
    parser.add_argument("--file", default="teste.stl", help="Arquivo STL de entrada")
    parser.add_argument("--cor", default="cinza", choices=["branco", "preto", "cinza"], help="Cor do filamento")
    parser.add_argument("--rx", type=float, default=0, help="Girar X (graus)")
    parser.add_argument("--ry", type=float, default=0, help="Girar Y (graus)")
    parser.add_argument("--rz", type=float, default=0, help="Girar Z (graus)")
    parser.add_argument("-nr", "--no-rotation", dest="no_auto", action="store_true", help="Desativa auto orientação")
    parser.add_argument("-ro", "--render-only", action="store_true", help="Pula o fatiamento e vai direto para o Blender")
    args = parser.parse_args()

    perfis = ["020_standard", "012_fine"]
    
    auto_mode = not args.no_auto
    if args.rx != 0 or args.ry != 0 or args.rz != 0:
        auto_mode = False

    for p in perfis:
        try:
            run_pipeline(args.file, p, cor_nome=args.cor, quality=4, rx=args.rx, ry=args.ry, rz=args.rz, auto=auto_mode, render_only=args.render_only)
        except Exception as e:
            print(f"\n❌ ERRO FATAL no perfil {p}: {e}")