#include <Adafruit_NeoPixel.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

#define LEDS_POR_TIRA 3 
Adafruit_NeoPixel tira1 = Adafruit_NeoPixel(LEDS_POR_TIRA, 4,  NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel tira2 = Adafruit_NeoPixel(LEDS_POR_TIRA, 19, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel tira3 = Adafruit_NeoPixel(LEDS_POR_TIRA, 2,  NEO_GRB + NEO_KHZ800); // Cambiado al pin 2 para evitar choques
Adafruit_NeoPixel tira4 = Adafruit_NeoPixel(LEDS_POR_TIRA, 18, NEO_GRB + NEO_KHZ800);

#define PIN_PRESION_1 32
#define PIN_PRESION_2 33
#define PIN_PRESION_3 34

Adafruit_MPU6050 mpu;

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10); 
  
  Serial.println("   COMPROBACIÓN GLOBAL ");
  
  // 1. Inicializar y configurar el brillo de las 4 tiras de LED
  tira1.begin(); tira1.show(); tira1.setBrightness(40);
  tira2.begin(); tira2.show(); tira2.setBrightness(40);
  tira3.begin(); tira3.show(); tira3.setBrightness(40);
  tira4.begin(); tira4.show(); tira4.setBrightness(40);
  Serial.println("-> Configurando 4 luces... Verificando encendido.");

  Wire.begin(5, 6); 

  // 2. Inicializar la IMU de movimiento
  if (!mpu.begin()) {
    Serial.println("no se encuentra la imu");
  } else {
    Serial.println("IMU MPU6050: Detectada correctamente.");
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    mpu.setGyroRange(MPU6050_RANGE_500_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  }
  Serial.println("---------------------------------------------\n");
}

void loop() {
  int presion1 = analogRead(PIN_PRESION_1);
  int presion2 = analogRead(PIN_PRESION_2);
  int presion3 = analogRead(PIN_PRESION_3);
  
  sensors_event_t acc, gyro, temp;
  mpu.getEvent(&acc, &gyro, &temp);

  Serial.print("PRESIONES -> P1 (D32): "); Serial.print(presion1);
  Serial.print(" | P2 (D33): "); Serial.print(presion2);
  Serial.print(" | P3 (D34): "); Serial.print(presion3);
  
  Serial.print("  ||   IMU -> X: "); Serial.print(acc.acceleration.x, 1);
  Serial.print(" Y: "); Serial.print(acc.acceleration.y, 1);
  Serial.print(" Z: "); Serial.println(acc.acceleration.z, 1);

  for(int i = 0; i < LEDS_POR_TIRA; i++) {
    tira1.setPixelColor(i, tira1.Color(0, 150, 255));
    tira2.setPixelColor(i, tira2.Color(0, 150, 255));
    tira3.setPixelColor(i, tira3.Color(0, 150, 255));
    tira4.setPixelColor(i, tira4.Color(0, 150, 255));
  }
  
  tira1.show();
  tira2.show();
  tira3.show();
  tira4.show();
  
  // Esperamos 200 milisegundos antes de volver a leer
  delay(200);
}
