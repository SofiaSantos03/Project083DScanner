# --- START OF FILE test_mesh_generator.py (ou run_process.py) ---

import os
import sys

try:
    from generate_stl import build_universal_solid
except ImportError:
    print("[ERRO] O ficheiro 'generate_stl.py' não foi encontrado na mesma pasta.")
    sys.exit(1)

def main():
    """
    Função principal que executa o processo de geração de malha.
    """
    print("--- INICIANDO CONSTRUÇÃO DE MALHA UNIVERSAL ---")
    
    input_data_file = "3dScanner_Data.txt"
    output_stl_file = "output_universal_solid.stl"
    
    if not os.path.exists(input_data_file):
        print(f"\n[ERRO] O ficheiro de dados '{input_data_file}' não foi encontrado.")
        return

    try:
        build_universal_solid(input_data_file, output_stl_file)
    except Exception as e:
        print(f"\n[ERRO CRÍTICO] Ocorreu um erro inesperado: {e}")
        import traceback
        traceback.print_exc()

    print("\n--- PROCESSAMENTO CONCLUÍDO ---")

if __name__ == "__main__":
    main()