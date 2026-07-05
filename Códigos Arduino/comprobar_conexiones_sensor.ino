#include <Wire.h>

void setup() {
  Serial.begin(115200);
  delay(3000); 

  Serial.println("\n--- COMPROBANDO CONEXIONES ---");
  Wire.begin(5, 6); 
}

void loop() {
  byte error, address;
  int nDevices = 0;

  Serial.println("Buscando el sensor...");

  for(address = 1; address < 127; address++ ) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();

    if (error == 0) {
      Serial.print(" Sensor encontrado en la dirección: 0x");
      if (address < 16) {
        Serial.print("0");
      }
      Serial.println(address, HEX);
      nDevices++;
    }
  }
  
  if (nDevices == 0) {
    Serial.println("Error: No se encuentra el sensor");
  } else {
    Serial.println("Todo listo");
  }
  
  delay(3000); 
}
