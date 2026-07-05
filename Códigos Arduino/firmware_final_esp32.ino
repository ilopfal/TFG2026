#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <Adafruit_NeoPixel.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

#define LEDS_POR_TIRA 3
Adafruit_NeoPixel tira1 = Adafruit_NeoPixel(LEDS_POR_TIRA, 4,  NEO_GRB + NEO_KHZ800); 
Adafruit_NeoPixel tira2 = Adafruit_NeoPixel(LEDS_POR_TIRA, 19, NEO_GRB + NEO_KHZ800); 
Adafruit_NeoPixel tira3 = Adafruit_NeoPixel(LEDS_POR_TIRA, 12, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel tira4 = Adafruit_NeoPixel(LEDS_POR_TIRA, 14, NEO_GRB + NEO_KHZ800);

#define PIN_PRESION_1 32
#define PIN_PRESION_2 33
#define PIN_PRESION_3 34

Adafruit_MPU6050 mpu;

int offsetP1 = 0, offsetP2 = 0, offsetP3 = 0; 
volatile bool dispositivoConectado = false; 
bool antiguoDispositivoConectado = false;

#define SERVICE_UUID           "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_LUCES   "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define CHARACTERISTIC_PRESION "d27038e2-6302-421b-851f-506e7a27572d"
#define CHARACTERISTIC_IMU     "cba1d466-344c-4be3-ab3f-189f80dd7518"

BLECharacteristic *pPresionChar;
BLECharacteristic *pImuChar;
BLEServer *pServer = NULL;

void apagarLuces() {
  for(int i = 0; i < LEDS_POR_TIRA; i++) {
    tira1.setPixelColor(i, tira1.Color(0, 0, 0)); 
    tira2.setPixelColor(i, tira2.Color(0, 0, 0)); 
    tira3.setPixelColor(i, tira3.Color(0, 0, 0)); 
    tira4.setPixelColor(i, tira4.Color(0, 0, 0));
  }
  tira1.show(); tira2.show(); tira3.show(); tira4.show();
}

class ConectividadCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
      dispositivoConectado = true;
      Serial.println("\nConexion establecida con Python");
    }
    
    void onDisconnect(BLEServer* pServer) {
      dispositivoConectado = false;
      Serial.println("\nAlerta: Enlace cortado o finalizado.");
      apagarLuces();
      delay(200); 
      pServer->getAdvertising()->start(); 
      Serial.println("Peluche visible.");
    }
};

class LucesCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
      String value = pCharacteristic->getValue();
      if (value.length() > 0) {
        char orden = value[0];
        Serial.print("Comando de visualizacion recibido: ");
        Serial.println(orden);

        if (orden == '1') { // TRISTEZA 
          for(int i = 0; i < LEDS_POR_TIRA; i++) {
            tira1.setPixelColor(i, tira1.Color(255, 110, 20)); 
            tira2.setPixelColor(i, tira2.Color(255, 110, 20)); 
            tira3.setPixelColor(i, tira3.Color(255, 110, 20)); 
            tira4.setPixelColor(i, tira4.Color(255, 110, 20));
          }
          tira1.show(); tira2.show(); tira3.show(); tira4.show();
        } 
        else if (orden == '2') { // ALEGRÍA 
          for(int i = 0; i < LEDS_POR_TIRA; i++) {
            tira1.setPixelColor(i, tira1.Color(60, 255, 60)); 
            tira2.setPixelColor(i, tira2.Color(60, 255, 60)); 
            tira3.setPixelColor(i, tira3.Color(60, 255, 60)); 
            tira4.setPixelColor(i, tira4.Color(60, 255, 60));
          }
          tira1.show(); tira2.show(); tira3.show(); tira4.show();
        } 
        else if (orden == '4') { // ENFADO
          for(int i = 0; i < LEDS_POR_TIRA; i++) {
            tira1.setPixelColor(i, tira1.Color(50, 40, 255)); 
            tira2.setPixelColor(i, tira2.Color(50, 40, 255)); 
            tira3.setPixelColor(i, tira3.Color(50, 40, 255)); 
            tira4.setPixelColor(i, tira4.Color(50, 40, 255));
          }
          tira1.show(); tira2.show(); tira3.show(); tira4.show();
        }
        else if (orden == '0') { // NEUTRAL 
          apagarLuces();
          Serial.println("Estado Neutral detectado. LEDs apagados por completo.");
        }
      }
    }
};

