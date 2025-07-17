# --- START OF FILE scanner_receiver.py ---

import socket
import numpy as np
import os
import sys

# Tenta importar a nossa função de geração de malha
try:
    from generate_stl import generate_mesh
    GENERATE_STL_AVAILABLE = True
except ImportError:
    print("[Aviso] Ficheiro 'generate_stl.py' não encontrado. A geração de STL será ignorada no final.")
    GENERATE_STL_AVAILABLE = False


HOST = '0.0.0.0'
PORT = 5000
DATA_FILENAME = "3dScanner_Data.txt"
# O nome do ficheiro de saída será definido dinamicamente mais tarde

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1)); IP = s.getsockname()[0]
    except Exception: IP = '127.0.0.1'
    finally: s.close()
    return IP

def process_data(data_line: str):
    try:
        parts = data_line.strip().split(',');
        distance = int(parts[0].split(':')[1]); theta_deg = float(parts[1].split(':')[1]); height = float(parts[2].split(':')[1])
        return distance, theta_deg, height
    except (ValueError, IndexError) as e:
        print(f"\n[Erro] Dados recebidos em formato inválido: '{data_line}'. Erro: {e}"); return None

# --- NOVA FUNÇÃO PARA OBTER A ESCOLHA DO UTILIZADOR ---
def get_user_choice_for_mesh_generation():
    """
    Mostra as opções de processamento ao utilizador e retorna o método escolhido.
    """
    print("\n" + "="*50)
    print("--- Escolha o Método de Geração da Malha 3D ---")
    print("\n1. BPA (Ball Pivoting)")
    print("   -> Para objetos com formas complexas, orgânicas ou curvas (ex: uma chávena, uma estátua).")
    print("\n2. RANSAC Faces")
    print("   -> Para analisar objetos com faces planas e ver como foram detectadas (uso para diagnóstico).")
    print("\n3. Idealize Box")
    print("   -> Para forçar o resultado a ser um paralelepípedo perfeito (use apenas se o objeto for uma caixa).")
    
    while True:
        try:
            choice = int(input("\nDigite o número da sua escolha (1, 2, ou 3): "))
            if choice == 1:
                return 'bpa'
            elif choice == 2:
                return 'ransac_faces'
            elif choice == 3:
                return 'idealize_box'
            else:
                print("Escolha inválida. Por favor, digite 1, 2, ou 3.")
        except ValueError:
            print("Entrada inválida. Por favor, digite um número.")
        except KeyboardInterrupt:
            print("\nOperação cancelada pelo utilizador.")
            return None

def main():
    if os.path.exists(DATA_FILENAME):
        print(f"A limpar o ficheiro de dados anterior: {DATA_FILENAME}")
        os.remove(DATA_FILENAME)

    local_ip = get_local_ip()
    should_exit = False

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print("\n--- Servidor de Scanner 3D Iniciado ---")
        print(f"-> Verifique se este IP está no código Arduino: {local_ip}")
        print(f"-> A aguardar conexão do scanner na porta {PORT}...")

        conn, addr = s.accept()
        with conn, open(DATA_FILENAME, "a") as f_points:
            print(f"\n[+] Scanner conectado de {addr}")
            print("A receber dados... (Pressione Ctrl+C para parar manualmente)")
            
            point_count = 0
            buffer = ""
            while not should_exit:
                try:
                    data_bytes = conn.recv(1024)
                    if not data_bytes: print("\n[!] Conexão fechada pelo scanner."); break
                    buffer += data_bytes.decode('utf-8')
                    
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        if not line: continue
                        
                        if line.upper() == "END":
                            print("\n[+] Sinal de 'END' recebido."); should_exit = True; break

                        result = process_data(line)
                        if result:
                            distance, theta_deg, height = result
                            theta_rad = np.deg2rad(theta_deg)
                            x = distance * np.cos(theta_rad); y = distance * np.sin(theta_rad); z = height
                            f_points.write(f"{x:.6f},{y:.6f},{z:.6f}\n")
                            f_points.flush()
                            point_count += 1
                            print(f"\rPontos recebidos: {point_count}", end="")

                except (ConnectionResetError, BrokenPipeError): print("\n[!] A conexão com o scanner foi perdida."); break
                except KeyboardInterrupt: print("\n[!] Interrupção manual."); break

    print(f"\n\nRecolha de dados concluída. {point_count} pontos guardados em '{DATA_FILENAME}'.")

    # --- LÓGICA DE GERAÇÃO DE MALHA MODIFICADA ---
    if GENERATE_STL_AVAILABLE and point_count > 20:
        # Pergunta ao utilizador qual método usar
        chosen_method = get_user_choice_for_mesh_generation()

        if chosen_method:
            # Define o nome do ficheiro de saída com base na escolha
            output_stl_filename = f"output_{chosen_method}.stl"
            
            print(f"\nA iniciar a geração do ficheiro STL: '{output_stl_filename}'...")
            try:
                # Chama a função de geração de malha com o método escolhido
                generate_mesh(
                    input_filepath=DATA_FILENAME, 
                    output_filepath=output_stl_filename,
                    method=chosen_method
                )
            except Exception as e:
                print(f"[Erro] Ocorreu um erro durante a geração do STL: {e}")
                import traceback
                traceback.print_exc()

    print("\n--- Processo do Scanner Concluído ---")


if __name__ == "__main__":
    main()