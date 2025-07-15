import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import time
import os
import open3d as o3d

# --- CONFIGURAÇÕES ---
DATA_FILENAME = "3dScanner_Data.txt"
UPDATE_INTERVAL_SECONDS = 0.5 # Verifica por novos pontos a cada meio segundo

# --- CONFIGURAÇÕES DO FILTRO DE RUÍDO (RADIUS) ---
# nb_points: Um ponto só é mantido se tiver pelo menos este número de vizinhos.
FILTER_NB_POINTS = 15 
# radius: ...dentro deste raio (em metros). Um valor maior é menos agressivo.
FILTER_RADIUS = 0.01 # 1 cm de raio

def apply_denoise_filter(points_np):
    """Aplica o filtro Radius Outlier Removal a um lote de pontos."""
    # Retorna imediatamente se não houver pontos suficientes para formar um vizinhança
    if len(points_np) < FILTER_NB_POINTS:
        return points_np
        
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points_np)
    
    # Executa o filtro
    cl, ind = pcd.remove_radius_outlier(nb_points=FILTER_NB_POINTS,
                                        radius=FILTER_RADIUS)
    
    # Retorna apenas os pontos que passaram no filtro ("inliers")
    return np.asarray(pcd.select_by_index(ind).points)

def read_new_points(file_handle):
    """Lê todas as novas linhas disponíveis do ficheiro e retorna-as como um array numpy."""
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
                # Ignora linhas mal formatadas silenciosamente para não encher o terminal
                pass
    
    # Converte para um array numpy e para metros
    return np.array(new_points) / 1000.0 if new_points else None

def main():
    print("--- Visualizador com Matplotlib (Otimizado) ---")
    print(f"A observar o ficheiro: '{DATA_FILENAME}'...")

    # Inicializa o Matplotlib no modo interativo
    plt.ion()
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')
    
    # Cria um único objeto 'scatter' que será atualizado, em vez de recriado.
    # Isto é muito mais eficiente.
    scatter_plot = ax.scatter([], [], [], s=5, c='blue', alpha=0.7)
    
    plt.show()

    # Array que vai conter todos os pontos filtrados que estão a ser mostrados
    all_filtered_points = np.empty((0, 3))

    try:
        with open(DATA_FILENAME, 'r') as file_handle:
            
            # ---------------------------------------------------
            # ETAPA 1: CARREGAMENTO E FILTRO INICIAL (PONTOS JÁ EXISTENTES)
            # ---------------------------------------------------
            print("A carregar e filtrar pontos existentes...")
            
            # A primeira chamada a read_new_points lê o ficheiro inteiro
            initial_points_raw = read_new_points(file_handle) 
            
            if initial_points_raw is not None:
                # Aplica o filtro aos pontos iniciais
                all_filtered_points = apply_denoise_filter(initial_points_raw)
                
                # Atualiza os dados do scatter plot com os pontos iniciais e filtrados
                scatter_plot._offsets3d = (all_filtered_points[:, 0], all_filtered_points[:, 1], all_filtered_points[:, 2])
                
                ax.set_title(f"Nuvem de Pontos ({len(all_filtered_points)} pontos)")
                ax.autoscale_view(True, True, True) # Ajusta o zoom automaticamente
                fig.canvas.draw_idle()
                plt.pause(0.1) # Pausa para garantir que o gráfico é desenhado
                
                print(f"Carregados e mostrados {len(all_filtered_points)} pontos filtrados.")

            # ---------------------------------------------------
            # ETAPA 2: LOOP DE ATUALIZAÇÃO INCREMENTAL (NOVOS PONTOS)
            # ---------------------------------------------------
            print("\nA aguardar novos pontos...")
            while plt.fignum_exists(fig.number):
                # As chamadas seguintes a read_new_points só lêem o que foi adicionado
                new_points_raw = read_new_points(file_handle)
                
                if new_points_raw is not None:
                    # Filtra APENAS o novo lote de pontos
                    new_filtered_points = apply_denoise_filter(new_points_raw)
                    
                    if len(new_filtered_points) > 0:
                        # Adiciona os novos pontos filtrados ao conjunto total
                        all_filtered_points = np.vstack((all_filtered_points, new_filtered_points))
                        
                        # Atualiza o scatter plot com o novo conjunto completo
                        scatter_plot._offsets3d = (all_filtered_points[:, 0], all_filtered_points[:, 1], all_filtered_points[:, 2])

                        ax.set_title(f"Nuvem de Pontos ({len(all_filtered_points)} pontos)")
                        ax.autoscale_view(True, True, True)
                        
                        fig.canvas.draw_idle()

                # Pausa controlada para a UI e para não sobrecarregar o CPU
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