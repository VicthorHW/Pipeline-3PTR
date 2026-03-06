import streamlit as st
import os
import json
import subprocess
import glob
from datetime import datetime
import time

st.set_page_config(page_title="3PTR Studio Asset Manager", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stCodeBlock code { font-size: 0.75rem !important; }
[data-testid="stFileUploaderDropzone"] + div { display: none !important; }
ul[data-testid="stUploadedFileList"] { display: none !important; }
[data-testid="stSidebar"] img {
    max-width: 160px !important;
    max-height: 160px !important;
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.1);
}
</style>
""", unsafe_allow_html=True)

JSON_CONFIG = "render_profiles.json"
PASTA_TEMP = "temp_uploads"
os.makedirs(PASTA_TEMP, exist_ok=True)

IMG_LOADING_SKEL = "https://via.placeholder.com/400x300.png?text=Carregando..." 

TIPS = {
    "roughness": "0 = Liso e reflexivo (Vidro, Espelho).\n1 = Fosco e áspero (Borracha, Giz).",
    "specular": "Intensidade do brilho batendo na peça.\n0 = Sem brilho.\n1 = Brilho plástico intenso.",
    "metallic": "0 = Dielétricos (Plástico).\n1 = Condutores (Metal).",
    "transmission": "0 = Opaco (sólido).\n1 = Transparente (vidro).",
    "subsurface": "Luz atravessa e espalha dentro (PETG translúcido).\n0 = Duro.\n1 = Cera/Pele."
}

MATERIAIS_TRAVADOS = {
    "PLA - Preto": {"cor_hex": "#1A1A1A", "roughness": 0.6, "specular": 0.5, "transmission": 0.0, "subsurface": 0.0, "metallic": 0.0},
    "PLA - Branco": {"cor_hex": "#F0F0F0", "roughness": 0.6, "specular": 0.5, "transmission": 0.0, "subsurface": 0.0, "metallic": 0.0},
    "PLA - Cinza": {"cor_hex": "#808080", "roughness": 0.6, "specular": 0.5, "transmission": 0.0, "subsurface": 0.0, "metallic": 0.0},
    "PLA - Marrom": {"cor_hex": "#654321", "roughness": 0.7, "specular": 0.3, "transmission": 0.0, "subsurface": 0.0, "metallic": 0.0},
    "PLA - Verde": {"cor_hex": "#228B22", "roughness": 0.6, "specular": 0.5, "transmission": 0.0, "subsurface": 0.0, "metallic": 0.0},
    "PLA - Azul": {"cor_hex": "#0000CD", "roughness": 0.6, "specular": 0.5, "transmission": 0.0, "subsurface": 0.0, "metallic": 0.0},
    "PLA - Azul Claro": {"cor_hex": "#87CEEB", "roughness": 0.6, "specular": 0.5, "transmission": 0.0, "subsurface": 0.0, "metallic": 0.0},
    "ABS - Preto": {"cor_hex": "#111111", "roughness": 0.5, "specular": 0.6, "transmission": 0.0, "subsurface": 0.0, "metallic": 0.0},
    "ABS - Branco": {"cor_hex": "#EEEEEE", "roughness": 0.5, "specular": 0.6, "transmission": 0.0, "subsurface": 0.0, "metallic": 0.0},
    "PETG - Preto": {"cor_hex": "#1A1A1A", "roughness": 0.4, "specular": 0.8, "transmission": 0.0, "subsurface": 0.0, "metallic": 0.0},
    "PETG - Transparente": {"cor_hex": "#FFFFFF", "roughness": 0.1, "specular": 0.9, "transmission": 0.95, "subsurface": 0.0, "metallic": 0.0}
}

def carregar_perfis():
    padrao = {
        "config_app": {
            "perfil_slicer": ["020_standard"], "cenario": ["template_ecommerce.blend"],
            "escala_global": 1.0, "samples": 64, 
            "res_producao": 100, "max_time": 0, "prev_res": 30, "prev_samples": 16, "auto_preview_toggle": False
        },
        "materiais": {}
    }
    if os.path.exists(JSON_CONFIG):
        with open(JSON_CONFIG, 'r', encoding='utf-8') as f:
            try:
                dados = json.load(f)
                if "config_app" not in dados: dados["config_app"] = padrao["config_app"]
                for key in padrao["config_app"]:
                    if key not in dados["config_app"]: dados["config_app"][key] = padrao["config_app"][key]
                padrao = dados
            except: pass
    for nome, props in MATERIAIS_TRAVADOS.items():
        if nome not in padrao["materiais"]: padrao["materiais"][nome] = props
    return padrao

def salvar_json_silencioso(dados):
    with open(JSON_CONFIG, 'w', encoding='utf-8') as f: json.dump(dados, f, indent=4)

perfis_db = carregar_perfis()

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def render_color_badge(nome_material, hex_color):
    r, g, b = hex_to_rgb(hex_color)
    luminancia = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    cor_texto = "#000000" if luminancia > 0.5 else "#FFFFFF"
    html = f"""<div style="background-color: {hex_color}; color: {cor_texto}; padding: 4px 10px; border-radius: 6px; display: inline-block; margin: 2px; font-weight: bold; border: 1px solid rgba(128,128,128,0.2); font-size: 0.85rem; text-align: center; width: 100%;">{nome_material}</div>"""
    st.markdown(html, unsafe_allow_html=True)

if "db_modelos" not in st.session_state: st.session_state.db_modelos = {}
if "modelo_ativo" not in st.session_state: st.session_state.modelo_ativo = None
if "cancelar_fila" not in st.session_state: st.session_state.cancelar_fila = False
if "disparar_preview" not in st.session_state: st.session_state.disparar_preview = False
if "executando_lote" not in st.session_state: st.session_state.executando_lote = False
if "clipboard_transform" not in st.session_state: st.session_state.clipboard_transform = None
if "arquivos_apagados" not in st.session_state: st.session_state.arquivos_apagados = set()
if "log_historico" not in st.session_state: st.session_state.log_historico = "💻 Terminal Debug Log Inicializado...\n"

# =====================================================================
# SIDEBAR
# =====================================================================
with st.sidebar:
    st.header("📦 Biblioteca")
    arquivos_upados = st.file_uploader("Importar STLs", type=['stl'], accept_multiple_files=True)
    
    if arquivos_upados:
        for arq in arquivos_upados:
            if arq.name not in st.session_state.db_modelos and arq.name not in st.session_state.arquivos_apagados:
                caminho_base = os.path.join(PASTA_TEMP, arq.name)
                with open(caminho_base, "wb") as f: f.write(arq.getbuffer())
                
                with st.spinner(f"Gerando miniatura para {arq.name}..."):
                    cmd_thumb = ["python", "pipeline.py", "--file", caminho_base, "--scene", "template_ecommerce.blend", "--cameras", "Cam_Frente", "--is_thumb"]
                    processo = subprocess.run(cmd_thumb, capture_output=True, text=True, encoding='utf-8')
                    thumb_path = None
                    for linha in processo.stdout.split('\n'):
                        if "###THUMB_GERADA###" in linha: thumb_path = linha.split("###THUMB_GERADA###")[1].strip()
                
                st.session_state.db_modelos[arq.name] = {
                    "arquivo": arq, "thumb": thumb_path,
                    "s_tx": 0.0, "s_ty": 0.0, "s_tz": 0.0, "s_rx": 0.0, "s_ry": 0.0, "s_rz": 0.0, "s_sx": 1.0, "s_sy": 1.0, "s_sz": 1.0,
                    "r_tx": 0.0, "r_ty": 0.0, "r_tz": 0.0, "r_rx": 0.0, "r_ry": 0.0, "r_rz": 0.0, "r_sx": 1.0, "r_sy": 1.0, "r_sz": 1.0,
                    "materiais": ["PLA - Preto"], "perfil": "020_standard", "cenario": "template_ecommerce.blend"
                }
                if not st.session_state.modelo_ativo: st.session_state.modelo_ativo = arq.name

    st.divider()
    if st.session_state.db_modelos:
        st.write("**Modelos Ativos:**")
        modelos_para_deletar = []
        
        for nome_mod, dados_mod in st.session_state.db_modelos.items():
            col_t1, col_t2, col_t3 = st.columns([1, 2.5, 0.5])
            with col_t1:
                if dados_mod["thumb"] and os.path.exists(dados_mod["thumb"]): st.image(dados_mod["thumb"], use_container_width=True)
                else: st.markdown("🧊")
            with col_t2:
                tipo_btn = "primary" if st.session_state.modelo_ativo == nome_mod else "secondary"
                if st.button(nome_mod, key=f"btn_{nome_mod}", type=tipo_btn, use_container_width=True):
                    st.session_state.modelo_ativo = nome_mod
                    st.session_state.disparar_preview = False
                    st.session_state.executando_lote = False
                    st.rerun()
            with col_t3:
                if st.button("🗑️", key=f"del_{nome_mod}", help="Apagar este STL permanentemente"): modelos_para_deletar.append(nome_mod)
            
            for mat_nome in dados_mod["materiais"][:2]: 
                hex_cor = perfis_db["materiais"].get(mat_nome, {}).get("cor_hex", "#808080")
                render_color_badge(mat_nome, hex_cor)
            st.markdown("---")
            
        for m in modelos_para_deletar:
            del st.session_state.db_modelos[m]
            st.session_state.arquivos_apagados.add(m)
            if st.session_state.modelo_ativo == m:
                st.session_state.modelo_ativo = list(st.session_state.db_modelos.keys())[0] if st.session_state.db_modelos else None
            st.rerun()

# =====================================================================
# ÁREA CENTRAL
# =====================================================================
if not st.session_state.db_modelos:
    st.info("👈 Importe arquivos na barra lateral para começar.")
    st.stop()

modelo_atual = st.session_state.db_modelos.get(st.session_state.modelo_ativo)
if not modelo_atual: st.stop()
MOD_ID = st.session_state.modelo_ativo 

col_centro, col_direita = st.columns([1.2, 1.8], gap="large")

with col_centro:
    st.subheader(f"🛠️ Configurações: {st.session_state.modelo_ativo}")
    
    col_clip1, col_clip2 = st.columns(2)
    with col_clip1:
        if st.button("📋 Copiar Setup", use_container_width=True):
            st.session_state.clipboard_transform = {
                "s_tx": modelo_atual["s_tx"], "s_ty": modelo_atual["s_ty"], "s_tz": modelo_atual["s_tz"],
                "s_rx": modelo_atual["s_rx"], "s_ry": modelo_atual["s_ry"], "s_rz": modelo_atual["s_rz"],
                "s_sx": modelo_atual["s_sx"], "s_sy": modelo_atual["s_sy"], "s_sz": modelo_atual["s_sz"],
                "r_tx": modelo_atual["r_tx"], "r_ty": modelo_atual["r_ty"], "r_tz": modelo_atual["r_tz"],
                "r_rx": modelo_atual["r_rx"], "r_ry": modelo_atual["r_ry"], "r_rz": modelo_atual["r_rz"],
                "r_sx": modelo_atual["r_sx"], "r_sy": modelo_atual["r_sy"], "r_sz": modelo_atual["r_sz"],
                "perfil": modelo_atual["perfil"], "cenario": modelo_atual["cenario"]
            }
            st.toast("Copiado para a área de transferência!")
    with col_clip2:
        if st.button("📤 Colar Setup", use_container_width=True, disabled=not st.session_state.clipboard_transform):
            if st.session_state.clipboard_transform:
                modelo_atual.update(st.session_state.clipboard_transform)
                st.toast("Transformações aplicadas!")
                st.rerun()

    with st.expander("🔪 Fatiador PrusaSlicer (Altera a Malha)", expanded=False):
        col_s1, col_s2, col_s3 = st.columns(3)
        modelo_atual["s_tx"] = col_s1.number_input("Slice Move X", value=float(modelo_atual["s_tx"]), step=1.0, key=f"s_tx_{MOD_ID}")
        modelo_atual["s_ty"] = col_s2.number_input("Slice Move Y", value=float(modelo_atual["s_ty"]), step=1.0, key=f"s_ty_{MOD_ID}")
        modelo_atual["s_tz"] = col_s3.number_input("Slice Move Z", value=float(modelo_atual["s_tz"]), step=1.0, key=f"s_tz_{MOD_ID}")
        modelo_atual["s_rx"] = col_s1.slider("Slice Giro X (°)", -180.0, 180.0, float(modelo_atual["s_rx"]), step=5.0, key=f"s_rx_{MOD_ID}")
        modelo_atual["s_ry"] = col_s2.slider("Slice Giro Y (°)", -180.0, 180.0, float(modelo_atual["s_ry"]), step=5.0, key=f"s_ry_{MOD_ID}")
        modelo_atual["s_rz"] = col_s3.slider("Slice Giro Z (°)", -180.0, 180.0, float(modelo_atual["s_rz"]), step=5.0, key=f"s_rz_{MOD_ID}")
        modelo_atual["s_sx"] = col_s1.slider("Slice Escala X", 0.1, 5.0, float(modelo_atual["s_sx"]), step=0.1, key=f"s_sx_{MOD_ID}")
        modelo_atual["s_sy"] = col_s2.slider("Slice Escala Y", 0.1, 5.0, float(modelo_atual["s_sy"]), step=0.1, key=f"s_sy_{MOD_ID}")
        modelo_atual["s_sz"] = col_s3.slider("Slice Escala Z", 0.1, 5.0, float(modelo_atual["s_sz"]), step=0.1, key=f"s_sz_{MOD_ID}")

    with st.expander("🎬 Cena Blender (Pose da Foto - Ultra Rápido)", expanded=True):
        col_r1, col_r2, col_r3 = st.columns(3)
        modelo_atual["r_tx"] = col_r1.number_input("Cena Move X", value=float(modelo_atual["r_tx"]), step=1.0, key=f"r_tx_{MOD_ID}")
        modelo_atual["r_ty"] = col_r2.number_input("Cena Move Y", value=float(modelo_atual["r_ty"]), step=1.0, key=f"r_ty_{MOD_ID}")
        modelo_atual["r_tz"] = col_r3.number_input("Cena Move Z", value=float(modelo_atual["r_tz"]), step=1.0, key=f"r_tz_{MOD_ID}")
        modelo_atual["r_rx"] = col_r1.slider("Cena Giro X (°)", -180.0, 180.0, float(modelo_atual["r_rx"]), step=5.0, key=f"r_rx_{MOD_ID}")
        modelo_atual["r_ry"] = col_r2.slider("Cena Giro Y (°)", -180.0, 180.0, float(modelo_atual["r_ry"]), step=5.0, key=f"r_ry_{MOD_ID}")
        modelo_atual["r_rz"] = col_r3.slider("Cena Giro Z (°)", -180.0, 180.0, float(modelo_atual["r_rz"]), step=5.0, key=f"r_rz_{MOD_ID}")
        modelo_atual["r_sx"] = col_r1.slider("Cena Escala X", 0.1, 5.0, float(modelo_atual["r_sx"]), step=0.1, key=f"r_sx_{MOD_ID}")
        modelo_atual["r_sy"] = col_r2.slider("Cena Escala Y", 0.1, 5.0, float(modelo_atual["r_sy"]), step=0.1, key=f"r_sy_{MOD_ID}")
        modelo_atual["r_sz"] = col_r3.slider("Cena Escala Z", 0.1, 5.0, float(modelo_atual["r_sz"]), step=0.1, key=f"r_sz_{MOD_ID}")

    with st.expander("Cenário e Perfil (Por Modelo)"):
        col_cf1, col_cf2 = st.columns(2)
        perfis_validos = ["020_standard", "012_fine"]
        cenarios_validos = glob.glob("*.blend")
        with col_cf1: modelo_atual["perfil"] = st.selectbox("Perfil PrusaSlicer", perfis_validos, index=perfis_validos.index(modelo_atual["perfil"]) if modelo_atual["perfil"] in perfis_validos else 0, key=f"perfil_{MOD_ID}")
        with col_cf2: modelo_atual["cenario"] = st.selectbox("Cenário (Blender)", cenarios_validos, index=cenarios_validos.index(modelo_atual["cenario"]) if modelo_atual["cenario"] in cenarios_validos else 0, key=f"cenario_{MOD_ID}")

    with st.expander("🎨 Paleta de Materiais Atribuídos", expanded=True):
        materiais_disponiveis = list(perfis_db.get("materiais", {}).keys())
        cols_mat = st.columns(4)
        for i, mat_nome in enumerate(materiais_disponiveis):
            with cols_mat[i % 4]:
                hex_cor = perfis_db["materiais"].get(mat_nome, {}).get("cor_hex", "#808080")
                render_color_badge(mat_nome, hex_cor)
                is_active = mat_nome in modelo_atual["materiais"]
                btn_txt = "➖ Remover" if is_active else "➕ Atribuir"
                if st.button(btn_txt, key=f"btn_mat_{mat_nome}_{MOD_ID}", use_container_width=True):
                    if is_active: modelo_atual["materiais"].remove(mat_nome)
                    else: modelo_atual["materiais"].append(mat_nome)
                    st.rerun()
        if not modelo_atual["materiais"]:
            st.error("⚠️ Escolha pelo menos 1 cor!")
            modelo_atual["materiais"] = ["PLA - Preto"]

        st.divider()
        mat_selecionado_edicao = st.selectbox("Edição de Catálogo: Escolha para editar sliders", materiais_disponiveis)
        mat_edit = perfis_db["materiais"].get(mat_selecionado_edicao, {})
        eh_padrao = mat_selecionado_edicao in MATERIAIS_TRAVADOS
        
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            cor_hex = st.color_picker("Cor", mat_edit.get("cor_hex", "#808080"), key=f"hex_{MOD_ID}")
            roughness = st.slider("Fosco (Rough)", 0.0, 1.0, float(mat_edit.get("roughness", 0.6)), help=TIPS["roughness"], key=f"ro_{MOD_ID}")
        with col_c2:
            metallic = st.slider("Metálico", 0.0, 1.0, float(mat_edit.get("metallic", 0.0)), help=TIPS["metallic"], key=f"me_{MOD_ID}")
            specular = st.slider("Brilho (Spec)", 0.0, 1.0, float(mat_edit.get("specular", 0.5)), help=TIPS["specular"], key=f"sp_{MOD_ID}")
        with col_c3:
            transmission = st.slider("Transmissão (Vidro)", 0.0, 1.0, float(mat_edit.get("transmission", 0.0)), help=TIPS["transmission"], key=f"tr_{MOD_ID}")
            subsurface = st.slider("Pele/Cera (Subsurf)", 0.0, 1.0, float(mat_edit.get("subsurface", 0.0)), help=TIPS["subsurface"], key=f"su_{MOD_ID}")
        
        material_atual_estado = {"cor_hex": cor_hex, "roughness": roughness, "specular": specular, "metallic": metallic, "transmission": transmission, "subsurface": subsurface}
        if not eh_padrao:
            if perfis_db["materiais"][mat_selecionado_edicao] != material_atual_estado:
                perfis_db["materiais"][mat_selecionado_edicao] = material_atual_estado
                salvar_json_silencioso(perfis_db)
        
        st.divider()
        col_n1, col_n2 = st.columns([3, 1])
        nome_sugerido = f"Cópia de {mat_selecionado_edicao}" if eh_padrao else f"{mat_selecionado_edicao} Novo"
        novo_nome_mat = col_n1.text_input("Nome para salvar:", value=nome_sugerido, key=f"new_{MOD_ID}")
        pode_salvar = novo_nome_mat not in MATERIAIS_TRAVADOS and novo_nome_mat not in perfis_db["materiais"]
        if col_n2.button("➕ Adicionar", disabled=not pode_salvar, use_container_width=True):
            perfis_db["materiais"][novo_nome_mat] = material_atual_estado
            salvar_json_silencioso(perfis_db)
            st.success(f"Material '{novo_nome_mat}' adicionado ao catálogo!")
            st.rerun()

    with st.expander("⚙️ Configurações Globais (Todos os modelos)", expanded=False):
        auto_orient = st.checkbox("Auto-Orientação (-ao)", value=bool(perfis_db["config_app"]["auto_orient"]))
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1: samples = st.number_input("Samples Produção", min_value=1, value=int(perfis_db["config_app"]["samples"]))
        with col_r2: res_producao = st.number_input("Resolução (%)", min_value=10, max_value=200, value=int(perfis_db["config_app"]["res_producao"]), step=10)
        with col_r3: max_time = st.number_input("Max. Segundos", min_value=0, value=int(perfis_db["config_app"]["max_time"]))
        perfis_db["config_app"].update({ "auto_orient": auto_orient, "samples": samples, "res_producao": res_producao, "max_time": max_time })

with col_direita:
    col_b1, col_bcfg, col_b2, col_bcan = st.columns([1.5, 0.4, 1.5, 1])
    with col_b1:
        btn_preview = st.button("📸 Forçar Preview Agora", use_container_width=True)
    with col_bcfg:
        with st.popover("⚙️"):
            p_res = st.number_input("Res % Preview", value=perfis_db["config_app"]["prev_res"])
            p_sam = st.number_input("Samples Prev", value=perfis_db["config_app"]["prev_samples"])
            auto_preview = st.toggle("🔄 Auto-Update", value=bool(perfis_db["config_app"].get("auto_preview_toggle", False)))
            if p_res != perfis_db["config_app"]["prev_res"] or p_sam != perfis_db["config_app"]["prev_samples"] or auto_preview != perfis_db["config_app"].get("auto_preview_toggle"):
                perfis_db["config_app"].update({"prev_res": p_res, "prev_samples": p_sam, "auto_preview_toggle": auto_preview})
                salvar_json_silencioso(perfis_db)

    with col_b2:
        btn_producao = st.button("🚀 INICIAR FILA DE PRODUÇÃO", type="primary", use_container_width=True)
    with col_bcan:
        if st.button("🛑 Cancelar", type="secondary", use_container_width=True):
            st.session_state.cancelar_fila = True

    barra_progresso = st.progress(0, text="Motor aguardando...")
    st.divider()

    class DummyPlaceholder:
        def info(self, *args, **kwargs): pass
        def warning(self, *args, **kwargs): pass
        def image(self, *args, **kwargs): pass
        def empty(self): pass
        def download_button(self, *args, **kwargs): pass

    preview_expander = st.empty()
    if not st.session_state.executando_lote:
        with preview_expander.container():
            st.subheader(f"👁️ Visualizador: {st.session_state.modelo_ativo}")
            prev_c1, prev_c2 = st.columns(2)
            with prev_c1:
                ph_timer_frente = st.empty()
                ph_img_frente = st.empty()
                ph_img_frente.info("Câmera Frente aparecerá aqui.")
                btn_down_frente = st.empty()
            with prev_c2:
                ph_timer_macro = st.empty()
                ph_img_macro = st.empty()
                ph_img_macro.info("Câmera Macro aparecerá aqui.")
                btn_down_macro = st.empty()
    else:
        preview_expander.empty()
        ph_timer_frente = DummyPlaceholder()
        ph_timer_macro = DummyPlaceholder()
        ph_img_frente = DummyPlaceholder()
        ph_img_macro = DummyPlaceholder()
        btn_down_frente = DummyPlaceholder()
        btn_down_macro = DummyPlaceholder()

    st.divider()
    st.subheader("🏭 Galeria de Produção em Lote")
    batch_grid_container = st.empty()

    st.sidebar.markdown("---")
    st.sidebar.caption("💻 Terminal Debug Log")
    log_container = st.sidebar.container(height=300)
    console_log = log_container.empty()
    console_log.code(st.session_state.log_historico[-4000:], language='bash')
    btn_download_log = st.sidebar.empty()

# =====================================================================
# MOTOR DE EXECUÇÃO
# =====================================================================
salvar_json_silencioso(perfis_db)

if auto_preview: st.session_state.disparar_preview = True 

if btn_preview or btn_producao or (auto_preview and st.session_state.disparar_preview):
    st.session_state.disparar_preview = False 
    st.session_state.cancelar_fila = False
    
    if btn_producao:
        st.session_state.executando_lote = True
        preview_expander.empty()

    if btn_preview or (auto_preview and not st.session_state.executando_lote):
        if auto_preview and not btn_preview:
            cooldown_time = 5
            for i in range(cooldown_time, 0, -1):
                ph_timer_frente.warning(f"⏳ Cooldown: Aguardando {i}s sem mexer na tela...")
                ph_timer_macro.warning(f"⏳ Auto-Render em breve...")
                time.sleep(1) 
            ph_timer_frente.empty()
            ph_timer_macro.empty()

        ph_img_frente.info("⏳ Processando Preview (Frente)...")
        ph_img_macro.info("⏳ Processando Preview (Macro)...")
        lista_modelos = [(st.session_state.modelo_ativo, modelo_atual)]
        matriz_materiais = [modelo_atual["materiais"][0]] if modelo_atual["materiais"] else ["PLA - Preto"]
        resolucao_exec, samples_exec = str(p_res), str(p_sam)
        cameras_exec = "Cam_Frente,Cam_Macro"
        is_prev_flag = True
        total_tasks = 1 
    else:
        lista_modelos = list(st.session_state.db_modelos.items())
        resolucao_exec, samples_exec = str(res_producao), str(samples)
        
        # BUG FIX: AS 4 CÂMERAS SÃO EXIGIDAS PARA A PRODUÇÃO AGORA!
        cameras_exec = "Cam_Frente,Cam_45,Cam_Topo,Cam_Macro" 
        cam_list = cameras_exec.split(",")
        is_prev_flag = False
        
        # O número total de tarefas é o número de materiais
        total_tasks = sum(len(dados["materiais"]) for _, dados in lista_modelos)
        
        # A grade de Loading agora gera 4 Skeletons por material (1 para cada câmera!)
        placeholders_batch = []
        task_idx_calc = 0
        with batch_grid_container.container():
            cols = st.columns(4) 
            for nome_arq, dados_mod in lista_modelos:
                for mat_batch in dados_mod["materiais"]:
                    for c_name in cam_list:
                        task_idx_calc += 1
                        placeholders_batch.append((IMG_LOADING_SKEL, f"⏳ {mat_batch} ({c_name})"))
                        cols[(task_idx_calc - 1) % 4].image(IMG_LOADING_SKEL, caption=f"⏳ {mat_batch} ({c_name})", use_container_width=True)

    st.session_state.log_historico += f"\n=== INICIO DA EXECUÇÃO ({datetime.now().strftime('%H:%M:%S')}) ===\n"
    
    task_atual = 0
    out_dir_final = None
    imagens_batch_concluidas = [] 
    processo = None

    for nome_arq, dados_arq in lista_modelos:
        if st.session_state.cancelar_fila: break
        caminho_base = os.path.join(PASTA_TEMP, nome_arq)
        
        for mat in matriz_materiais if is_prev_flag else dados_arq["materiais"]:
            if st.session_state.cancelar_fila: break
            
            task_atual += 1
            barra_progresso.progress(int((task_atual / total_tasks) * 100), text=f"[{task_atual}/{total_tasks}] Processando: {nome_arq} | {mat}")
            
            comando = [
                "python", "pipeline.py", "--file", caminho_base, "--profile", dados_arq["perfil"],
                "--material", mat, "--scale", "1.0", "--samples", samples_exec, 
                "--time", str(max_time), "--scene", dados_arq["cenario"], "--res", resolucao_exec,
                "--cameras", cameras_exec,
                "--s_tx", str(dados_arq["s_tx"]), "--s_ty", str(dados_arq["s_ty"]), "--s_tz", str(dados_arq["s_tz"]),
                "--s_rx", str(dados_arq["s_rx"]), "--s_ry", str(dados_arq["s_ry"]), "--s_rz", str(dados_arq["s_rz"]),
                "--s_sx", str(dados_arq["s_sx"]), "--s_sy", str(dados_arq["s_sy"]), "--s_sz", str(dados_arq["s_sz"]),
                "--r_tx", str(dados_arq["r_tx"]), "--r_ty", str(dados_arq["r_ty"]), "--r_tz", str(dados_arq["r_tz"]),
                "--r_rx", str(dados_arq["r_rx"]), "--r_ry", str(dados_arq["r_ry"]), "--r_rz", str(dados_arq["r_rz"]),
                "--r_sx", str(dados_arq["r_sx"]), "--r_sy", str(dados_arq["r_sy"]), "--r_sz", str(dados_arq["r_sz"])
            ]
            if auto_orient: comando.append("-ao")
            if is_prev_flag: comando.append("--is_preview") 
                
            try:
                processo = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', bufsize=1)
                
                # Leitor Universal Dinâmico (Lê TODAS as câmeras sem hardcode)
                for linha in processo.stdout:
                    st.session_state.log_historico += linha
                    console_log.code(st.session_state.log_historico[-4000:], language='bash')
                    
                    if "###OUT_DIR###" in linha: out_dir_final = linha.split("###OUT_DIR###")[1].strip()
                    elif "###SAVED_IMG_PATH###" in linha:
                        partes = linha.strip().split("###")
                        if len(partes) >= 4:
                            cam_code = partes[2].strip()
                            img_path = partes[3].strip()
                            
                            time.sleep(0.2) 
                            if os.path.exists(img_path):
                                if is_prev_flag:
                                    if "FRENTE" in cam_code:
                                        ph_img_frente.image(img_path, caption=f"Frente ({mat})", use_container_width=True)
                                        with open(img_path, "rb") as file: btn_down_frente.download_button(label="⬇️ Baixar Frente", data=file.read(), file_name=os.path.basename(img_path), mime="image/png", key=f"dl_f_{task_atual}")
                                    elif "MACRO" in cam_code:
                                        ph_img_macro.image(img_path, caption=f"Macro ({mat})", use_container_width=True)
                                else:
                                    # LOTE: Adiciona na lista geral
                                    imagens_batch_concluidas.append((img_path, f"{cam_code} - {mat}"))
                                    
                                    if st.session_state.executando_lote:
                                        with batch_grid_container.container():
                                            current_total_gen = []
                                            for i, p_batch in enumerate(placeholders_batch):
                                                if i < len(imagens_batch_concluidas): current_total_gen.append(imagens_batch_concluidas[i])
                                                else: current_total_gen.append(p_batch)
                                            cols = st.columns(4)
                                            for idx, (img_p, cap) in enumerate(current_total_gen):
                                                cols[idx % 4].image(img_p, caption=cap, use_container_width=True)
                processo.wait()
            
            finally:
                if processo is not None and processo.poll() is None:
                    processo.kill()

    if st.session_state.cancelar_fila:
        barra_progresso.progress(100, text=f"❌ Fila Cancelada!")
        st.session_state.cancelar_fila = False
    else:
        barra_progresso.progress(100, text=f"✅ Concluído!")
        if btn_producao: st.balloons()
    
    btn_download_log.download_button("📄 Baixar Log Completo da Sessão", data=st.session_state.log_historico, file_name=f"debug_log_{datetime.now().strftime('%H_%M')}.txt", use_container_width=True)
    st.session_state.executando_lote = False