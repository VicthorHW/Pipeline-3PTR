import trimesh
import math
import argparse
import sys

# Vacina contra o terminal do Windows
sys.stdout.reconfigure(encoding='utf-8')

def orientar(input_path, output_path, auto=False, tx=0.0, ty=0.0, tz=0.0, rx=0.0, ry=0.0, rz=0.0, sx=1.0, sy=1.0, sz=1.0):
    mesh = trimesh.load(input_path)

    # 1. ESCALA (Scale)
    if sx != 1.0 or sy != 1.0 or sz != 1.0:
        matriz_escala = trimesh.transformations.scale_and_translate(scale=[sx, sy, sz])
        mesh.apply_transform(matriz_escala)

    # 2. ROTAÇÃO (Rotation)
    if auto and rx == 0 and ry == 0 and rz == 0:
        print(f"🔄 Aplicando orientação automática em {input_path}...")
        stable_poses, probs = mesh.compute_stable_poses()
        mesh.apply_transform(stable_poses[0])
    elif rx != 0 or ry != 0 or rz != 0:
        print(f"🔄 Aplicando rotação manual: X={rx}°, Y={ry}°, Z={rz}°...")
        rad_x = math.radians(rx)
        rad_y = math.radians(ry)
        rad_z = math.radians(rz)
        matriz_rotacao = trimesh.transformations.euler_matrix(rad_x, rad_y, rad_z, 'sxyz')
        mesh.apply_transform(matriz_rotacao)
    else:
        print(f"⏩ Mantendo orientação original.")

    # 3. TRANSLAÇÃO (Translation) + Encostar no chão
    min_z = mesh.bounds[0][2]
    # Move para o TX, TY solicitados, e no TZ ele compensa a base para não afundar no chão
    mesh.apply_translation([tx, ty, tz - min_z])

    mesh.export(output_path)
    print(f"✅ STL processado e salvo em: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--auto", action="store_true", help="Ativa a auto-orientação")
    
    # Rotação
    parser.add_argument("--rx", type=float, default=0.0)
    parser.add_argument("--ry", type=float, default=0.0)
    parser.add_argument("--rz", type=float, default=0.0)
    
    # Translação
    parser.add_argument("--tx", type=float, default=0.0)
    parser.add_argument("--ty", type=float, default=0.0)
    parser.add_argument("--tz", type=float, default=0.0)
    
    # Escala
    parser.add_argument("--sx", type=float, default=1.0)
    parser.add_argument("--sy", type=float, default=1.0)
    parser.add_argument("--sz", type=float, default=1.0)
    
    args = parser.parse_args()
    orientar(args.input, args.output, args.auto, args.tx, args.ty, args.tz, args.rx, args.ry, args.rz, args.sx, args.sy, args.sz)