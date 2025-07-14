import numpy as np
import pyvista as pv
from scipy.spatial import Delaunay

def generate_mesh(input_filepath="3dScanner_Data.txt", output_filepath="scanner_output.stl"):
    """
    Gera uma malha 3D usando Scipy e PyVista, com a correção final para a visualização.
    """
    print(f"\n A iniciar a geração da malha a partir de '{input_filepath}' (Usando PyVista/Scipy)")

    try:
        points = np.loadtxt(input_filepath, delimiter=",")
        if points.shape[0] < 20:
            print("[Erro] Ficheiro contém muito poucos pontos.")
            return
        print(f"Nuvem de pontos carregada com {points.shape[0]} pontos.")
    except Exception as e:
        print(f"[Erro] Falha ao carregar o ficheiro '{input_filepath}': {e}")
        return
        
    points = points / 1000.0

    print("A criar a nuvem de pontos no PyVista...")
    cloud = pv.PolyData(points)

    print("A gerar a malha volumétrica com Delaunay 3D do PyVista...")
    grid = cloud.delaunay_3d(alpha=0.04)

    print("A extrair a superfície externa da malha...")
    surface = grid.extract_surface()
    print(f"-> Superfície extraída com {surface.n_faces} faces.")
    
    print("A preencher buracos e a suavizar a malha...")
    filled_surface = surface.fill_holes(hole_size=1.0)
    smooth_surface = filled_surface.smooth(n_iter=50, relaxation_factor=0.1)
    
    print("-> Limpeza e suavização concluídas.")

    print(f"A exportar a malha final para '{output_filepath}'...")
    smooth_surface.save(output_filepath)
    print(f"\n[SUCESSO] Malha 3D exportada para '{output_filepath}'.")

    # 5. VISUALIZAÇÃO COM PYVISTA (CORRIGIDA)
    print("A abrir visualizador 3D...")
    
    plotter = pv.Plotter(window_size=[800, 600])
    plotter.add_mesh(smooth_surface, color='lightblue', style='surface',
                     specular=0.7, smooth_shading=True, show_edges=True, edge_color='gray')
    plotter.add_points(points, color='orange', point_size=5)
    plotter.show_axes()

    
    print("Feche a janela para terminar o script.")
    plotter.show()