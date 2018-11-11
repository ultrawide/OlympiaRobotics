// Refer to readme.txt to install library depedencies

#include <gamma.h>
#include <RGBmatrixPanel.h>
#include <IRremote.h> 
#include <Wire.h>

// I2C 
#define SLAVE_ADDRESS 0x04

// LED DISPLAY
#define CLK 11 // USE THIS ON ARDUINO MEGA
#define OE   9
#define LAT 10
#define A   A0
#define B   A1
#define C   A2
#define D   A3

RGBmatrixPanel matrix(A, B, C, D, CLK, LAT, OE, false, 64);

// Car Counting US Sensor PINS
int ECHOPIN = 7;
int TRIGPIN = 6;

// CarCount Variables
int number = 0;
int distance = 0;
int duration = 0;
int carCount = 0;
bool enableCount = false;

// IR SENSOR PINS
int RECVPIN = 12;
int LEDPIN = 3;

// IR Sensor Variables
IRrecv irrecv(RECVPIN);
decode_results results;
bool isEmergency = false;

void setup() {
  Serial.begin(9600); // start serial for output
  // initialize i2c as slave
  Wire.begin(SLAVE_ADDRESS);
  
  // define callbacks for i2c communication
  Wire.onReceive(receiveData);
  Wire.onRequest(sendData);
  
  Serial.println("I2C Ready!");

  /// ULTRASOUND SETUP ///
  pinMode(TRIGPIN, OUTPUT); // Sets the trigPin as an output
  pinMode(ECHOPIN, INPUT);  // Sets the echoPin as an input
  Serial.println("Car Count Ready!");

  /// IR SENSOR SETUP ///
  irrecv.enableIRIn(); // Start the receiver
  Serial.println("Enabled IRin");

  /// LED DISPLAY ///
  matrix.begin();
  matrix.fillScreen(matrix.Color333(0, 0, 0));

  // draw some text!
  matrix.setTextSize(2);     // size 1 == 8 pixels high
  matrix.setTextWrap(true); 

  matrix.setCursor(8, 0); // start at top left, with 8 pixel of spacing
}

void loop() {
  //LED_Display();
  IR_Detector();
  Car_Count();
  delay(1000);
}

// callback for received data
void receiveData(int byteCount){
  while(Wire.available()) {
    number = Wire.read();
    Serial.print("data received: ");
    Serial.println(number);
    switch (number)
    {
      case 8: // STOP
        matrix.setTextSize(2); 
        matrix.fillScreen(matrix.Color333(0, 0, 0));
        matrix.setCursor(4, 8);
        matrix.setTextColor(matrix.Color333(7,0,0));
        matrix.print("Stop!");
        break;
      case 4: // Emergency Vehicles only
        matrix.setTextSize(1); 
        matrix.fillScreen(matrix.Color333(0, 0, 0));
        matrix.setCursor(5, 3);
        matrix.setTextColor(matrix.Color333(7,7,0));
        matrix.print("Emergency");
        matrix.setCursor(9, 13);
        matrix.print("Vehicles");
        matrix.setCursor(19, 22);
        matrix.print("Only");
        break;
      case 5: // Stop there is a problem
        matrix.setTextSize(1); 
        matrix.fillScreen(matrix.Color333(0, 0, 0));
        matrix.setCursor(2, 0);
        matrix.setTextColor(matrix.Color333(7,0,0));
        matrix.print("Stop!");
        //matrix.setCursor(0, 9);
        matrix.setTextColor(matrix.Color333(7,7,0));
        matrix.print("There");
        matrix.setCursor(0, 8);
        matrix.print("is");
        matrix.setCursor(14, 8);
        matrix.print("a");
        matrix.setCursor(22, 8);
        matrix.print("problem");
        matrix.setCursor(5, 16);
        matrix.print("please be");
        matrix.setCursor(12, 24);
        matrix.print("patient");
        break;
      case 6: // Proceed slowly
        matrix.setTextSize(1); 
        matrix.fillScreen(matrix.Color333(0, 0, 0));
        matrix.setCursor(6, 6);
        matrix.setTextColor(matrix.Color333(7,1,0));
        matrix.print("Proceed");
        matrix.setCursor(20, 16);
        matrix.print("Slowly");
        break;
    }
  }
}

// callback for sending data
void sendData(){
  if (number == 1)
  {
    carCount = 0;
  }
  else if (number == 2)
  {
    Wire.write(carCount);
  }
  else if (number == 6)
  {
    matrix.setTextSize(1); 
    matrix.fillScreen(matrix.Color333(0, 0, 0));
    matrix.setCursor(6, 6);
    matrix.setTextColor(matrix.Color333(7,1,0));
    matrix.print("Proceed");
    matrix.setCursor(20, 16);
    matrix.print("Slowly");
  }
  else if (number == 7)
  {
    isEmergency = false;
  }
}

// Car Count 
void Car_Count()
{
  digitalWrite(TRIGPIN, LOW);
  delayMicroseconds(2);
 
  digitalWrite(TRIGPIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIGPIN, LOW);
 
  // Reads the echoPin, returns the sound wave travel time in
  // microseconds
  duration = pulseIn(ECHOPIN, HIGH);

  // Calculating the distance
  distance = duration*0.034/2;

  //Prints the distance on the serial Monitor
  Serial.print("Car Count Distance: ");
  Serial.println(distance);

  if (distance <= 150 && enableCount)
  {
    enableCount = false;
    carCount += 1;
    Serial.print("Car count: ");
    Serial.println(carCount); 
  }
  else if (distance > 150)
  {
    enableCount = true; 
  }
}

// Do we want an LED to light up instead?
void IR_Detector()
{
  if (irrecv.decode(&results)) {
    Serial.println(results.value, HEX);
    isEmergency = true;
    irrecv.resume();
  }
}
