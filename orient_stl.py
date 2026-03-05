import trimesh
import math
import argparse

def orientar(input_path, output_path, auto=True, rx=0, ry=0, rz=0):
    mesh = trimesh.load(input_path)

    # Se a opção automática estiver ligada e nenhum ângulo foi passado
    if auto and rx == 0 and ry == 0 and rz == 0:
        print(f"🔄 Aplicando orientação automática em {input_path}...")
        stable_poses, probs = mesh.compute_stable_poses()
        mesh.apply_transform(stable_poses[0])
    else:
        print(f"🔄 Aplicando rotação manual: X={rx}°, Y={ry}°, Z={rz}°...")
        
        # Converte graus para radianos (necessário para a matriz matemática)
        rad_x = math.radians(rx)
        rad_y = math.radians(ry)
        rad_z = math.radians(rz)
        
        # Cria a matriz de rotação nos três eixos (padrão 'sxyz')
        matriz_rotacao = trimesh.transformations.euler_matrix(rad_x, rad_y, rad_z, 'sxyz')
        mesh.apply_transform(matriz_rotacao)

    # Passo final: Garante que a base do objeto fique encostada no chão (Z=0)
    min_z = mesh.bounds[0][2]
    mesh.apply_translation([0, 0, -min_z])

    mesh.export(output_path)
    print(f"✅ STL orientado salvo em: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--no-auto", action="store_true")
    parser.add_argument("--rx", type=float, default=0.0)
    parser.add_argument("--ry", type=float, default=0.0)
    parser.add_argument("--rz", type=float, default=0.0)
    args = parser.parse_args()

    auto_mode = not args.no_auto
    orientar(args.input, args.output, auto_mode, args.rx, args.ry, args.rz)