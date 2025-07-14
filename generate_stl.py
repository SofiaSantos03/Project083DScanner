# --- START OF FILE generate_stl.py ---

import numpy as np
import open3d as o3d

# Esta é a única função no ficheiro, projetada para ser importada e usada por outro script.
def generate_mesh(input_filepath, output_filepath):
    """
    Carrega uma nuvem de pontos, processa-a com Open3D e gera uma malha
    usando o algoritmo Ball-Pivoting.
    """
    print(f"\n A iniciar a geração da malha a partir de '{input_filepath}' (Usando Open3D)")
    print(f" -> O ficheiro de saída será '{output_filepath}'")

    # 1. CARREGAR A NUVEM DE PONTOS
    try:
        points = np.loadtxt(input_filepath, delimiter=",")
        if points.shape[0] < 20:
            print("[Erro] O ficheiro da nuvem de pontos contém muito poucos pontos.")
            return
        print(f"Nuvem de pontos carregada com {points.shape[0]} pontos.")
    except Exception as e:
        print(f"[Erro] Falha ao carregar o ficheiro '{input_filepath}': {e}")
        return

    # 2. PREPARAR A NUVEM DE PONTOS
    points = points / 1000.0
    print("Pontos convertidos de milímetros para metros.")
    
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    
    print("A filtrar outliers estatísticos...")
    cl, ind = pcd.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)
    pcd = pcd.select_by_index(ind)
    print(f"Filtragem concluída. Restam {len(pcd.points)} pontos.")
    
    # 3. CALCULAR AS NORMAIS
    print("A estimar as normais dos pontos...")
    pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.05, max_nn=30))
    pcd.orient_normals_consistent_tangent_plane(k=30)
    print("Normais estimadas e orientadas.")
    
    # 4. GERAR A MALHA
    print("A gerar a malha com o algoritmo Ball-Pivoting...")
    radii = [0.005, 0.01, 0.02, 0.04]
    mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
        pcd, o3d.utility.DoubleVector(radii))
    
    if len(mesh.triangles) == 0:
        print("[ERRO] A geração da malha falhou. Nenhum triângulo foi criado.")
        return
        
    print(f"Malha criada com {len(mesh.triangles)} triângulos.")

    # 5. GUARDAR A MALHA
    o3d.io.write_triangle_mesh(output_filepath, mesh)
    print(f"\n[SUCESSO] Malha 3D exportada para '{output_filepath}'.")

    # 6. VISUALIZAÇÃO
    print("A abrir visualizador 3D...")
    pcd.paint_uniform_color([1, 0.706, 0])
    o3d.visualization.draw_geometries([pcd, mesh])