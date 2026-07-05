const int pinSensor = 2; 

const int umbralFuerza = 50; //ruido
void setup() {
  Serial.begin(115200);
  delay(3000);   
  pinMode(pinSensor, INPUT);
}
void loop() {
  int fuerza = analogRead(pinSensor);   
  if (fuerza > umbralFuerza) {
    Serial.print("Fuerza: ");
    Serial.println(fuerza);
  } else {
    Serial.println("Esperando...");
  }  
  delay(300); 
}  
