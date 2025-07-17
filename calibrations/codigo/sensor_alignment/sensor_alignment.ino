#include <WiFiS3.h>
#include <AccelStepper.h>
#include <Adafruit_VL53L0X.h>
#include <math.h>

// --- CONFIGURAÇÕES ---
const char ssid[] = "Vodafone-D433A6"; // Mude para a sua rede
const char pass[] = "datreta12345."; // Mude para a sua password
const char server[] = "192.168.20.73";  // Mude para o IP do seu PC
const int port = 5000;

#define TIPO_MOTOR AccelStepper::HALF4WIRE
const int PINO_MOTOR_PRATO_IN1 = 2, PINO_MOTOR_PRATO_IN2 = 3, PINO_MOTOR_PRATO_IN3 = 4, PINO_MOTOR_PRATO_IN4 = 5;
const long PASSOS_POR_ROTACAO_PRATO = 4174;

// --- OBJETOS ---
WiFiClient client;
AccelStepper motorPrato(TIPO_MOTOR, PINO_MOTOR_PRATO_IN1, PINO_MOTOR_PRATO_IN3, PINO_MOTOR_PRATO_IN2, PINO_MOTOR_PRATO_IN4);
Adafruit_VL53L0X lox = Adafruit_VL53L0X();

void setup() {
  Serial.begin(115200);
  while (!Serial);

  Serial.println("--- Modo de Calibração de Alinhamento do Sensor ---");
  
  int status = WL_IDLE_STATUS;
  Serial.print("Conectando a rede...");
  while (status != WL_CONNECTED) { status = WiFi.begin(ssid, pass); delay(5000); Serial.print("."); }
  Serial.println(" OK!");

  Serial.print("Inicializando sensor...");
  if (!lox.begin()) { Serial.println(" Falha."); while (1); }
  Serial.println(" OK.");

  motorPrato.setMaxSpeed(400);
  motorPrato.setAcceleration(200);
  motorPrato.setCurrentPosition(0);

  Serial.print("Conectando ao servidor...");
  if (!client.connect(server, port)) { Serial.println(" Falha."); while(1); }
  Serial.println(" Conectado!");
  
  delay(1000);

  Serial.println("A fazer uma rotação de 360 graus...");
  
  char dataBuffer[50];
  VL53L0X_RangingMeasurementData_t measure;

  for (int angulo = 0; angulo < 360; angulo += 1) {
    long posicaoAlvo = round((angulo / 360.0) * PASSOS_POR_ROTACAO_PRATO);
    motorPrato.moveTo(posicaoAlvo);
    while (motorPrato.distanceToGo() != 0) { motorPrato.run(); }
    
    delay(200);
    
    lox.rangingTest(&measure, false);
    
    if (measure.RangeStatus != 4 && measure.RangeMilliMeter < 200) {
      sprintf(dataBuffer, "Dist:%d,Theta:%d", measure.RangeMilliMeter, angulo);
      client.println(dataBuffer);
    }
  }

  Serial.println("\n--- Scan de alinhamento concluído. ---");
  client.println("END");
  client.stop();
  motorPrato.disableOutputs();
  while(1);
}

void loop() {}