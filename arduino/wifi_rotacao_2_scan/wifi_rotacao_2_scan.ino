#include <WiFiS3.h>
#include <Wire.h>
#include <AccelStepper.h>
#include <Adafruit_VL53L0X.h>
#include <math.h>

// --- CONFIGURAÇÕES DE REDE ---
const char ssid[] = "Vodafone-D433A6";
const char pass[] = "datreta12345.";
const char server[] = "192.168.20.73";
const int port = 5000;

// --- CONFIGURAÇÕES DOS MOTORES E SENSORES ---

// [ALTERAÇÃO] Voltando a usar HALF4WIRE para o prato, para uma rotação mais suave.
#define TIPO_MOTOR_PRATO AccelStepper::HALF4WIRE
#define TIPO_MOTOR_Z     AccelStepper::HALF4WIRE

const int PINO_MOTOR_Z_IN1 = 6; const int PINO_MOTOR_Z_IN2 = 7; const int PINO_MOTOR_Z_IN3 = 8; const int PINO_MOTOR_Z_IN4 = 9;
const long PASSOS_PARA_SUBIR_INICIAL = 15432; 
const long PASSOS_PARA_SUBIR_CAMADA = 819; // Para 2mm por camada

const int PINO_MOTOR_PRATO_IN1 = 2; const int PINO_MOTOR_PRATO_IN2 = 3; const int PINO_MOTOR_PRATO_IN3 = 4; const int PINO_MOTOR_PRATO_IN4 = 5;

// [ALTERAÇÃO] Como voltamos para HALF4WIRE, o número de passos calibrado é duplicado.
const long PASSOS_POR_ROTACAO_PRATO = 4174; 

const int PINO_FIM_DE_CURSO = 13;
const float ALTURA_MAXIMA_FISICA_MM = 160.0; 

// --- INICIALIZAÇÃO DOS OBJETOS ---
WiFiClient client;
AccelStepper motorZ(TIPO_MOTOR_Z, PINO_MOTOR_Z_IN1, PINO_MOTOR_Z_IN3, PINO_MOTOR_Z_IN2, PINO_MOTOR_Z_IN4);
AccelStepper motorPrato(TIPO_MOTOR_PRATO, PINO_MOTOR_PRATO_IN1, PINO_MOTOR_PRATO_IN3, PINO_MOTOR_PRATO_IN2, PINO_MOTOR_PRATO_IN4);
Adafruit_VL53L0X lox = Adafruit_VL53L0X();

// --- VARIÁVEIS GLOBAIS DE CONTROLO ---
bool homingCompleto = false; long offsetPassosPrato = 0; int status = WL_IDLE_STATUS; int camadaAtual = 1; float alturaMaximaScanMM = 0;

