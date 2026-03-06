import bpy
import sys
import os
import json
import math

try:
    argv = sys.argv
    index = argv.index("--") + 1
except ValueError:
    print("❌ Erro: Argumentos do script Blender não encontrados.")
    sys.exit(1)

# Leitura dos argumentos básicos
stl_path = argv[index]
material_name = argv[index + 1]
output_prefix = argv[index + 2]
quality_samples = int(argv[index + 3])
max_time_sec = int(argv[index + 4])
blend_save_path = argv[index + 5]
escala_cli = float(argv[index + 6])
json_config_path = argv[index + 7]
res_percent = int(argv[index + 8])
cameras_str = argv[index + 9]
is_thumb = (argv[index + 10].lower() == 'true')

# Leitura das Transformações do BLENDER (Cena)
r_tx = float(argv[index + 11])
r_ty = float(argv[index + 12])
r_tz = float(argv[index + 13])
r_rx = float(argv[index + 14])
r_ry = float(argv[index + 15])
r_rz = float(argv[index + 16])
r_sx = float(argv[index + 17])
r_sy = float(argv[index + 18])
r_sz = float(argv[index + 19])

RENDER_EEVEE_THUMB = True 

print(f"🎬 Iniciando Estúdio no Blender para: {stl_path}")

# PARTE 1: Importação
bpy.ops.wm.stl_import(filepath=stl_path)
if len(bpy.context.selected_objects) > 1:
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.join()
obj = bpy.context.selected_objects[0]
obj.name = "Produto_Render"

with open(json_config_path, 'r', encoding='utf-8') as f:
    perfis = json.load(f)
config_global = perfis.get("config_global", {})
material_data = perfis.get("materiais", {}).get(material_name, perfis["materiais"].get("PLA - Preto", {}))

# === CÁLCULO DE ESCALA ===
escala_final_multiplicador = config_global.get("escala_padrao", 1.0) * escala_cli

max_dim = max(obj.dimensions.x, obj.dimensions.y, obj.dimensions.z)
if max_dim > 0:
    base_scale = 0.1 / max_dim 
else:
    base_scale = 1.0
    
final_scale = base_scale * escala_final_multiplicador

# === CORREÇÃO CRÍTICA DA ORDEM DE TRANSFORMAÇÃO ===
# 1. Primeiro aplicamos a Escala (Encolhendo o modelo gigante do fatiador)
obj.scale = (final_scale * r_sx, final_scale * r_sy, final_scale * r_sz)

# 2. Aplicamos a Rotação do Blender
obj.rotation_euler = (math.radians(r_rx), math.radians(r_ry), math.radians(r_rz))

# 3. Forçamos o Blender a recalcular as dimensões REAIS da peça AGORA que ela foi escalada e girada
bpy.context.view_layer.update()

# 4. Translação proporcional (Normalizamos o slider da interface para o tamanho em escala do estúdio)
offset_x = r_tx * base_scale
offset_y = r_ty * base_scale
offset_z = r_tz * base_scale

if not is_thumb:
    # Centraliza o pivot no bounding box exato da peça
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    # Move para o piso exato da cena, compensando o offset do usuário
    obj.location = (offset_x, offset_y, (obj.dimensions.z / 2.0) + offset_z)
else:
    obj.location.x += offset_x
    obj.location.y += offset_y
    obj.location.z += offset_z

# Atualiza a cena final antes de renderizar
bpy.context.view_layer.update()

# Correção de Normais (força bruta para opacidade)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()

# PARTE 3: Material Opaco
mat = bpy.data.materials.new(name=f"Material_{material_name}")
mat.use_nodes = True
bsdf = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)

if not bsdf:
    bsdf = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
    output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
    mat.node_tree.links.new(bsdf.outputs[0], output.inputs[0])

h = material_data.get("cor_hex", "#808080").lstrip('#')
rgb = tuple(int(h[i:i+2], 16)/255.0 for i in (0, 2, 4))

def set_node_value(node, possible_names, value):
    for name in possible_names:
        if name in node.inputs:
            node.inputs[name].default_value = value
            return

set_node_value(bsdf, ['Base Color'], (*rgb, 1.0))
set_node_value(bsdf, ['Roughness'], material_data.get("roughness", 0.6))
set_node_value(bsdf, ['Metallic'], material_data.get("metallic", 0.0))
set_node_value(bsdf, ['Specular IOR Level', 'Specular'], material_data.get("specular", 0.5))
set_node_value(bsdf, ['Transmission Weight', 'Transmission'], material_data.get("transmission", 0.0))
set_node_value(bsdf, ['Subsurface Weight', 'Subsurface'], material_data.get("subsurface", 0.0))
set_node_value(bsdf, ['Alpha'], material_data.get("alpha", 1.0))

obj.data.materials.append(mat)

# PARTE 4: Renderização
multiplicador_luz = config_global.get("multiplicador_luz_cena", 1.0)
if multiplicador_luz != 1.0:
    for light in bpy.data.lights: light.energy = light.energy * multiplicador_luz

if is_thumb and RENDER_EEVEE_THUMB:
    try: bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except: bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.context.scene.eevee.taa_render_samples = 4
    bpy.context.scene.render.resolution_percentage = 25
else:
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.device = 'GPU'
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'CUDA' 
        prefs.get_devices()
        for d in prefs.devices: d.use = True
    except: pass
    bpy.context.scene.cycles.samples = quality_samples
    bpy.context.scene.cycles.use_denoising = True
    bpy.context.scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    if max_time_sec > 0: bpy.context.scene.cycles.time_limit = max_time_sec
    bpy.context.scene.render.resolution_percentage = res_percent

# PARTE 5: Salvar e Exportar
if not is_thumb:
    bpy.ops.wm.save_as_mainfile(filepath=blend_save_path)

cameras_list = cameras_str.split(',')
for cam_name in cameras_list:
    cam_name = cam_name.strip()
    if cam_name in bpy.data.objects:
        bpy.context.scene.camera = bpy.data.objects[cam_name]
        bpy.context.scene.render.filepath = f"{output_prefix}_{cam_name}.png"
        bpy.ops.render.render(write_still=True)
        print(f"###SAVED_IMG_PATH###{cam_name.upper()}###{bpy.context.scene.render.filepath}")

print("✅ Workflow do Blender concluído.")