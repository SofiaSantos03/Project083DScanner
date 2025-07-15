import socket
import numpy as np
from scipy.optimize import least_squares
import matplotlib.pyplot as plt

HOST = '0.0.0.0'
PORT = 5000

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: s.connect(('10.255.255.255', 1)); IP = s.getsockname()[0]
    except Exception: IP = '127.0.0.1'
    finally: s.close()
    return IP

def receive_data():
    local_ip = get_local_ip()
    points = []
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print("\n--- Verificador de Alinhamento do Sensor ---")
        print(f"1. Faça upload do sketch 'sensor_alignment.ino'.")
        print(f"2. IP do PC: {local_ip}")
        print(f"3. Coloque um objeto CILÍNDRICO no centro do prato.")
        print(f"\nA aguardar conexão...")

        conn, addr = s.accept()
        with conn:
            print(f"\n[+] Conectado! A receber dados...")
            buffer = ""
            while True:
                data = conn.recv(1024)
                if not data: break
                buffer += data.decode('utf-8', errors='ignore')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if "END" in line.upper():
                        print("[+] Scan concluído.")
                        return np.array(points)
                    try:
                        parts = line.strip().split(',')
                        dist = int(parts[0].split(':')[1])
                        theta = int(parts[1].split(':')[1])
                        
                        theta_rad = np.deg2rad(theta)
                        x = dist * np.cos(theta_rad)
                        y = dist * np.sin(theta_rad)
                        points.append([x, y])
                    except (ValueError, IndexError): pass
    return np.array(points)

def circle_residuals(params, data):
    xc, yc, r = params
    x, y = data.T
    return (x - xc)**2 + (y - yc)**2 - r**2

def filter_outliers(points_2d):
    """Remove pontos que estão muito longe do centro de massa."""
    if len(points_2d) < 10:
        return points_2d
        
    # Calcula o centro de massa e as distâncias de cada ponto a ele
    center = np.mean(points_2d, axis=0)
    distances = np.linalg.norm(points_2d - center, axis=1)
    
    # Usa a Distância Interquartil (IQR) para definir os limites (robusto a outliers)
    q1, q3 = np.percentile(distances, [25, 75])
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    # Mantém apenas os pontos dentro dos limites
    inliers = points_2d[(distances >= lower_bound) & (distances <= upper_bound)]
    print(f"Filtragem: Removidos {len(points_2d) - len(inliers)} pontos de ruído.")
    return inliers

def analyze_and_visualize(points_2d):
    if len(points_2d) < 10:
        print("\n[ERRO] Pontos insuficientes.")
        return
        
    # [NOVO] Aplica o filtro antes da análise
    filtered_points = filter_outliers(points_2d)
    
    if len(filtered_points) < 10:
        print("\n[ERRO] Não restaram pontos suficientes após a filtragem.")
        return

    # A análise agora é feita nos pontos filtrados
    x_m, y_m = np.mean(filtered_points, axis=0)
    r_m = np.mean(np.sqrt((filtered_points[:, 0] - x_m)**2 + (filtered_points[:, 1] - y_m)**2))
    
    result = least_squares(circle_residuals, [x_m, y_m, r_m], args=(filtered_points,))
    xc, yc, r = result.x
    
    print("\n--- Análise de Alinhamento ---")
    print(f"Raio do objeto: {r:.2f} mm")
    print(f"Centro do círculo: (x={xc:.2f}, y={yc:.2f}) mm")
    
    offset_distance = np.sqrt(xc**2 + yc**2)
    
    if offset_distance < 1.0:
        print("\n[RESULTADO] Sensor excelentemente alinhado!")
    else:
        print(f"\n[RESULTADO] Sensor desalinhado por {offset_distance:.2f} mm.")
        if abs(xc) > abs(yc):
            if xc > 0: print("  - Mova o sensor para a DIREITA.")
            else: print("  - Mova o sensor para a ESQUERDA.")
        else:
            if yc > 0: print("  - Mova o sensor para a FRENTE.")
            else: print("  - Mova o sensor para TRÁS.")
            
    plt.figure(figsize=(8, 8))
    # Mostra os pontos filtrados
    plt.plot(filtered_points[:, 0], filtered_points[:, 1], 'b.', label='Pontos (Filtrados)')
    
    circle_plot = plt.Circle((xc, yc), r, color='r', fill=False, label='Círculo Ajustado')
    plt.gca().add_artist(circle_plot)
    
    plt.plot(0, 0, 'g+', markersize=15, label='Centro Ideal (0,0)')
    plt.plot(xc, yc, 'r+', markersize=15, label=f'Centro Medido ({xc:.1f}, {yc:.1f})')
    
    plt.title("Análise de Alinhamento do Sensor")
    plt.xlabel("Eixo X (mm)"); plt.ylabel("Eixo Y (mm)")
    plt.gca().set_aspect('equal', adjustable='box')
    plt.grid(True); plt.legend(); plt.show()

if __name__ == "__main__":
    p = receive_data()
    if len(p) > 0:
        analyze_and_visualize(p)