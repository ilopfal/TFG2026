#include <Adafruit_NeoPixel.h>

#define PIN_DATOS 4

#define NUM_LUCES 3 

// Configuramos la tira LED
Adafruit_NeoPixel tira = Adafruit_NeoPixel(NUM_LUCES, PIN_DATOS, NEO_GRB + NEO_KHZ800);

void setup() {
  tira.begin();          
  tira.show();            
  tira.setBrightness(50); 
}

void loop() {

  for(int i = 0; i < NUM_LUCES; i++) {
    tira.setPixelColor(i, tira.Color(0, 150, 255)); 
    tira.show(); 
    delay(150);  
  }

  delay(1000); 

  for(int i = 0; i < NUM_LUCES; i++) {
    tira.setPixelColor(i, tira.Color(0, 0, 0));
    tira.show();
    delay(150);
  }

  delay(1000); 
}  
