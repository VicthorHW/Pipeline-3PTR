import argparse
import numpy as np
import trimesh
import re

def convert_gcode_to_stl(input_gcode, output_stl, quality=4):
    print(f"📦 Filtrando e convertendo: {input_gcode}")
    
    path_points = []
    curr = [0.0, 0.0, 0.0]
    
    # INICIALIZAÇÃO CORRETA: Começamos assumindo que NÃO estamos no objeto 
    # (isso ignora automaticamente a linha de purga inicial)
    is_printing_object = False 

    regex_x = re.compile(r'X([-+]?\d*\.\d+|\d+)')
    regex_y = re.compile(r'Y([-+]?\d*\.\d+|\d+)')
    regex_z = re.compile(r'Z([-+]?\d*\.\d+|\d+)')
    regex_e = re.compile(r'E([-+]?\d*\.\d+|\d+)')

    with open(input_gcode, 'r') as f:
        for line in f:
            clean_line = line.strip()

            # 1. LÓGICA DE FILTRAGEM (Remove Skirt, Purga e Movimentos Customizados)
            if ";TYPE:" in clean_line:
                # Se o slicer avisar que é perímetro ou preenchimento, ativamos a gravação
                if any(x in clean_line for x in ["Perimeter", "Infill", "Top solid infill", "Solid infill"]):
                    is_printing_object = True
                else:
                    # Se for Skirt, Brim ou Support, desativamos
                    is_printing_object = False
                continue # Pula a linha do comentário em si

            # Extrair valores (se existirem na linha)
            x_m = regex_x.search(line)
            y_m = regex_y.search(line)
            z_m = regex_z.search(line)
            e_m = regex_e.search(line)
            
            # Precisamos sempre atualizar a posição do "bico", mesmo quando não 
            # estamos gravando, para a próxima linha começar do lugar certo.
            new_pos = curr.copy()
            if x_m: new_pos[0] = float(x_m.group(1))
            if y_m: new_pos[1] = float(y_m.group(1))
            if z_m: new_pos[2] = float(z_m.group(1))

            # 2. SÓ ADICIONA GEOMETRIA SE FOR O OBJETO E HOUVER EXTRUSÃO (E > 0)
            if is_printing_object and e_m and float(e_m.group(1)) > 0:
                p1, p2 = np.array(curr), np.array(new_pos)
                # Só cria o segmento se houver deslocamento real (evita pontos duplicados)
                if np.linalg.norm(p2 - p1) > 0.01:
                    path_points.append((p1, p2))
            
            curr = new_pos

    if not path_points:
        print("❌ Falha: Nenhuma extrusão válida do objeto foi encontrada no G-code.")
        return

    print(f"🛠️ Gerando malha para {len(path_points)} segmentos (isso pode levar alguns segundos)...")
    
    segments = []
    for p1, p2 in path_points:
        dist = np.linalg.norm(p2 - p1)
        cyl = trimesh.creation.cylinder(radius=0.2, height=dist, sections=quality)
        direction = p2 - p1
        translation = (p1 + p2) / 2
        matrix = trimesh.geometry.align_vectors([0, 0, 1], direction)
        matrix[:3, 3] = translation
        cyl.apply_transform(matrix)
        segments.append(cyl)

    # Unifica tudo em um único objeto 3D
    mesh = trimesh.util.concatenate(segments)
    mesh.merge_vertices() # Otimiza removendo pontos sobrepostos
    mesh.export(output_stl)
    print(f"✅ STL gerado com sucesso: {output_stl}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--quality", type=int, default=4)
    args = parser.parse_args()
    
    convert_gcode_to_stl(args.input, args.output, args.quality)