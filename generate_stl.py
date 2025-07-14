
import numpy as np
import open3d as o3d

def generate_mesh(input_filepath="3dScanner_Data.txt", output_filepath="scanner_output.stl"):
    """
    Carrega uma nuvem de pontos e gera uma malha, adaptado para funcionar
    com a versão específica do Open3D instalada.
    """
    print(f"\n A iniciar a geração da malha a partir de '{input_filepath}' (Modo Compatível)")

    try:
        points = np.loadtxt(input_filepath, delimiter=",")
        if points.shape[0] == 0:
            print("[Erro] O ficheiro da nuvem de pontos está vazio.")
            return
        print(f"Nuvem de pontos carregada com {points.shape[0]} pontos.")
    except Exception as e:
        print(f"[Erro] Falha ao carregar o ficheiro '{input_filepath}': {e}")
        return

    points = points / 1000.0
    print("Pontos convertidos de milímetros para metros.")
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    
    print("A filtrar outliers...")
    cl, ind = pcd.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)
    pcd = pcd.select_by_index(ind)
    print(f"Filtragem concluída. Restam {len(pcd.points)} pontos.")
    
    print("A estimar as normais dos pontos...")
    pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
    pcd.orient_normals_consistent_tangent_plane(k=30)
    print("Normais estimadas e orientadas.")
    
    print("A gerar a malha com o algoritmo Ball-Pivoting...")
    radii = [0.01, 0.02, 0.04, 0.08] # serve para ajustar a resolução da malha ou seja o tamanho dos triângulos
    mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
        pcd, o3d.utility.DoubleVector(radii))
    print(f"Malha criada com {len(mesh.triangles)} triângulos.")

    print("A otimizar a malha (funções compatíveis)...")
    
    mesh.remove_degenerate_triangles()
    
    # As linhas seguintes foram comentadas, pois podem não existir na versão do Open3D 0.19.0 instalada.
    # mesh.remove_duplicate_triangles()
    # mesh.remove_duplicate_vertices()
    
    mesh.remove_unreferenced_vertices()
    print("Otimização concluída.")


    o3d.io.write_triangle_mesh(output_filepath, mesh)
    print(f"\n[SUCESSO] Malha 3D (não otimizada) exportada para '{output_filepath}'.")

    print("A abrir visualizador 3D...")
    pcd.paint_uniform_color([1, 0.706, 0])
    o3d.visualization.draw_geometries([pcd, mesh])