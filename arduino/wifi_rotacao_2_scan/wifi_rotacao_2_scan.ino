// =======================================================================
// ===     CÓDIGO FIRMWARE FINAL E CALIBRADO PARA SCANNER 3D           ===
// =======================================================================
// Versão: 2.2 - Correção da Leitura de Altura + Calibração de Precisão
// =======================================================================

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

// =======================================================================
// ===               INÍCIO DA CONFIGURAÇÃO DE CALIBRAÇÃO              ===
// =======================================================================

// --- CALIBRAÇÃO E MELHORIA DE QUALIDADE ---
// Fator para corrigir a precisão da distância.
const float FATOR_CORRECAO_DISTANCIA =1.0;// 0.9956; valor real/valor medido(ou media do valor medido)

// Número de leituras a fazer por cada ponto para reduzir o ruído.
const int NUMERO_DE_AMOSTRAS = 5;

// =======================================================================
// ===                 FIM DA CONFIGURAÇÃO DE CALIBRAÇÃO               ===
// =======================================================================

// --- CONFIGURAÇÕES DOS MOTORES E SENSORES ---
#define TIPO_MOTOR_PRATO AccelStepper::HALF4WIRE
#define TIPO_MOTOR_Z     AccelStepper::HALF4WIRE
const int PINO_MOTOR_Z_IN1 = 6; const int PINO_MOTOR_Z_IN2 = 7; const int PINO_MOTOR_Z_IN3 = 8; const int PINO_MOTOR_Z_IN4 = 9;
const float PASSOS_POR_MM_Z = 2068.20;
const float ALTURA_CAMADA_MM = 1.0;
const int   PASSO_ANGULAR_GRAUS = 1;
const long PASSOS_PARA_SUBIR_INICIAL = round(10.0 * PASSOS_POR_MM_Z);
const long PASSOS_PARA_SUBIR_CAMADA = round(ALTURA_CAMADA_MM * PASSOS_POR_MM_Z);
const int PINO_MOTOR_PRATO_IN1 = 2; const int PINO_MOTOR_PRATO_IN2 = 3; const int PINO_MOTOR_PRATO_IN3 = 4; const int PINO_MOTOR_PRATO_IN4 = 5;
const long PASSOS_POR_ROTACAO_PRATO = 4174;
const int PINO_FIM_DE_CURSO = 12;
const float ALTURA_MAXIMA_FISICA_MM = 160.0;
const int VELOCIDADE_HOMING_Z = 1000;

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

  Serial.println("\n--- Scanner 3D - MODO CALIBRADO FINAL ---");
  Serial.print("Fator de Correção de Distância: "); Serial.println(FATOR_CORRECAO_DISTANCIA, 4);

  Serial.print("Tentando conectar a rede: "); Serial.println(ssid);
  while (status != WL_CONNECTED) { status = WiFi.begin(ssid, pass); delay(5000); Serial.print("."); }
  Serial.println("\nWiFi conectado com sucesso!"); Serial.print("Endereço IP do Arduino: "); Serial.println(WiFi.localIP());
  Serial.println("Inicializando sensor VL53L0X...");
  if (!lox.begin()) { Serial.println(F("Falha ao iniciar o sensor VL53L0X.")); while (1); }
  Serial.println("Sensor VL53L0X OK."); pinMode(PINO_FIM_DE_CURSO, INPUT_PULLUP);
  
  motorZ.setMaxSpeed(700); motorZ.setAcceleration(350);
  motorPrato.setMaxSpeed(700); motorPrato.setAcceleration(400);

  Serial.println("Fase 1: Homing do eixo Z...");
  motorZ.setSpeed(VELOCIDADE_HOMING_Z);
  unsigned long tempoPrimeiroSinalLow = 0; const int intervaloDebounce = 50; bool botaoConfirmadoPressionado = false;
  while (!botaoConfirmadoPressionado) {
    motorZ.runSpeed();
    if (digitalRead(PINO_FIM_DE_CURSO) == LOW) {
      if (tempoPrimeiroSinalLow == 0) tempoPrimeiroSinalLow = millis();
      else if (millis() - tempoPrimeiroSinalLow > intervaloDebounce) botaoConfirmadoPressionado = true;
    } else { tempoPrimeiroSinalLow = 0; }
  }
  motorZ.stop(); motorZ.setCurrentPosition(0);
  Serial.println("Ponto zero físico (fim de curso) encontrado!");

  Serial.print("Subindo para a posição inicial de scan...");
  motorZ.moveTo(-PASSOS_PARA_SUBIR_INICIAL);
  while (motorZ.distanceToGo() != 0) motorZ.run();
  motorZ.setCurrentPosition(0); motorPrato.setCurrentPosition(0);
  Serial.println(" Posição inicial atingida.");
  
  Serial.println("\n----------------------------------------------------");
  
  // CORREÇÃO: Limpa qualquer dado antigo do buffer serial
  while (Serial.available() > 0) {
    Serial.read();
  }

  Serial.println("Por favor, insira a altura máxima do scan em milímetros (mm)");
  while (Serial.available() == 0) { delay(100); }
  alturaMaximaScanMM = Serial.parseFloat();
  if (alturaMaximaScanMM <= 0 || alturaMaximaScanMM > ALTURA_MAXIMA_FISICA_MM) { 
    if (alturaMaximaScanMM > ALTURA_MAXIMA_FISICA_MM) {
        Serial.print("AVISO: Altura excede o limite físico. Ajustando para "); Serial.print(ALTURA_MAXIMA_FISICA_MM); Serial.println(" mm."); 
        alturaMaximaScanMM = ALTURA_MAXIMA_FISICA_MM; 
    } else {
        Serial.println("AVISO: Altura inválida. Usando o valor máximo de 160 mm.");
        alturaMaximaScanMM = ALTURA_MAXIMA_FISICA_MM;
    }
  }
  Serial.print("Altura máxima do scan definida para: "); Serial.print(alturaMaximaScanMM); Serial.println(" mm");
  Serial.println("----------------------------------------------------"); delay(2000);
  Serial.print("Conectando ao servidor "); Serial.print(server); Serial.print(":"); Serial.println(port);
  if (!client.connect(server, port)) { Serial.println("Falha na conexão com o servidor Python."); while(1); }
  Serial.println("Conectado ao servidor! A iniciar scan.");
  homingCompleto = true;
  delay(1000);
}

