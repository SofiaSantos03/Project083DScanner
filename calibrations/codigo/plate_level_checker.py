import socket
import numpy as np
import open3d as o3d
import os
import math

HOST = '0.0.0.0'
PORT = 5000
DISTANCE_TOLERANCE_MM = 15.0 

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: s.connect(('10.255.255.255', 1)); IP = s.getsockname()[0]
    except Exception: IP = '127.0.0.1'
    finally: s.close()
    return IP

def receive_data():
    local_ip = get_local_ip()
    points, distances = [], []
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print("\n--- Verificador de Nivelamento do Prato ---")
        print(f"1. Faça upload do sketch 'plate_calibration.ino'.")
        print(f"2. IP do PC: {local_ip}")
        print(f"3. Verifique que o prato está VAZIO.")
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
                        return points, distances
                    try:
                        parts = line.strip().split(',')
                        dist = int(parts[0].split(':')[1])
                        theta = int(parts[1].split(':')[1])
                        
                        theta_rad = np.deg2rad(theta)
                        x = dist * np.cos(theta_rad)
                        y = dist * np.sin(theta_rad)
                        z = float(dist)

                        points.append([x, y, z])
                        distances.append(dist)
                    except (ValueError, IndexError): pass
    return points, distances

def analyze_and_visualize(points_list, distances_list):
    if len(points_list) < 20:
        print("\n[ERRO] Pontos insuficientes.")
        return

    points_np, distances_np = np.array(points_list), np.array(distances_list)

    print("\nFiltrando por distância...")
    median_distance = np.median(distances_np)
    min_dist, max_dist = median_distance - DISTANCE_TOLERANCE_MM, median_distance + DISTANCE_TOLERANCE_MM
    valid_indices = (distances_np >= min_dist) & (distances_np <= max_dist)
    
    filtered_points_np, outlier_points_np = points_np[valid_indices], points_np[~valid_indices]
    
    if len(filtered_points_np) < 20:
        print("[ERRO] Não restaram pontos após a filtragem.")
        return

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(filtered_points_np)
    
    plane_model, inliers_idx = pcd.segment_plane(distance_threshold=1.0, ransac_n=3, num_iterations=1000)
    [a, b, c, d] = plane_model
    
    normal = np.array([a, b, c])
    if normal[2] < 0: normal = -normal
    
    dot_product = np.clip(np.dot(normal, [0, 0, 1]), -1.0, 1.0)
    angle_deg = np.rad2deg(np.arccos(dot_product))
    
    print(f"Inclinação Total: {angle_deg:.2f} graus")
    
    angle_x = np.rad2deg(math.atan2(-normal[1], normal[2]))
    angle_y = np.rad2deg(math.atan2(normal[0], normal[2]))
    print(f"  - Eixo X (frente/trás): {angle_x:.2f} graus")
    print(f"  - Eixo Y (esquerda/direita): {angle_y:.2f} graus")

    inlier_cloud = pcd.select_by_index(inliers_idx)
    inlier_cloud.paint_uniform_color([0, 0, 1])
    
    noise_cloud = o3d.geometry.PointCloud()
    if len(outlier_points_np) > 0:
        noise_cloud.points = o3d.utility.Vector3dVector(outlier_points_np)
    noise_cloud.paint_uniform_color([1, 0, 0])

    bbox = inlier_cloud.get_axis_aligned_bounding_box()
    bbox.color = (0.8, 0.8, 0.8)
    
    print("\nA abrir visualizador...")
    o3d.visualization.draw_geometries([inlier_cloud, noise_cloud, bbox], 
                                      window_name="Análise de Nivelamento do Prato")

if __name__ == "__main__":
    p, d = receive_data()
    if p: analyze_and_visualize(p, d)