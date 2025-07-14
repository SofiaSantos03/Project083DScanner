# --- START OF FILE test_stl_generation.py ---

import os
import sys

# --- INSTRUÇÕES ---
# 1. Coloque este ficheiro no mesmo diretório que 'generate_stl.py' e '3dScanner_Data.txt'.
# 2. Execute-o a partir da linha de comandos com: python test_stl_generation.py
# 3. Ele irá chamar a função 'generate_mesh' e tentar criar o ficheiro STL.

def run_test():
    """
    Função principal que executa o teste de geração de STL.
    """
    print("--- Script de Teste para Geração de Malha STL ---")

    # Passo 1: Verificar se os ficheiros necessários existem
    
    # Tenta importar a função principal do seu outro script.
    try:
        from generate_stl_test import generate_mesh
        print("[OK] Ficheiro 'generate_stl.py' encontrado e função 'generate_mesh' importada.")
    except ImportError:
        print("\n[ERRO CRÍTICO] O ficheiro 'generate_stl.py' não foi encontrado neste diretório.")
        print("Certifique-se de que ambos os scripts estão na mesma pasta.")
        sys.exit(1) # Sai do programa

    # Define os nomes dos ficheiros de entrada e saída
    input_file = "3dScanner_Data.txt"
    output_file = "test_output.stl" # Usamos um nome diferente para não sobreescrever o original

    # Verifica se o ficheiro de dados existe
    if not os.path.exists(input_file):
        print(f"\n[ERRO CRÍTICO] O ficheiro de dados '{input_file}' não foi encontrado.")
        print("Certifique-se de que os dados do scan estão nesta pasta.")
        sys.exit(1)
    
    print(f"[OK] Ficheiro de dados '{input_file}' encontrado.")

    # Passo 2: Executar a função de geração de malha
    
    print("\n-------------------------------------------------")
    print(f"A chamar a função 'generate_mesh' para criar '{output_file}'...")
    print("-------------------------------------------------")

    try:
        # Chama a função do outro ficheiro, passando os nomes dos ficheiros
        generate_mesh(input_filepath=input_file, output_filepath=output_file)
        
        # Se a função terminar sem erros, chegamos aqui.
        print("-------------------------------------------------")
        print("Função 'generate_mesh' executada sem erros fatais.")
        print("-------------------------------------------------")

    except Exception as e:
        # Se ocorrer qualquer erro DENTRO da função generate_mesh, ele será capturado aqui.
        print("\n-------------------------------------------------")
        print(f"[ERRO INESPERADO] Ocorreu um erro durante a execução de 'generate_mesh':")
        print(f"Detalhes: {e}")
        print("-------------------------------------------------")
        sys.exit(1)

    # Passo 3: Verificar o resultado
    if os.path.exists(output_file):
        print(f"\n[SUCESSO] O ficheiro de saída '{output_file}' foi criado!")
        print("Pode agora abri-lo num visualizador de STL para verificar o resultado.")
    else:
        print(f"\n[AVISO] A função foi executada, mas o ficheiro de saída '{output_file}' não foi criado.")
        print("Verifique as mensagens de erro acima para perceber o que pode ter corrido mal (ex: todos os pontos foram filtrados).")

# Ponto de entrada do script
if __name__ == "__main__":
    run_test()