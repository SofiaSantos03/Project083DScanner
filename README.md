# Project083DScanner
Programming for 3D Scanner Project
# Projeto de Scanner 3D

Este projeto implementa um sistema completo para um scanner 3D DIY, composto por um servidor em Python para receber dados e um script para gerar uma malha 3D (ficheiro `.stl`) a partir desses dados. O sistema foi projetado para funcionar com um scanner baseado em Arduino que envia dados de distância, ângulo e altura via Wi-Fi.

A versão final utiliza a biblioteca **Open3D** para o processamento da nuvem de pontos e geração da malha, pois provou ser robusta para criar modelos 3D imprimíveis.

## Componentes do Projeto

### Hardware (Não incluído neste repositório)
*   **Arduino** com capacidade de Wi-Fi (ex: ESP32, Arduino com WiFi Shield).
*   **Sensor de Distância:** VL53L0X (Time-of-Flight).
*   **Dois Motores de Passo:** Um para a rotação do prato e outro para o movimento vertical (eixo Z).
*   **Estrutura Mecânica:** Para montar todos os componentes.

### Software
1.  **Servidor de Receção (`scanner_receiver.py`):**
    *   Um servidor TCP em Python que escuta numa porta específica (porta 5000 por defeito).
    *   Recebe os dados do scanner no formato `"Dist:123,Theta:90,Z:10.00"`.
    *   Converte os dados de coordenadas polares para cartesianas (X, Y, Z).
    *   Guarda a nuvem de pontos num ficheiro de texto (`3dScanner_Data.txt`).
    *   No final da recolha, chama automaticamente o script de geração de malha.

2.  **Geração da Malha (`generate_stl.py`):**
    *   Um módulo em Python que usa a biblioteca **Open3D**.
    *   Carrega a nuvem de pontos do ficheiro de texto.
    *   Converte as unidades para metros (melhor para os algoritmos).
    *   Limpa a nuvem de pontos, removendo ruído (outliers).
    *   Calcula as normais da superfície.
    *   Gera uma malha 3D usando o algoritmo **Ball-Pivoting**, que é bom a preservar detalhes e buracos.
    *   Guarda o resultado final como um ficheiro `.stl`.

3.  **Usar 3D Builder do Windows:**
    *   Após a geração do `.stl`, recomenda-se abrir o modelo na aplicação **3D Builder** do Windows.
    *   Esta ferramenta permite detetar e corrigir automaticamente falhas na malha (como buracos ou superfícies malformadas).
    *   A reparação assegura que o modelo esteja pronto para impressão 3D ou visualização em software CAD.

## Requisitos

É necessário ter **Python 3.12** instalado. Este projeto depende das seguintes bibliotecas externas:

*   **`numpy`**: Para cálculos numéricos e manipulação de arrays.
*   **`open3d`**: A biblioteca principal para todo o processamento 3D (nuvens de pontos, malhas, visualização).

### Instalação das Bibliotecas
Pode instalar todas as dependências necessárias com um único comando no seu terminal:

```bash
pip install numpy open3d 