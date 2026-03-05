import bpy
import sys
import os

try:
    argv = sys.argv
    index = argv.index("--") + 1
except ValueError:
    print("❌ Erro: Argumentos do script Blender não encontrados.")
    sys.exit(1)

stl_path = argv[index]
color_hex = argv[index + 1]
output_prefix = argv[index + 2]

print(f"🎬 Iniciando Renderização no Blender para: {stl_path}")

# ==============================================================================
# PARTE 1: Importação e "Bounding Box" (A Caixa Limite de 10cm)
# ==============================================================================
bpy.ops.wm.stl_import(filepath=stl_path)
obj = bpy.context.selected_objects[0]
obj.name = "Produto_Render"

# CORREÇÃO: Blender usa Metros. 100mm = 0.1m. 
max_dim = max(obj.dimensions.x, obj.dimensions.y, obj.dimensions.z)
if max_dim > 0:
    scale_factor = 0.1 / max_dim 
    obj.scale = (scale_factor, scale_factor, scale_factor)

bpy.context.view_layer.update()

# ==============================================================================
# PARTE 2: Alinhamento Geométrico
# ==============================================================================
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
obj.location = (0, 0, 0)
obj.location.z = obj.dimensions.z / 2.0
bpy.context.view_layer.update()

# ==============================================================================
# PARTE 3: Material Dinâmico
# ==============================================================================
mat = bpy.data.materials.new(name="Material_Filamento")
if not mat.use_nodes:
    mat.use_nodes = True

bsdf = None
for node in mat.node_tree.nodes:
    if node.type == 'BSDF_PRINCIPLED':
        bsdf = node
        break

if not bsdf:
    bsdf = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
    output = next((n for n in mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if not output:
        output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
    mat.node_tree.links.new(bsdf.outputs[0], output.inputs[0])

h = color_hex.lstrip('#')
rgb = tuple(int(h[i:i+2], 16)/255.0 for i in (0, 2, 4))
bsdf.inputs['Base Color'].default_value = (*rgb, 1.0)
bsdf.inputs['Roughness'].default_value = 0.6 
obj.data.materials.append(mat)

# ==============================================================================
# PARTE 4: OTIMIZAÇÃO EXTREMA DE RENDER (Foco em Velocidade)
# ==============================================================================
bpy.context.scene.render.engine = 'CYCLES'

# 1. Força o uso de GPU
bpy.context.scene.cycles.device = 'GPU'
prefs = bpy.context.preferences.addons['cycles'].preferences
# Tenta ativar CUDA (Nvidia) ou OptiX
try:
    prefs.compute_device_type = 'CUDA' 
    prefs.get_devices()
    for d in prefs.devices:
        d.use = True
except:
    pass # Falback silencioso caso não seja Nvidia

# 2. Configurações de Qualidade vs Tempo (Render em ~10s)
bpy.context.scene.cycles.samples = 32          # Baixíssimo (Padrão é 4096)
bpy.context.scene.cycles.use_denoising = True  # IA limpa a imagem
bpy.context.scene.cycles.denoiser = 'OPENIMAGEDENOISE'
bpy.context.scene.cycles.max_bounces = 4       # Menos cálculo de luz quicando

# ==============================================================================
# PARTE 5: Loop de Câmeras e Salvar
# ==============================================================================
cameras = ["Cam_Frente", "Cam_45", "Cam_Topo", "Cam_Macro"]

for cam_name in cameras:
    if cam_name in bpy.data.objects:
        cam_obj = bpy.data.objects[cam_name]
        bpy.context.scene.camera = cam_obj
        
        img_path = f"{output_prefix}_{cam_name}.png"
        bpy.context.scene.render.filepath = img_path
        
        print(f"📸 Renderizando {cam_name} rápido...")
        bpy.ops.render.render(write_still=True)
    else:
        print(f"⚠️ Aviso: Câmera '{cam_name}' não encontrada no template!")

print("✅ Renderização rápida concluída.")