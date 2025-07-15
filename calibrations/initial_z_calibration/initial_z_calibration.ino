#include <AccelStepper.h>
#include <Adafruit_VL53L0X.h>
#include <Wire.h>

// --- CONFIGURAÇÕES DOS MOTORES E SENSORES ---
#define TIPO_MOTOR_Z     AccelStepper::HALF4WIRE

// Pinos do motor do eixo Z
const int PINO_MOTOR_Z_IN1 = 6;
const int PINO_MOTOR_Z_IN2 = 7;
const int PINO_MOTOR_Z_IN3 = 8;
const int PINO_MOTOR_Z_IN4 = 9;

// Pino do fim de curso (sugestão: usar um pino que não seja o 13)
const int PINO_FIM_DE_CURSO = 13;

// Calibração dos passos do motor Z. Meça a distância que o eixo sobe para
// 4096 passos e ajuste este valor se necessário. (4096 passos / 10mm = 409.6)
const float PASSOS_POR_MM_Z = 409.6; 

// --- CONFIGURAÇÕES DA CALIBRAÇÃO ---
// Se a distância medida saltar para um valor acima deste (em mm), 
// o código considera que encontrou a borda do prato.
const int LIMITE_DETECCAO_SALTO_MM = 50;

// --- INICIALIZAÇÃO DOS OBJETOS ---
AccelStepper motorZ(TIPO_MOTOR_Z, PINO_MOTOR_Z_IN1, PINO_MOTOR_Z_IN3, PINO_MOTOR_Z_IN2, PINO_MOTOR_Z_IN4);
Adafruit_VL53L0X lox = Adafruit_VL53L0X();

void setup() {
  // Inicializa a comunicação serial para vermos os resultados
  Serial.begin(115200);
  while (!Serial); // Aguarda a abertura do Monitor Serial
  Serial.println("\n--- Ferramenta de Calibração da Altura Inicial (Z-Homing Autónomo) ---");

  // Inicializa o sensor de distância
  Serial.print("Inicializando sensor VL53L0X... ");
  if (!lox.begin()) {
    Serial.println(F("Falha. Verifique a conexão do sensor."));
    while (1); // Para a execução se o sensor não for encontrado
  }
  Serial.println("OK.");

  // Configura o pino do fim de curso e o motor
  pinMode(PINO_FIM_DE_CURSO, INPUT_PULLUP);
  motorZ.setMaxSpeed(800);
  motorZ.setAcceleration(500);

  // --------------------------------------------------------------------
  // FASE 0: SUBIR PARA GARANTIR QUE O FIM DE CURSO ESTÁ LIVRE
  // --------------------------------------------------------------------
  Serial.print("Fase 0: A verificar o estado do fim de curso... ");
  // Verifica se, ao ligar, o interruptor já está pressionado (em estado LOW)
  if (digitalRead(PINO_FIM_DE_CURSO) == LOW) {
    Serial.println("Pressionado. A subir para libertar...");
    // Sobe um pouco (ex: 2mm) para garantir que o interruptor é libertado.
    // Lembre-se: um valor negativo no 'move' faz o motor SUBIR.
    motorZ.move(-round(PASSOS_POR_MM_Z * 2)); 
    while (motorZ.distanceToGo() != 0) {
      motorZ.run();
    }
  }
  Serial.println("OK. Fim de curso libertado.");
  delay(500);


  // --------------------------------------------------------------------
  // FASE 1: HOMING FÍSICO (DESCIDA ATÉ AO FIM DE CURSO)
  // --------------------------------------------------------------------
  Serial.print("Fase 1: A descer para encontrar o ponto zero físico... ");
  motorZ.setSpeed(800); // Velocidade de descida (positiva na sua configuração)
  while (digitalRead(PINO_FIM_DE_CURSO) == HIGH) {
    motorZ.runSpeed();
  }
  motorZ.stop();
  motorZ.setCurrentPosition(0); // Define esta posição como o zero absoluto
  Serial.println("OK!");
  delay(1000);

  // --------------------------------------------------------------------
  // FASE 2: SUBIDA LENTA PARA ENCONTRAR A SUPERFÍCIE DO PRATO
  // --------------------------------------------------------------------
  Serial.println("Fase 2: A subir lentamente e a medir para encontrar a superfície do prato...");
  Serial.println("Distância medida:");

  motorZ.setSpeed(-500); // Velocidade de subida (negativa)
  VL53L0X_RangingMeasurementData_t measure;
  bool bordaDetectada = false;

  while (!bordaDetectada) {
    motorZ.runSpeed(); // Move o motor um pouco para cima
    lox.rangingTest(&measure, false); // Faz uma leitura de distância
    
    // Apenas processa se a leitura for válida
    if (measure.RangeStatus != 4) {
      Serial.print("  -> ");
      Serial.print(measure.RangeMilliMeter);
      Serial.println(" mm");

      // Condição de paragem: se a distância medida der um salto para um valor grande
      if (measure.RangeMilliMeter > LIMITE_DETECCAO_SALTO_MM) {
        bordaDetectada = true;
      }
    }
    delay(10); // Pequena pausa para estabilidade entre medições
  }

  motorZ.stop(); // Para o motor assim que a borda é detectada
  long posicaoFinalPassos = motorZ.currentPosition();
  float alturaFinalMM = abs(posicaoFinalPassos) / PASSOS_POR_MM_Z;

  // --------------------------------------------------------------------
  // FASE 3: APRESENTAÇÃO DOS RESULTADOS FINAIS
  // --------------------------------------------------------------------
  Serial.println("\n----------------------------------------------------");
  Serial.println(">>> CALIBRAÇÃO CONCLUÍDA <<<");
  Serial.println("----------------------------------------------------");
  Serial.print("A altura da superfície do prato (do fim de curso até à borda) é de: ");
  Serial.print(alturaFinalMM, 2);
  Serial.println(" mm");
  Serial.print("Este valor corresponde a: ");
  Serial.print(abs(posicaoFinalPassos));
  Serial.println(" passos.");
  Serial.println("\nInstruções:");
  Serial.println("1. Copie o número de passos acima.");
  Serial.println("2. Cole esse valor na variável 'PASSOS_PARA_SUBIR_INICIAL' do seu sketch de scan principal.");
  
  motorZ.disableOutputs(); // Desliga o motor para poder movê-lo manualmente
  while(1); // Para a execução do programa aqui
}

void loop() {
  // O loop principal está vazio, pois tudo é feito na função setup().
}