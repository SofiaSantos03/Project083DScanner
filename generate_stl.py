# --- START OF FILE generate_stl.py ---

import numpy as np
import open3d as o3d
from scipy.interpolate import splprep, splev

def fit_ellipse(points):
    """ Encontra a melhor elipse que se ajusta a um conjunto de pontos 2D. """

    center = np.mean(points, axis=0)
    radii = np.mean(np.sqrt(np.sum((points - center)**2, axis=1)))
    return center, radii

def build_universal_solid(input_filepath, output_filepath):
    """
    Constrói uma malha 3D sólida e fechada a partir de uma nuvem de pontos 
    estruturada, idealizando cada camada.
    """
    print(f"\n A iniciar a construção da malha a partir de '{input_filepath}'")
    
    # --- PASSO 1: Carregar os Dados ---
    try:
        points_mm = np.loadtxt(input_filepath, delimiter=",")
        print(f"Nuvem de pontos carregada com {points_mm.shape[0]} pontos.")
    except Exception as e:
        print(f"[Erro] Falha ao carregar o ficheiro '{input_filepath}': {e}")
        return

    # --- PASSO 2: Separar Pontos em Camadas (Ordem Cronológica) ---
    print("A separar os pontos em camadas...")
    layers = []
    if len(points_mm) > 0:
        current_layer = [points_mm[0]]
        for i in range(1, len(points_mm)):
            if abs(points_mm[i, 2] - current_layer[0][2]) > 0.1:
                if len(current_layer) > 10: # Ignora camadas com muito poucos pontos
                    layers.append(np.array(current_layer))
                current_layer = []
            current_layer.append(points_mm[i])
        if len(current_layer) > 10:
            layers.append(np.array(current_layer))
    print(f"Detectadas {len(layers)} camadas válidas.")

    if len(layers) < 2:
        print("[ERRO] Não foram detectadas camadas suficientes.")
        return

    # --- PASSO 3: Idealizar Cada Camada (O Passo de "Preenchimento") ---
    print("A idealizar e a interpolar cada camada para uma forma perfeita...")
    ideal_layers = []
    num_points_per_layer = 180 # Alta resolução para um círculo suave

    for layer in layers:
        # Foca-se apenas nas coordenadas X, Y para encontrar a forma 2D
        points_2d = layer[:, :2]
        
        # Encontra o centro e o raio médio da camada
        center_2d, radius = fit_ellipse(points_2d)
        
        # Cria novos pontos num círculo perfeito
        angles = np.linspace(0, 2 * np.pi, num_points_per_layer, endpoint=False)
        x_new = center_2d[0] + radius * np.cos(angles)
        y_new = center_2d[1] + radius * np.sin(angles)
        
        # Obtém a altura Z média da camada original
        z_mean = np.mean(layer[:, 2])
        
        # Cria a camada idealizada com os novos pontos X, Y e a altura Z original
        ideal_layer = np.vstack((x_new, y_new, np.full(num_points_per_layer, z_mean))).T
        ideal_layers.append(ideal_layer)

    # --- PASSO 4: Construir a Malha a Partir das Camadas Idealizadas ---
    print("A construir as paredes a partir das camadas idealizadas...")
    all_vertices = []
    all_triangles = []
    vertex_offset = 0

    for i in range(len(ideal_layers) - 1):
        lower_layer = ideal_layers[i]
        upper_layer = ideal_layers[i+1]
        
        current_vertices = np.vstack((lower_layer, upper_layer))
        all_vertices.append(current_vertices)
        
        for j in range(num_points_per_layer):
            p1 = j
            p2 = (j + 1) % num_points_per_layer
            p3 = j + num_points_per_layer
            p4 = (j + 1) % num_points_per_layer + num_points_per_layer
            
            all_triangles.append([p1 + vertex_offset, p2 + vertex_offset, p3 + vertex_offset])
            all_triangles.append([p2 + vertex_offset, p4 + vertex_offset, p3 + vertex_offset])

        vertex_offset += len(current_vertices)
    
    final_wall_vertices = np.vstack(all_vertices)
    wall_mesh = o3d.geometry.TriangleMesh(
        vertices=o3d.utility.Vector3dVector(final_wall_vertices),
        triangles=o3d.utility.Vector3iVector(all_triangles)
    )

    # --- PASSO 5: Tapar os Buracos ---
    print("A tapar o topo e a base...")
    
    def create_cap(points):
        # Para criar a tampa, basta triangular os pontos do anel idealizado
        pcd = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points))
        # Para um polígono simples, o Ball-Pivoting é eficaz
        pcd.normals = o3d.utility.Vector3dVector(np.tile([0, 0, 1], (len(points), 1)))
        radii = [np.max(np.abs(points)) * 2] # Um raio grande o suficiente para cobrir tudo
        cap = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(pcd, o3d.utility.DoubleVector(radii))
        return cap

    bottom_cap = create_cap(ideal_layers[0])
    # Inverte os triângulos da tampa de baixo para que a normal aponte para fora
    bottom_cap.triangles = o3d.utility.Vector3iVector(np.asarray(bottom_cap.triangles)[:, ::-1])
    top_cap = create_cap(ideal_layers[-1])

    # --- PASSO 6: Juntar e Finalizar ---
    print("A combinar e finalizar o modelo...")
    final_mesh = wall_mesh + bottom_cap + top_cap
    final_mesh.merge_close_vertices(0.01) # Tolerância em mm
    
    # Converte para metros para o ficheiro STL e visualização
    final_mesh.scale(0.001, center=(0,0,0))
    final_mesh.compute_vertex_normals()

    print(f"\nMalha final criada com {len(final_mesh.triangles)} triângulos.")
    
    # --- PASSO 7: Guardar e Visualizar ---
    o3d.io.write_triangle_mesh(output_filepath, final_mesh)
    print(f"[SUCESSO] Malha 3D sólida exportada para '{output_filepath}'.")

    pcd_original = o3d.geometry.PointCloud()
    pcd_original.points = o3d.utility.Vector3dVector(points_mm / 1000.0)
    pcd_original.paint_uniform_color([0.8, 0.8, 0.8])
    o3d.visualization.draw_geometries([pcd_original, final_mesh], window_name="Resultado Idealizado (Construtor Universal)")