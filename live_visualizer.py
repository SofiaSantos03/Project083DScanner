import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import time
import os
import open3d as o3d

# --- CONFIGURAÇÕES ---
DATA_FILENAME = "3dScanner_Data.txt"
UPDATE_INTERVAL_SECONDS = 0.5

# --- CONFIGURAÇÕES DO FILTRO DE RUÍDO (RADIUS) EM MILÍMETROS ---
FILTER_NB_POINTS = 15
FILTER_RADIUS = 10.0 # Raio de 10mm

def apply_denoise_filter(points_np):
    if len(points_np) < FILTER_NB_POINTS:
        return points_np
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points_np)
    cl, ind = pcd.remove_radius_outlier(nb_points=FILTER_NB_POINTS, radius=FILTER_RADIUS)
    return np.asarray(pcd.select_by_index(ind).points)

def read_new_points(file_handle):
    """Lê todas as novas linhas disponíveis e retorna-as como um array numpy em mm."""
    new_lines = file_handle.readlines()
    if not new_lines:
        return None
    new_points = []
    for line in new_lines:
        line = line.strip()
        if line:
            try:
                coords = [float(val) for val in line.strip().split(',')]
                new_points.append(coords)
            except (ValueError, IndexError):
                pass
    
    return np.array(new_points) if new_points else None

# --- INÍCIO DA ALTERAÇÃO ---
def set_equal_aspect_3d(ax, points):
    """
    Define os limites dos eixos para que a escala seja igual em X, Y e Z,
    mantendo o objeto centrado.
    """
    if len(points) == 0:
        return

    # Encontra os limites de todos os pontos
    x_vals = points[:, 0]
    y_vals = points[:, 1]
    z_vals = points[:, 2]

    max_range = np.array([x_vals.max()-x_vals.min(), y_vals.max()-y_vals.min(), z_vals.max()-z_vals.min()]).max()
    
    # Adiciona uma pequena margem para que os pontos não fiquem colados às bordas
    max_range *= 1.1 

    mid_x = (x_vals.max()+x_vals.min()) * 0.5
    mid_y = (y_vals.max()+y_vals.min()) * 0.5
    mid_z = (z_vals.max()+z_vals.min()) * 0.5
    
    ax.set_xlim(mid_x - max_range/2, mid_x + max_range/2)
    ax.set_ylim(mid_y - max_range/2, mid_y + max_range/2)
    ax.set_zlim(mid_z - max_range/2, mid_z + max_range/2)
# --- FIM DA ALTERAÇÃO ---

def main():
    print("--- Visualizador com Matplotlib (em Milímetros) ---")
    print(f"A observar o ficheiro: '{DATA_FILENAME}'...")

    plt.ion()
    # Aumentar um pouco o tamanho da figura pode ajudar
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_zlabel('Z (mm)')
    
    scatter_plot = ax.scatter([], [], [], s=5, c='blue', alpha=0.7)
    
    # Definir limites iniciais para evitar um gráfico vazio
    ax.set_xlim(-50, 50)
    ax.set_ylim(-50, 50)
    ax.set_zlim(0, 100)
    set_equal_aspect_3d(ax, np.array([[-50,-50,0],[50,50,100]])) # Força o aspeto inicial
    
    plt.show()

    all_filtered_points = np.empty((0, 3))

    try:
        # Apaga o ficheiro no início para garantir que começamos do zero (opcional)
        # if os.path.exists(DATA_FILENAME):
        #     os.remove(DATA_FILENAME)
        # open(DATA_FILENAME, 'a').close() # Cria o ficheiro se não existir
            
        with open(DATA_FILENAME, 'r') as file_handle:
            # Move o ponteiro para o final do ficheiro para ler apenas os novos dados
            file_handle.seek(0, os.SEEK_END) 

            print("\nA aguardar novos pontos...")
            while plt.fignum_exists(fig.number):
                new_points_raw = read_new_points(file_handle)
                
                if new_points_raw is not None:
                    # Filtramos apenas os novos pontos para ser mais eficiente
                    # Adicionamos os pontos brutos primeiro e depois filtramos tudo
                    all_filtered_points = np.vstack((all_filtered_points, new_points_raw))
                    
                    # Filtramos todos os pontos para ter uma visão mais limpa
                    # Pode ser pesado se a nuvem de pontos for muito grande
                    points_to_display = apply_denoise_filter(all_filtered_points)

                    if len(points_to_display) > 0:
                        scatter_plot._offsets3d = (points_to_display[:, 0], points_to_display[:, 1], points_to_display[:, 2])
                        ax.set_title(f"Nuvem de Pontos ({len(points_to_display)} pontos)")
                        
                        # --- INÍCIO DA ALTERAÇÃO ---
                        # Usar a nova função para definir os limites
                        set_equal_aspect_3d(ax, points_to_display)
                        # --- FIM DA ALTERAÇÃO ---

                        fig.canvas.draw_idle()

                plt.pause(UPDATE_INTERVAL_SECONDS)

    except FileNotFoundError:
        print(f"Erro: O ficheiro '{DATA_FILENAME}' não foi encontrado.")
        print("A criar o ficheiro e a tentar novamente...")
        open(DATA_FILENAME, 'a').close()
        # Chama a função main() novamente após criar o ficheiro
        main()
    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")
    finally:
        plt.ioff()
        print("\nVisualização terminada.")

if __name__ == "__main__":
    main()