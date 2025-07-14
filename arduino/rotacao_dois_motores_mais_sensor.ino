/*
 * CÓDIGO DE TESTE - ROTAÇÃO PRECISA DO PRATO
 * 
 * Objetivo: Isolar e testar a lógica de rotação do prato giratório
 * usando posições absolutas (moveTo) e rotação contínua.
 * 
 * O que faz:
 * 1. Gira 360 graus em incrementos de 5 graus.
 * 2. Gira mais 360 graus na mesma direção para testar o 'offset'.
 * 3. Volta à posição inicial.
 * 4. Repete.
 */

#include <AccelStepper.h>
#include <math.h> // Para a função round()

// --- CONFIGURAÇÕES DO MOTOR DO PRATO ---
#define TIPO_MOTOR AccelStepper::HALF4WIRE
const int PINO_MOTOR_PRATO_IN1 = 2;
const int PINO_MOTOR_PRATO_IN2 = 3;
const int PINO_MOTOR_PRATO_IN3 = 4;
const int PINO_MOTOR_PRATO_IN4 = 5;

// IMPORTANTE: Ajuste este valor se o seu motor for diferente.
// 4096 é o valor típico para o motor 28BYJ-48 em modo de meio passo.
const long PASSOS_POR_ROTACAO_PRATO = 4096;

// --- INICIALIZAÇÃO DO MOTOR ---
AccelStepper motorPrato(TIPO_MOTOR, PINO_MOTOR_PRATO_IN1, PINO_MOTOR_PRATO_IN3, PINO_MOTOR_PRATO_IN2, PINO_MOTOR_PRATO_IN4);

void setup() {
  Serial.begin(115200);
  while (!Serial);
  Serial.println("--- Teste de Rotação Precisa do Prato ---");

  // --- CONFIGURAÇÃO DO MOTOR ---
  motorPrato.setMaxSpeed(800);      // Velocidade máxima de rotação
  motorPrato.setAcceleration(400);  // Aceleração para um início/fim suave
  motorPrato.setCurrentPosition(0); // Define a posição atual como o ponto zero
  
  Serial.print("Motor configurado. Passos por rotação: ");
  Serial.println(PASSOS_POR_ROTACAO_PRATO);
  Serial.println("O teste começará em 5 segundos...");
  delay(5000);
}

void loop() {
  // --- TESTE 1: PRIMEIRA ROTAÇÃO (0 a 360 graus) ---
  Serial.println("\n--- INICIANDO ROTAÇÃO 1 (0 -> 360 graus) ---");
  delay(1000);

  // O loop vai de 5 em 5 graus. Começa em 5 para o primeiro movimento.
  for (int angulo = 5; angulo <= 360; angulo += 5) {
    // Calcula a posição de destino ABSOLUTA para o ângulo atual
    long posicaoAlvo = round((angulo / 360.0) * PASSOS_POR_ROTACAO_PRATO);

    Serial.print("Movendo para o ângulo: ");
    Serial.print(angulo);
    Serial.print(" graus. Posição alvo (passos): ");
    Serial.println(posicaoAlvo);

    motorPrato.moveTo(posicaoAlvo);
    
    // Este loop while é bloqueante, mas é perfeito para um teste simples.
    // Ele garante que um movimento termina antes do próximo começar.
    while (motorPrato.distanceToGo() != 0) {
      motorPrato.run();
    }
    delay(200); // Pequena pausa para observar a posição
  }

  Serial.println("--- ROTAÇÃO 1 COMPLETA ---");
  delay(3000); // Pausa de 3 segundos


  // --- TESTE 2: SEGUNDA ROTAÇÃO CONTÍNUA (360 a 720 graus) ---
  Serial.println("\n--- INICIANDO ROTAÇÃO 2 (contínua) ---");
  delay(1000);

  for (int angulo = 365; angulo <= 720; angulo += 5) {
    // O cálculo é o mesmo, mas o motor continuará a girar para a frente
    // porque a posição alvo é sempre crescente.
    long posicaoAlvo = round((angulo / 360.0) * PASSOS_POR_ROTACAO_PRATO);
    
    Serial.print("Movendo para o ângulo virtual: ");
    Serial.print(angulo);
    Serial.print(" graus. Posição alvo (passos): ");
    Serial.println(posicaoAlvo);

    motorPrato.moveTo(posicaoAlvo);
    while (motorPrato.distanceToGo() != 0) {
      motorPrato.run();
    }
    delay(200);
  }

  Serial.println("--- ROTAÇÃO 2 COMPLETA ---");
  delay(3000); // Pausa de 3 segundos


  // --- TESTE 3: RETORNAR AO PONTO ZERO ---
  Serial.println("\n--- INICIANDO RETORNO À POSIÇÃO ZERO ---");
  delay(1000);

  motorPrato.moveTo(0);
  while (motorPrato.distanceToGo() != 0) {
    motorPrato.run();
  }

  Serial.println("--- POSIÇÃO ZERO ATINGIDA ---");
  Serial.println("O ciclo de teste irá recomeçar em 10 segundos...");
  delay(10000); // Pausa longa antes de repetir o teste
}