void setup() {
  Serial.begin(115200);
  while (!Serial); 

  Serial.print("Tentando conectar a rede: ");
  Serial.println(ssid);
  while (status != WL_CONNECTED) { status = WiFi.begin(ssid, pass); delay(5000); Serial.print("."); }
  Serial.println("\nWiFi conectado com sucesso!");
  Serial.print("Endereço IP do Arduino: "); Serial.println(WiFi.localIP());
  Serial.println("Inicializando sensor VL53L0X...");
  if (!lox.begin()) { Serial.println(F("Falha ao iniciar o sensor VL53L0X.")); while (1); }
  Serial.println("Sensor VL53L0X OK.");
  pinMode(PINO_FIM_DE_CURSO, INPUT_PULLUP);
  
  motorZ.setMaxSpeed(700);
  motorZ.setAcceleration(350);

  motorPrato.setMaxSpeed(700); 
  motorPrato.setAcceleration(400);

  Serial.println("Fase 1: Homing do eixo Z...");
  motorZ.setSpeed(500);
  unsigned long tempoPrimeiroSinalLow = 0;
  const int intervaloDebounce = 50;
  bool botaoConfirmadoPressionado = false;
  while (!botaoConfirmadoPressionado) { motorZ.runSpeed(); if (digitalRead(PINO_FIM_DE_CURSO) == LOW) { if (tempoPrimeiroSinalLow == 0) tempoPrimeiroSinalLow = millis(); else if (millis() - tempoPrimeiroSinalLow > intervaloDebounce) botaoConfirmadoPressionado = true; } else { tempoPrimeiroSinalLow = 0; } }
  motorZ.stop();
  Serial.println("Ponto zero físico (fim de curso) encontrado!");
  motorZ.setCurrentPosition(0); 
  motorPrato.setCurrentPosition(0);
  Serial.print("Subindo para a posição inicial de scan...");
  motorZ.moveTo(-PASSOS_PARA_SUBIR_INICIAL);
  while (motorZ.distanceToGo() != 0) motorZ.run();
  Serial.println(" Posição inicial atingida.");
  motorZ.setCurrentPosition(0); 
  Serial.println("Altura de referência (Z=0) definida na posição inicial do scan.");
  Serial.println("\n----------------------------------------------------");
  Serial.print("O limite físico do eixo Z é de "); Serial.print(ALTURA_MAXIMA_FISICA_MM); Serial.println(" mm.");
  Serial.println("Por favor, insira a altura máxima do scan em milímetros (mm)");
  Serial.println("e pressione Enter no Monitor Serial:");
  while (Serial.available() == 0) { delay(100); }
  alturaMaximaScanMM = Serial.parseFloat(); 
  if (alturaMaximaScanMM > ALTURA_MAXIMA_FISICA_MM) { Serial.print("AVISO: A altura solicitada excede o limite físico. Ajustando para "); Serial.print(ALTURA_MAXIMA_FISICA_MM); Serial.println(" mm."); alturaMaximaScanMM = ALTURA_MAXIMA_FISICA_MM; }
  Serial.print("Altura máxima do scan definida para: "); Serial.print(alturaMaximaScanMM); Serial.println(" mm");
  Serial.println("----------------------------------------------------");
  delay(2000);
  Serial.print("Conectando ao servidor "); Serial.print(server); Serial.print(":"); Serial.println(port);
  if (!client.connect(server, port)) { Serial.println("Falha na conexão com o servidor Python."); while(1); }
  Serial.println("Conectado ao servidor! A iniciar scan.");
  homingCompleto = true;
  delay(1000);
}

void loop() {
  if (!homingCompleto) return;
  if (!client.connected()) { Serial.println("ERRO: Servidor desconectado. Parando o scan."); while(1); }
  
  float alturaAtualZ_mm = (-motorZ.currentPosition() / (float)PASSOS_PARA_SUBIR_CAMADA * 2.0);

  if (alturaAtualZ_mm >= alturaMaximaScanMM) { Serial.println("\n--- Altura máxima de scan definida pelo utilizador atingida. Digitalização concluída! ---"); client.println("END"); client.stop(); motorZ.disableOutputs(); motorPrato.disableOutputs(); while (1); }
  Serial.print("Iniciando rotação da camada #"); Serial.print(camadaAtual); Serial.print(" (Altura atual: "); Serial.print(alturaAtualZ_mm, 2); Serial.print(" mm / "); Serial.print(alturaMaximaScanMM); Serial.print(" mm)"); Serial.println();
  char dataBuffer[100]; VL53L0X_RangingMeasurementData_t measure;
  for (int angulo = 0; angulo < 360; angulo += 5) {
    long posicaoAlvo = round((angulo / 360.0) * PASSOS_POR_ROTACAO_PRATO);
    motorPrato.moveTo(posicaoAlvo + offsetPassosPrato);
    while (motorPrato.distanceToGo() != 0) motorPrato.run();
    
    delay(30); 
    
    lox.rangingTest(&measure, false);
    
    if (measure.RangeStatus != 4) {
      int distancia = measure.RangeMilliMeter; char alturaStr[10]; dtostrf(alturaAtualZ_mm, 4, 2, alturaStr);
      sprintf(dataBuffer, "Dist:%d,Theta:%d,Z:%s", distancia, angulo, alturaStr);
      if (client.connected()) { client.println(dataBuffer); } else { Serial.println("ERRO: Conexão perdida durante o envio de dados."); while(1); }
    }

    delay(50);
  }
  offsetPassosPrato += PASSOS_POR_ROTACAO_PRATO;
  Serial.println("Rotação da camada concluída.");

  Serial.println("Subindo eixo Z para a próxima camada (2 mm)...");
  motorZ.move(-PASSOS_PARA_SUBIR_CAMADA);
  while (motorZ.distanceToGo() != 0) motorZ.run();
  
  camadaAtual++;
  Serial.println("Eixo Z posicionado. Próxima camada pronta.");
  delay(100);
}