void loop() {
  if (!homingCompleto) return;
  if (!client.connected()) { Serial.println("ERRO: Servidor desconectado. Parando o scan."); while(1); }
  
  float alturaAtualZ_mm = (camadaAtual - 1) * ALTURA_CAMADA_MM;

  if (alturaAtualZ_mm >= alturaMaximaScanMM) {
    Serial.println("\n--- Altura máxima de scan atingida. Digitalização concluída! ---");
    client.println("END"); client.stop();
    motorZ.disableOutputs(); motorPrato.disableOutputs();
    while (1);
  }
  
  Serial.print("Iniciando rotação da camada #"); Serial.print(camadaAtual);
  Serial.print(" (Altura atual: "); Serial.print(alturaAtualZ_mm, 2);
  Serial.print(" mm / "); Serial.print(alturaMaximaScanMM); Serial.print(" mm)");
  Serial.println();
  
  char dataBuffer[100];
  
  for (int angulo = 0; angulo < 360; angulo += PASSO_ANGULAR_GRAUS) {
    long posicaoAlvo = round((angulo / 360.0) * PASSOS_POR_ROTACAO_PRATO);
    motorPrato.moveTo(posicaoAlvo + offsetPassosPrato);
    while (motorPrato.distanceToGo() != 0) motorPrato.run();
    
    // --- LÓGICA DE MEDIÇÃO OTIMIZADA ---
    long somaDistancias = 0;
    int leiturasValidas = 0;
    VL53L0X_RangingMeasurementData_t measure;

    for (int i = 0; i < NUMERO_DE_AMOSTRAS; i++) {
      lox.rangingTest(&measure, false);
      if (measure.RangeStatus != 4) {
        somaDistancias += measure.RangeMilliMeter;
        leiturasValidas++;
      }
      delay(5);
    }

    if (leiturasValidas > 0) {
      float distanciaMediaLida = (float)somaDistancias / leiturasValidas;
      int distanciaCorrigida = (int)(distanciaMediaLida * FATOR_CORRECAO_DISTANCIA);
      
      char alturaStr[10];
      dtostrf(alturaAtualZ_mm, 4, 2, alturaStr);
      sprintf(dataBuffer, "D:%d,A:%d,Z:%s", distanciaCorrigida, angulo, alturaStr);
      
      if (client.connected()) {
        client.println(dataBuffer);
      } else {
        Serial.println("ERRO: Conexão perdida durante o envio de dados.");
        while(1);
      }
    }
    delay(30);
  }
  
  offsetPassosPrato += PASSOS_POR_ROTACAO_PRATO;
  Serial.println("Rotação da camada concluída.");
  Serial.print("Subindo eixo Z para a próxima camada...");
  motorZ.move(-PASSOS_PARA_SUBIR_CAMADA);
  while (motorZ.distanceToGo() != 0) motorZ.run();
  camadaAtual++;
  Serial.println(" Posicionado.");
  delay(100);
}