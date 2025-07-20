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
# ALTERAÇÃO: O raio agora está em mm. 10mm = 1cm.
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

def update_axis_limits(ax, new_points):
    """Expande os limites dos eixos apenas se os novos pontos estiverem fora dos limites atuais."""
    if len(new_points) == 0:
        return
    xlim, ylim, zlim = ax.get_xlim(), ax.get_ylim(), ax.get_zlim()
    min_x, max_x = np.min(new_points[:, 0]), np.max(new_points[:, 0])
    min_y, max_y = np.min(new_points[:, 1]), np.max(new_points[:, 1])
    min_z, max_z = np.min(new_points[:, 2]), np.max(new_points[:, 2])
    new_xlim = (min(xlim[0], min_x), max(xlim[1], max_x))
    new_ylim = (min(ylim[0], min_y), max(ylim[1], max_y))
    new_zlim = (min(zlim[0], min_z), max(zlim[1], max_z))
    ax.set_xlim(new_xlim)
    ax.set_ylim(new_ylim)
    ax.set_zlim(new_zlim)

def main():
    print("--- Visualizador com Matplotlib (em Milímetros) ---")
    print(f"A observar o ficheiro: '{DATA_FILENAME}'...")

    plt.ion()
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_zlabel('Z (mm)')
    
    scatter_plot = ax.scatter([], [], [], s=5, c='blue', alpha=0.7)
    plt.show()

    all_filtered_points = np.empty((0, 3))

    try:
        with open(DATA_FILENAME, 'r') as file_handle:
            print("A carregar e filtrar pontos existentes...")
            initial_points_raw = read_new_points(file_handle) 
            
            if initial_points_raw is not None:
                all_filtered_points = apply_denoise_filter(initial_points_raw)
                scatter_plot._offsets3d = (all_filtered_points[:, 0], all_filtered_points[:, 1], all_filtered_points[:, 2])
                ax.set_title(f"Nuvem de Pontos ({len(all_filtered_points)} pontos)")
                ax.autoscale_view(True, True, True)
                fig.canvas.draw_idle()
                plt.pause(0.1)
                print(f"Carregados e mostrados {len(all_filtered_points)} pontos filtrados.")

            print("\nA aguardar novos pontos...")
            while plt.fignum_exists(fig.number):
                new_points_raw = read_new_points(file_handle)
                
                if new_points_raw is not None:
                    new_filtered_points = apply_denoise_filter(new_points_raw)
                    
                    if len(new_filtered_points) > 0:
                        all_filtered_points = np.vstack((all_filtered_points, new_filtered_points))
                        scatter_plot._offsets3d = (all_filtered_points[:, 0], all_filtered_points[:, 1], all_filtered_points[:, 2])
                        ax.set_title(f"Nuvem de Pontos ({len(all_filtered_points)} pontos)")
                        update_axis_limits(ax, new_filtered_points)
                        fig.canvas.draw_idle()

                plt.pause(UPDATE_INTERVAL_SECONDS)

    except FileNotFoundError:
        print(f"Erro: O ficheiro '{DATA_FILENAME}' não foi encontrado.")
    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")
    finally:
        plt.ioff()
        print("\nVisualização terminada.")

if __name__ == "__main__":
    main()