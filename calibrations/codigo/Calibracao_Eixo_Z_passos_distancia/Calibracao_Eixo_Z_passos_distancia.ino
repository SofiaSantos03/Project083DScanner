#include <AccelStepper.h>

// --- CONFIGURAÇÕES DO MOTOR Z ---
// Certifique-se que estes pinos correspondem à sua montagem
#define TIPO_MOTOR_Z AccelStepper::HALF4WIRE
const int PINO_MOTOR_Z_IN1 = 6;
const int PINO_MOTOR_Z_IN2 = 7;
const int PINO_MOTOR_Z_IN3 = 8;
const int PINO_MOTOR_Z_IN4 = 9;

// --- CONFIGURAÇÃO DO FIM DE CURSO ---
const int PINO_FIM_DE_CURSO = 12;

// --- VALOR DE CALIBRAÇÃO INICIAL (O QUE VAMOS TESTAR E CORRIGIR) ---
// Com base no seu código anterior: 819 passos = 2 mm
// Então, 1 mm = 819 / 2 = 409.5 passos.
float passosPorMilimetro = 409.5; 

// --- INICIALIZAÇÃO DOS OBJETOS ---
AccelStepper motorZ(TIPO_MOTOR_Z, PINO_MOTOR_Z_IN1, PINO_MOTOR_Z_IN3, PINO_MOTOR_Z_IN2, PINO_MOTOR_Z_IN4);

void setup() {
  Serial.begin(115200);
  while (!Serial);

  Serial.println("\n--- Ferramenta de Calibração do Eixo Z ---");
  
  pinMode(PINO_FIM_DE_CURSO, INPUT_PULLUP);
  
  motorZ.setMaxSpeed(700);
  motorZ.setAcceleration(350);

  // Fase 1: Homing físico no fim de curso
  Serial.println("A procurar o ponto zero físico (fim de curso)...");
  motorZ.setSpeed(500); // Lembre-se: positivo = descer
  
  // Debounce para o botão de fim de curso
  unsigned long tempoPrimeiroSinalLow = 0;
  const int intervaloDebounce = 50;
  bool botaoConfirmadoPressionado = false;
  
  while (!botaoConfirmadoPressionado) { 
    motorZ.runSpeed(); 
    if (digitalRead(PINO_FIM_DE_CURSO) == LOW) { 
      if (tempoPrimeiroSinalLow == 0) tempoPrimeiroSinalLow = millis(); 
      else if (millis() - tempoPrimeiroSinalLow > intervaloDebounce) botaoConfirmadoPressionado = true; 
    } else { 
      tempoPrimeiroSinalLow = 0; 
    } 
  }
  motorZ.stop();
  motorZ.setCurrentPosition(0); 
  Serial.println("Ponto zero encontrado! Eixo Z está na posição 0.");
}

void loop() {
  Serial.println("\n-------------------------------------------");
  Serial.print("Calibração atual: ");
  Serial.print(passosPorMilimetro, 2);
  Serial.println(" passos por mm.");
  Serial.println("Insira a distância de teste em milímetros (mm) e pressione Enter:");

  // Espera pela entrada do utilizador
  while (Serial.available() == 0) {
    delay(100);
  }
  float distanciaDesejada = Serial.parseFloat();
  
  // Limpa o buffer de entrada caso haja caracteres extras
  while (Serial.available() > 0) {
    Serial.read();
  }
  
  if (distanciaDesejada <= 0) {
    Serial.println("Distância inválida. Por favor, insira um número positivo.");
    return;
  }

  Serial.print("OK. A tentar subir ");
  Serial.print(distanciaDesejada);
  Serial.println(" mm...");

  // Calcula o número de passos a mover com base na calibração atual
  long passosParaMover = round(distanciaDesejada * passosPorMilimetro);
  
  // Lembre-se: negativo = subir
  motorZ.moveTo(-passosParaMover);
  while (motorZ.distanceToGo() != 0) {
    motorZ.run();
  }
  
  Serial.println("Movimento concluído.");
  Serial.println("Por favor, meça a distância REAL que o eixo subiu (em mm).");
  Serial.println("Depois, insira o valor medido e pressione Enter:");

  // Espera pela medida real
  while (Serial.available() == 0) {
    delay(100);
  }
  float distanciaReal = Serial.parseFloat();
  
  // Limpa o buffer de entrada
  while (Serial.available() > 0) {
    Serial.read();
  }

  if (distanciaReal <= 0) {
    Serial.println("Medida inválida. A reiniciar o teste.");
    // Desce de volta para a posição zero para o próximo teste
    motorZ.moveTo(0);
    while (motorZ.distanceToGo() != 0) motorZ.run();
    return;
  }
  
  // --- O CÁLCULO MÁGICO ---
  // A nova calibração é calculada com uma regra de três:
  // (passos que ele moveu / distância que ele realmente se moveu)
  float novaCalibracao = (float)passosParaMover / distanciaReal;

  Serial.println("\n--- RESULTADO DA CALIBRAÇÃO ---");
  Serial.print("O motor moveu ");
  Serial.print(passosParaMover);
  Serial.println(" passos.");
  Serial.print("Isso resultou num movimento real de ");
  Serial.print(distanciaReal, 2);
  Serial.println(" mm.");
  Serial.print("O novo valor de calibração calculado é: ");
  Serial.print(novaCalibracao, 4);
  Serial.println(" passos/mm");
  Serial.println("-------------------------------");

  // Atualiza o valor para o próximo teste
  passosPorMilimetro = novaCalibracao;
  
  Serial.println("A descer de volta para a posição zero para o próximo teste...");
  motorZ.moveTo(0);
  while(motorZ.distanceToGo() != 0) {
    motorZ.run();
  }
  Serial.println("Pronto para o próximo teste.");
}