void setup() {
  Serial.begin(115200);
  delay(1500); 
  
  tira1.begin(); tira1.setBrightness(90);
  tira2.begin(); tira2.setBrightness(90);
  tira3.begin(); tira3.setBrightness(90);
  tira4.begin(); tira4.setBrightness(90); 
  apagarLuces();

  Wire.begin(5, 6); 

  if (!mpu.begin()) {
    Serial.println("[ERROR] MPU6050 inalcanzable.");
    while (1) delay(10);
  }
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);

  Serial.println("\nInicializando tara de 3 sensores...");
  long s1 = 0, s2 = 0, s3 = 0; 
  int muestras = 100; 
  
  for(int i = 0; i < muestras; i++) {
    s1 += analogRead(PIN_PRESION_1); 
    s2 += analogRead(PIN_PRESION_2); 
    s3 += analogRead(PIN_PRESION_3);
    delay(30); 
  }
  offsetP1 = s1 / muestras; 
  offsetP2 = s2 / muestras; 
  offsetP3 = s3 / muestras;
  
  Serial.print(" P1 Zero Offset: "); Serial.print(offsetP1);
  Serial.print(" | P2 Zero Offset: "); Serial.print(offsetP2);
  Serial.print(" | P3 Zero Offset: "); Serial.println(offsetP3);
  Serial.println("[CALIBRACION] Completada. Listo para leer.");

  BLEDevice::init("Peluche_Inteligente");
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new ConectividadCallbacks());

  BLEService *pService = pServer->createService(SERVICE_UUID);
  
  BLECharacteristic *pLucesChar = pService->createCharacteristic(CHARACTERISTIC_LUCES, BLECharacteristic::PROPERTY_WRITE);
  pLucesChar->setCallbacks(new LucesCallbacks());

  pPresionChar = pService->createCharacteristic(CHARACTERISTIC_PRESION, BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);
  pImuChar = pService->createCharacteristic(CHARACTERISTIC_IMU, BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);

  pService->start();
  
  BLEAdvertising *pAdvertising = pServer->getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  pAdvertising->setMinPreferred(0x06);  
  pAdvertising->setMinPreferred(0x12);
  
  pAdvertising->start();
  Serial.println("[BLE] Servidor activo. Esperando Raspberry/PC...");
}

void loop() {
  if (dispositivoConectado) {
    long suma_presion = 0;
    float energia_movimiento_acumulado = 0.0;
    int contador_muestras = 0;
    
    for (int i = 0; i < 20; i++) {
      int p1 = abs(analogRead(PIN_PRESION_1) - offsetP1);
      int p2 = abs(analogRead(PIN_PRESION_2) - offsetP2);
      int p3 = abs(analogRead(PIN_PRESION_3) - offsetP3);
      
      if (p1 < 250) p1 = 0;
      if (p2 < 250) p2 = 0;
      if (p3 < 250) p3 = 0;
      
      suma_presion += (p1 + p2 + p3); 
      
      sensors_event_t a, g, temp;
      mpu.getEvent(&a, &g, &temp);
      
      float acc_total = sqrt(a.acceleration.x * a.acceleration.x + 
                             a.acceleration.y * a.acceleration.y + 
                             a.acceleration.z * a.acceleration.z) * 10.0;
                             
      float movimiento_puro = abs(acc_total - 98.1);
      energia_movimiento_acumulado += movimiento_puro;
      contador_muestras++;
      
      delay(50); 
    }
    
    int promedio_presion = suma_presion / contador_muestras;
    float promedio_movimiento_repetitivo = (energia_movimiento_acumulado / contador_muestras) * 5.0; 
    
    String str_presion = String(promedio_presion);
    String str_imu = String(promedio_movimiento_repetitivo);
    
    pPresionChar->setValue(str_presion.c_str());
    pPresionChar->notify();
    
    pImuChar->setValue(str_imu.c_str());
    pImuChar->notify(); 
  }
  delay(50);
}
