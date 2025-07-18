# --- START OF FILE scanner_receiver.py ---

import socket
import numpy as np
import os
import sys

try:
    from generate_stl import build_universal_solid 
    GENERATE_STL_AVAILABLE = True
except ImportError:
    print("[Aviso] Ficheiro 'generate_stl.py' não encontrado.")
    GENERATE_STL_AVAILABLE = False

HOST = '0.0.0.0'
PORT = 5000
DATA_FILENAME = "3dScanner_Data.txt"
OUTPUT_STL_FILENAME = "output_universal_solid.stl"

# =======================================================================
# VERIFIQUE ESTE VALOR!
# Meça com uma régua a distância EXATA da lente do seu sensor até ao CENTRO
# do prato rotativo. Coloque esse valor exato aqui em milímetros.
SENSOR_OFFSET_MM = 175.0 # <--- MUDE ESTE VALOR PARA A SUA MEDIÇÃO REAL!
# =======================================================================

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: s.connect(('10.255.255.255', 1)); IP = s.getsockname()[0]
    except Exception: IP = '127.0.0.1'
    finally: s.close()
    return IP

def process_data(data_line: str):
    try:
        parts = data_line.strip().split(',')
        # Formato esperado: "Dist:123,Theta:45,Z:10.00"
        distance = int(parts[0].split(':')[1])
        theta_deg = int(parts[1].split(':')[1])
        height = float(parts[2].split(':')[1])
        return distance, theta_deg, height
    except (ValueError, IndexError, TypeError) as e:
        print(f"\n[Erro] Formato de dados inválido: '{data_line}'. Erro: {e}"); return None

def main():
    if os.path.exists(DATA_FILENAME):
        print(f"A limpar ficheiro de dados anterior: {DATA_FILENAME}")
        os.remove(DATA_FILENAME)

    local_ip = get_local_ip()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print("\n--- Servidor de Scanner 3D Iniciado ---")
        print(f"-> IP do servidor: {local_ip}")
        print(f"-> A aguardar conexão do scanner na porta {PORT}...")
        conn, addr = s.accept()
        with conn, open(DATA_FILENAME, "a") as f_points:
            print(f"\n[+] Scanner conectado de {addr}")
            point_count = 0
            buffer = ""
            while True:
                try:
                    data_bytes = conn.recv(1024)
                    if not data_bytes: print("\n[!] Conexão fechada pelo scanner."); break
                    buffer += data_bytes.decode('utf-8')
                    
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        if not line: continue
                        
                        if line.upper() == "END":
                            print("\n[+] Sinal de 'END' recebido."); return # Sai da função main

                        result = process_data(line)
                        if result:
                            distance, theta_deg, height = result
                            if distance < SENSOR_OFFSET_MM and distance > 0:
                                theta_rad = np.deg2rad(theta_deg)
                                radius = SENSOR_OFFSET_MM - distance
                                x = radius * np.cos(theta_rad)
                                y = radius * np.sin(theta_rad)
                                z = height
                                
                                f_points.write(f"{x:.6f},{y:.6f},{z:.6f}\n")
                                f_points.flush()
                                point_count += 1
                                print(f"\rPontos Aceites: {point_count}", end="")
                except (ConnectionResetError, BrokenPipeError): print("\n[!] A conexão foi perdida."); break
                except KeyboardInterrupt: print("\n[!] Interrupção manual."); break

    print(f"\n\nRecolha de dados concluída. {point_count} pontos guardados.")
    if GENERATE_STL_AVAILABLE and point_count > 50:
        print(f"\nA iniciar a geração do STL...")
        try:
            build_universal_solid(DATA_FILENAME, OUTPUT_STL_FILENAME)
        except Exception as e:
            print(f"[Erro] Falha na geração do STL: {e}")

if __name__ == "__main__":
    main()
    print("\n--- Processo do Scanner Concluído ---")