# --- START OF FILE generate_stl.py ---

import numpy as np
import open3d as o3d
from scipy.interpolate import splprep, splev

def build_universal_solid(input_filepath, output_filepath):
    """
    Constrói uma malha 3D sólida e fechada a partir de uma nuvem de pontos,
    garantindo tampas perfeitamente planas através de triangulação em leque.
    """
    print(f"\n A iniciar a construção da malha a partir de '{input_filepath}'")
    
    # --- PASSO 1: Carregar os Dados ---
    try:
        points_mm = np.loadtxt(input_filepath, delimiter=",")
        if points_mm.shape[0] < 50:
            print(f"[Erro] Ficheiro contém muito poucos pontos ({points_mm.shape[0]}). A abortar.")
            return
        print(f"Nuvem de pontos carregada com {points_mm.shape[0]} pontos.")
    except Exception as e:
        print(f"[Erro] Falha ao carregar o ficheiro '{input_filepath}': {e}")
        return

    # --- PASSO 2: Separar Pontos em Camadas ---
    print("A separar os pontos em camadas...")
    layers = []
    if len(points_mm) > 0:
        current_layer = [points_mm[0]]
        for i in range(1, len(points_mm)):
            if abs(points_mm[i, 2] - current_layer[0][2]) > 0.1:
                if len(current_layer) > 10:
                    layers.append(np.array(current_layer))
                current_layer = []
            current_layer.append(points_mm[i])
        if len(current_layer) > 10:
            layers.append(np.array(current_layer))
    print(f"Detectadas {len(layers)} camadas válidas.")

    if len(layers) < 2:
        print("[ERRO] Não foram detectadas camadas suficientes (precisa de pelo menos 2).")
        return

    # --- PASSO 3: RECONSTRUIR CADA CAMADA COM SPLINES ---
    print("A reconstruir o contorno de cada camada com splines...")
    resampled_layers = []
    num_points_per_layer = 180 

    for layer in layers:
        points_2d = layer[:, :2]
        center_2d = np.mean(points_2d, axis=0)
        angles = np.arctan2(points_2d[:, 1] - center_2d[1], points_2d[:, 0] - center_2d[0])
        sorted_indices = np.argsort(angles)
        sorted_points_2d = points_2d[sorted_indices]
        tck, u = splprep([sorted_points_2d[:, 0], sorted_points_2d[:, 1]], s=3.0, per=True)
        
        # <-- A CORREÇÃO ESTÁ AQUI: Adicionar `endpoint=False`
        # Isto evita a criação de um vértice duplicado no final de cada anel.
        u_new = np.linspace(u.min(), u.max(), num_points_per_layer, endpoint=False)
        
        x_new, y_new = splev(u_new, tck, der=0)
        z_mean = np.mean(layer[:, 2])
        resampled_layer = np.vstack((x_new, y_new, np.full(num_points_per_layer, z_mean))).T
        resampled_layers.append(resampled_layer)

    # --- PASSO 4: CONSTRUIR VÉRTICES E PAREDES ---
    print("A construir as paredes da malha...")
    all_vertices = np.vstack(resampled_layers)
    all_triangles = []

    for i in range(len(resampled_layers) - 1):
        lower_layer_start_index = i * num_points_per_layer
        upper_layer_start_index = (i + 1) * num_points_per_layer
        
        for j in range(num_points_per_layer):
            p1 = lower_layer_start_index + j
            p2 = lower_layer_start_index + (j + 1) % num_points_per_layer
            p3 = upper_layer_start_index + j
            p4 = upper_layer_start_index + (j + 1) % num_points_per_layer
            
            all_triangles.append([p1, p2, p3])
            all_triangles.append([p2, p4, p3])

    # --- PASSO 5: CRIAR TAMPAS PLANAS COM TRIANGULAÇÃO EM LEQUE ---
    print("A criar tampas planas para a base e o topo...")
    
    # Tampa da Base
    bottom_layer_vertices = resampled_layers[0]
    bottom_center_point = np.mean(bottom_layer_vertices, axis=0)
    all_vertices = np.vstack([all_vertices, bottom_center_point])
    bottom_center_index = len(all_vertices) - 1
    
    for j in range(num_points_per_layer):
        p1 = j
        p2 = (j + 1) % num_points_per_layer
        all_triangles.append([bottom_center_index, p2, p1])

    # Tampa do Topo
    top_layer_vertices = resampled_layers[-1]
    top_center_point = np.mean(top_layer_vertices, axis=0)
    all_vertices = np.vstack([all_vertices, top_center_point])
    top_center_index = len(all_vertices) - 1
    
    top_layer_start_index = (len(resampled_layers) - 1) * num_points_per_layer
    for j in range(num_points_per_layer):
        p1 = top_layer_start_index + j
        p2 = top_layer_start_index + (j + 1) % num_points_per_layer
        all_triangles.append([top_center_index, p1, p2])

    # --- PASSO 6: JUNTAR TUDO E FINALIZAR ---
    print("A combinar e finalizar o modelo...")
    final_mesh = o3d.geometry.TriangleMesh(
        vertices=o3d.utility.Vector3dVector(all_vertices),
        triangles=o3d.utility.Vector3iVector(all_triangles)
    )
    
    final_mesh.merge_close_vertices(0.01)
    final_mesh.scale(0.001, center=(0,0,0))
    final_mesh.compute_vertex_normals()
    
    print(f"\nMalha final criada com {len(final_mesh.triangles)} triângulos.")
    
    # --- PASSO 7: GUARDAR E VISUALIZAR ---
    o3d.io.write_triangle_mesh(output_filepath, final_mesh)
    print(f"[SUCESSO] Malha 3D sólida exportada para '{output_filepath}'.")

    pcd_original = o3d.geometry.PointCloud()
    pcd_original.points = o3d.utility.Vector3dVector(points_mm / 1000.0)
    pcd_original.paint_uniform_color([0.8, 0.2, 0.2])
    
    o3d.visualization.draw_geometries(
        [pcd_original, final_mesh], 
        window_name="Resultado (Vermelho = Original, Cinza = Final)"
    )