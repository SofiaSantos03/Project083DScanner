# Projeto de Scanner 3D (Project083DScanner)

Este repositório contém o software de controlo e processamento para um scanner 3D. O sistema é composto por um servidor em Python que recebe dados de um scanner baseado em Arduino, um visualizador em tempo real e um pipeline de geração de malha 3D sofisticado que transforma nuvens de pontos ruidosas em modelos `.stl` sólidos e imprimíveis.

O projeto foi calibrado e utiliza algoritmos personalizados, como **interpolação por spline** e **triangulação em leque**, para garantir uma alta fidelidade geométrica e modelos 3D sem buracos.

## Funcionalidades Principais

*   **Recolha de Dados via Wi-Fi:** Um servidor Python recebe dados de distância, ângulo e altura em tempo real.
*   **Calibração de Precisão:** Implementa um sistema de calibração em duas fases (hardware no Arduino, geometria no Python) para garantir que os modelos 3D tenham as dimensões corretas.
*   **Visualização em Tempo Real:** Um script (`live_visualizer.py`) permite monitorizar a formação da nuvem de pontos durante o scan, ideal para depuração.
*   **Geração de Malha de Alta Qualidade:** Utiliza um pipeline avançado com **Open3D** e **SciPy** para:
    1.  Separar a nuvem de pontos em camadas.
    2.  Suavizar o ruído de cada camada usando **interpolação por spline**, preservando a forma original do objeto.
    3.  Construir as paredes do modelo.
    4.  Fechar o topo e a base com **tampas perfeitamente planas** através de triangulação em leque.
*   **Automação:** O processo de geração da malha é iniciado automaticamente no final da recolha de dados.

## Componentes do Projeto

### Hardware (Exemplo de Configuração)
*   **Microcontrolador:** Arduino com capacidade Wi-Fi.
*   **Sensor de Distância:** VL53L0X (Time-of-Flight) para medições precisas.
*   **Motores:** Dois motores de passo com drivers (e.g., A4988) para a rotação da plataforma e para o movimento vertical (eixo Z).
*   **Estrutura Mecânica:** Uma montagem que mantém o sensor fixo e permite a rotação e elevação do objeto.

### Software
1.  **`scanner_receiver.py` (Servidor Principal):**
    *   Inicia um servidor TCP que aguarda a conexão do scanner.
    *   Recebe dados no formato `"D:123,A:90,H:10.00"`.
    *   Aplica as constantes de calibração (`SENSOR_OFFSET_MM`, `OFFSET_X`, `OFFSET_Y`) para converter os dados em coordenadas cartesianas (X, Y, Z) precisas.
    *   Guarda a nuvem de pontos em `3dScanner_Data.txt`.
    *   No final, chama `generate_stl.py` para criar o modelo 3D.

2.  **`generate_stl.py` (O Gerador de Malha):**
    *   Carrega a nuvem de pontos.
    *   Separa os pontos em camadas com base na altura Z.
    *   Para cada camada, utiliza **interpolação por spline** (`scipy.interpolate`) para criar um contorno suave e preciso, eliminando o ruído do sensor sem perder a forma do objeto.
    *   Gera as faces das paredes que ligam as camadas suavizadas.
    *   Calcula os pontos centrais do topo e da base e gera tampas perfeitamente planas através de **triangulação em leque**.
    *   Combina tudo numa única malha 3D e guarda-a como `output_universal_solid.stl`.

3.  **`live_visualizer.py` (Ferramenta de Depuração):**
    *   Um script que lê o ficheiro `3dScanner_Data.txt` em tempo real e plota a nuvem de pontos à medida que ela é formada. Essencial para verificar a calibração e o alinhamento durante um scan.

4.  **`test_mesh_generator.py` (Executor Manual):**
    *   Um script simples que permite executar o processo de geração de malha (`generate_stl.py`) num ficheiro `3dScanner_Data.txt` já existente, sem precisar de correr o servidor.

## Requisitos de Software

É necessário ter **Python 3.10** instalado. Este projeto depende das seguintes bibliotecas:

