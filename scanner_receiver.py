# --- START OF FILE scanner_receiver.py ---
import socket
import numpy as np
import os

# Tenta importar a função de geração de STL. Se não existir, avisa.
try:
    from generate_stl import generate_mesh
    GENERATE_STL_AVAILABLE = True
except ImportError:
    print("[Aviso] Ficheiro 'generate_stl.py' não encontrado. A geração de STL será ignorada no final.")
    GENERATE_STL_AVAILABLE = False


HOST = '0.0.0.0'    # Escuta todas as interfaces de rede disponíveis
PORT = 5000
DATA_FILENAME = "3dScanner_Data.txt"
OUTPUT_STL_FILENAME = "scanner_output.stl"

def get_local_ip():
    """Tenta encontrar o endereço IP local da máquina para facilitar a configuração."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def process_data(data_line: str):
    """
    Analisa uma string de dados do Arduino, converte e retorna os valores.
    Formato esperado: "Dist:123,Theta:90,Z:10.00"
    """
    try:
        parts = data_line.strip().split(',')
        distance = int(parts[0].split(':')[1])
        theta_deg = float(parts[1].split(':')[1])
        height = float(parts[2].split(':')[1])
        return distance, theta_deg, height
    except (ValueError, IndexError) as e:
        print(f"[Erro] Dados recebidos em formato inválido: '{data_line}'. Erro: {e}")
        return None

def main():
    """
    Função principal que orquestra a receção de dados e a geração da malha.
    """
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
                    if not data_bytes:
                        print("\n[!] Conexão fechada pelo scanner.")
                        break
                    
                    buffer += data_bytes.decode('utf-8')
                    
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        if not line:
                            continue
                        
                        if line.upper() == "END":
                            print("\n[+] Sinal de 'END' recebido. A terminar a receção de dados.")
                            should_exit = True
                            break

                        result = process_data(line)
                        if result:
                            distance, theta_deg, height = result
                            theta_rad = np.deg2rad(theta_deg)
                            x = distance * np.cos(theta_rad)
                            y = distance * np.sin(theta_rad)
                            z = height

                            f_points.write(f"{x:.6f},{y:.6f},{z:.6f}\n")
                            point_count += 1
                            print(f"\rPontos recebidos: {point_count}", end="")

                except (ConnectionResetError, BrokenPipeError):
                    print("\n[!] A conexão com o scanner foi perdida.")
                    break
                except KeyboardInterrupt:
                    print("\n[!] Interrupção manual. A parar o servidor.")
                    break

    print(f"\n\nRecolha de dados concluída. {point_count} pontos guardados em '{DATA_FILENAME}'.")

    if GENERATE_STL_AVAILABLE and point_count > 0:
        print(f"A iniciar a geração do ficheiro STL: '{OUTPUT_STL_FILENAME}'...")
        try:
            generate_mesh(input_filepath=DATA_FILENAME, output_filepath=OUTPUT_STL_FILENAME)
            print("[Sucesso] Ficheiro STL gerado com sucesso!")
        except Exception as e:
            print(f"[Erro] Ocorreu um erro durante a geração do STL: {e}")

if __name__ == "__main__":
    main()