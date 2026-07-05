#include <Adafruit_NeoPixel.h>

// Declaramos que cada tira física tiene exactamente 3 LEDs independientes
#define LEDS_POR_TIRA 3

// Configuración de los pines digitales limpios y estables de tu proyecto
#define TIRA1 4   // Tira 1 (D2)
#define TIRA2 19  // Tira 2 (D19)
#define TIRA3 5   // Tira 3 (D5)
#define TIRA4 18  // Tira 4 (D18) -> Nueva tira añadida

// Inicialización de las 4 tiras NeoPixel
Adafruit_NeoPixel tira1 = Adafruit_NeoPixel(LEDS_POR_TIRA, TIRA1, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel tira2 = Adafruit_NeoPixel(LEDS_POR_TIRA, TIRA2, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel tira3 = Adafruit_NeoPixel(LEDS_POR_TIRA, TIRA3, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel tira4 = Adafruit_NeoPixel(LEDS_POR_TIRA, TIRA4, NEO_GRB + NEO_KHZ800);

void setup() {
  Serial.begin(115200);
  Serial.println("--- INICIANDO ---");

  tira1.begin(); tira1.setBrightness(80);
  tira2.begin(); tira2.setBrightness(80);
  tira3.begin(); tira3.setBrightness(80);
  tira4.begin(); tira4.setBrightness(80); // Brillo de la cuarta tira configurado

  // Forzamos un apagado inicial completo al arrancar por seguridad
  apagarTodosLosLeds();
  Serial.println("[OK] 4 Tiras inicializadas.");
  delay(1000);
}

void loop() {

  Serial.println("\n>>> TRISTEZA ");
  cambiarColorTiras(255, 110, 20);
  esperarSegundos(5);

  //  Verde Menta Suave 
  Serial.println("\n>>> Mostrando: ALEGRIA (Verde Menta Suave)");
  cambiarColorTiras(70, 255, 70);
  esperarSegundos(5);

  // Violeta Lavanda Relajante
  Serial.println("\n>>> Mostrando: ENFADO (Violeta Lavanda Relajante)");
  cambiarColorTiras(50, 40, 255);
  esperarSegundos(5);

  Serial.println("\n>>> Mostrando: APAGADO NEUTRAL (Espera)");
  apagarTodosLosLeds();
  esperarSegundos(3);
}

void cambiarColorTiras(uint8_t r, uint8_t g, uint8_t b) {
  for (int i = 0; i < LEDS_POR_TIRA; i++) {
    tira1.setPixelColor(i, tira1.Color(r, g, b));
    tira2.setPixelColor(i, tira2.Color(r, g, b));
    tira3.setPixelColor(i, tira3.Color(r, g, b));
    tira4.setPixelColor(i, tira4.Color(r, g, b)); 
  }
  tira1.show();
  tira2.show();
  tira3.show();
  tira4.show();
}

// Función auxiliar para apagar todas las luces
void apagarTodosLosLeds() {
  for (int i = 0; i < LEDS_POR_TIRA; i++) {
    tira1.setPixelColor(i, tira1.Color(0, 0, 0));
    tira2.setPixelColor(i, tira2.Color(0, 0, 0));
    tira3.setPixelColor(i, tira3.Color(0, 0, 0));
    tira4.setPixelColor(i, tira4.Color(0, 0, 0)); 
  }
  tira1.show();
  tira2.show();
  tira3.show();
  tira4.show();
}

void esperarSegundos(int segundos) {
  for (int i = 1; i <= segundos; i++) {
    delay(1000);
    Serial.print("Tiempo expuesto: ");
    Serial.print(i);
    Serial.println("s");
  }
}
