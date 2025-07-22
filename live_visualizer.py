# --- START OF FILE live_visualizer.py (Corrigido para Tempo Real) ---

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import time
import os

# --- CONFIGURAÇÕES ---
DATA_FILENAME = "3dScanner_Data.txt"
UPDATE_INTERVAL_SECONDS = 0.5 # Com que frequência o script verifica o ficheiro

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
                # Assume que os dados estão separados por vírgulas
                coords = [float(val) for val in line.split(',')]
                new_points.append(coords)
            except (ValueError, IndexError):
                # Ignora linhas mal formatadas
                pass
    
    return np.array(new_points) if new_points else None

def set_equal_aspect_3d(ax, all_points):
    """
    Ajusta os limites dos eixos para que a escala seja 1:1:1,
    dando uma representação visual correta das proporções do objeto.
    """
    if len(all_points) == 0:
        return

    x_vals, y_vals, z_vals = all_points[:, 0], all_points[:, 1], all_points[:, 2]
    max_range = np.array([
        x_vals.max() - x_vals.min(), 
        y_vals.max() - y_vals.min(), 
        z_vals.max() - z_vals.min()
    ]).max()
    
    # Adiciona uma margem de 10%
    max_range *= 1.1 

    mid_x = (x_vals.max() + x_vals.min()) * 0.5
    mid_y = (y_vals.max() + y_vals.min()) * 0.5
    mid_z = (z_vals.max() + z_vals.min()) * 0.5
    
    ax.set_xlim(mid_x - max_range / 2, mid_x + max_range / 2)
    ax.set_ylim(mid_y - max_range / 2, mid_y + max_range / 2)
    ax.set_zlim(mid_z - max_range / 2, mid_z + max_range / 2)

def main():
    print("--- Visualizador em Tempo Real com Matplotlib ---")
    print(f"A observar o ficheiro: '{DATA_FILENAME}'...")

    plt.ion() # Ativa o modo interativo do Matplotlib
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_zlabel('Z (mm)')
    
    # O 'scatter_plot' é o objeto que vamos atualizar com os novos pontos
    scatter_plot = ax.scatter([], [], [], s=5, c='blue', alpha=0.7)
    plt.show()

    all_points = np.empty((0, 3))

    # Verifica se o ficheiro existe antes de tentar abrir
    if not os.path.exists(DATA_FILENAME):
        print(f"Aviso: Ficheiro '{DATA_FILENAME}' não encontrado. A aguardar que seja criado...")
        # Cria um ficheiro vazio para evitar erros
        open(DATA_FILENAME, 'a').close()

    try:
        with open(DATA_FILENAME, 'r') as file_handle:
            print("A aguardar novos pontos... (Pressione Ctrl+C na consola ou feche a janela para parar)")
            
            # --- LÓGICA PRINCIPAL ---
            while plt.fignum_exists(fig.number):
                # Tenta ler novas linhas a partir da posição atual do ficheiro
                new_points_batch = read_new_points(file_handle)
                
                if new_points_batch is not None and len(new_points_batch) > 0:
                    # Adiciona os novos pontos à lista de todos os pontos
                    all_points = np.vstack((all_points, new_points_batch))
                    
                    # Atualiza os dados do gráfico
                    scatter_plot._offsets3d = (all_points[:, 0], all_points[:, 1], all_points[:, 2])
                    ax.set_title(f"Nuvem de Pontos ({len(all_points)} pontos)")
                    
                    # Reajusta os eixos para manter a escala correta
                    set_equal_aspect_3d(ax, all_points)
                    
                    # Redesenha o gráfico
                    fig.canvas.draw_idle()

                # Espera um pouco antes de verificar o ficheiro novamente
                plt.pause(UPDATE_INTERVAL_SECONDS)

    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")
    finally:
        plt.ioff()
        print("\nVisualização terminada.")

if __name__ == "__main__":
    main()