*   **`numpy`**: Para cálculos numéricos.
*   **`open3d`**: Para todo o processamento 3D (nuvens de pontos, malhas, visualização).
*   **`matplotlib`**: Para o visualizador em tempo real.
*   **`scipy`**: Especificamente para a interpolação por spline na geração da malha.

### Instalação das Bibliotecas
Pode instalar todas as dependências com um único comando no terminal:

```bash
pip install numpy open3d matplotlib scipy

=====================================================
GUIA RÁPIDO: Como Usar e Calibrar o Scanner 3D
=====================================================

Para obter resultados precisos do seu scanner 3D, é necessário seguir este processo de calibração em duas partes. Primeiro, calibramos o sensor no Arduino para que ele se torne uma "régua" precisa. Depois, informamos o software em Python sobre a geometria exata da sua montagem.


-----------------------------------------------------
Parte 1: Calibração do Sensor (no Arduino)
-----------------------------------------------------

O objetivo é garantir que o sensor reporta a distância física real.

1. Colocar um objeto plano a uma distância conhecida e fácil de medir do sensor. Por exemplo, usar uma régua para o posicionar exatamente a 100 mm.

2. No código principal do Arduino (.ino), adicionar temporariamente uma linha como `Serial.println(distanciaCorrigida);` dentro do loop de medição para se poder ver os valores. Fazer o upload do código.

3. Abrir o Serial Monitor no Arduino IDE. Observar a distância que o sensor está a ler.

4. Comparar a distância lida com a distância real (100 mm).
   - Se os valores forem muito próximos, a calibração está boa.
   - Se houver uma diferença consistente, ajustar a constante `FATOR_CORRECAO_DISTANCIA` no topo do código .ino.

   Usar a seguinte fórmula para encontrar o novo fator:
   Novo_Fator = Fator_Antigo * (Distancia_Real / Distancia_Lida)

   Fazer o upload e verifique novamente até que a leitura seja precisa.


-----------------------------------------------------
Parte 2: Calibração da Geometria (no Python)
-----------------------------------------------------
Agora que o sensor está calibrado, precisamos informar ao software Python como converter os dados do sensor em coordenadas 3D precisas.

1. Calibrar o `SENSOR_OFFSET_MM`:
   - Medir com uma régua a distância EXATA, em milímetros, desde a lente do sensor até ao centro exato do prato rotativo.
   - Abrir o ficheiro `scanner_receiver.py`.
   - Colocar o valor que acabou de medir na variável `SENSOR_OFFSET_MM`.

2. Calibrar `OFFSET_X` e `OFFSET_Y` (para centralização fina):
   - No ficheiro `scanner_receiver.py`, definir `OFFSET_X = 0.0` e `OFFSET_Y = 0.0`.
   - Fazer um scan de um objeto cilíndrico.
   - Executar o script `live_visualizer.py` para ver a nuvem de pontos.
   - Observar o centro do círculo. Se ele estiver deslocado, anotar as coordenadas do centro. Por exemplo, se o centro estiver em (X=5, Y=-2).
   - Os offsets finais serão os valores opostos para corrigir o desvio:
     OFFSET_X = -5.0
     OFFSET_Y = 2.0
   - Atualizar estas variáveis no ficheiro `scanner_receiver.py`.


-----------------------------------------------------
Como Executar um Scan Completo
-----------------------------------------------------

1. Certificar de que o Arduino está ligado e pronto.

2. No computador, abrir um terminal e executar o servidor Python:
   python scanner_receiver.py

3. (Opcional) Para ver o progresso em tempo real, abrir um SEGUNDO terminal e executar o visualizador:
   python live_visualizer.py

4. Iniciar o processo de scan no Arduino (pressionando reset ou enviando um comando, dependendo da sua configuração).

5. Aguardar o final do scan. O Arduino enviará o sinal "END", e o script `scanner_receiver.py` irá detetá-lo e iniciar automaticamente a geração do ficheiro .stl. O ficheiro final será guardado como `output_universal_solid.stl`.