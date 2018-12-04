#include <gamma.h>
#include <RGBmatrixPanel.h> 
#include <Wire.h>

// DEBUG
#define DEBUG 0// set DEBUG 0 to turn off print statements
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

// ARDUINO COMMANDS RECEIVED FROM THE RASPBERRY PI OVER i2C
int RECEIVED_CMD = 0;

// COMMANDS THAT THE ARDUINO WILL INTERPRET
#define RESET_CAR_COUNT 1
#define WRITE_CAR_COUNT 2
#define RESET_EMERGENCY_FLAG 7
#define WRITE_EMERGENCY_FLAG 9
#define DISPLAY_STOP 8
#define DISPLAY_EMERGENCY_VEHICLES_ONLY 4
#define DISPLAY_PROBLEM 5
#define DISPLAY_PROCEED_SLOWLY 6

RGBmatrixPanel matrix(A, B, C, D, CLK, LAT, OE, false, 64);

// Car Counting US Sensor PINS
int ECHOPIN = 9;
int TRIGPIN = 10;

// CarCount Variables
int distance = 0;
int duration = 0;
int carCount = 0;
bool enableCount = false;

// Determines the frequency of function calls in the main loop
int curTime = 0;
int carCountTime = 0;
int irTime = 0;

// IR SENSOR PINS
int RECVPIN = 12;
int LEDPIN = 3;

// IR Sensor Variables
int isEmergencyFlag = 0;
#define NUM_READINGS_IR 8
int irReadings[NUM_READINGS_IR] = {-1, -1, -1, -1, -1, -1, -1, -1};
int irReadingsIndex = 0;

//Disabling Interrupts 
int A_TO_P = 7; // This connects to 35 Arduino to Pi (output)
int P_TO_A = 8; //This connects to 37 Pi to Arduino (input)

void setup() {
  if (DEBUG == 1)
  {
    Serial.begin(9600); // start serial for output
  }
  
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

  /// LED DISPLAY ///
  matrix.begin();
  matrix.fillScreen(matrix.Color333(0, 0, 0));

  // draw some text!
  matrix.setTextSize(2);     // size 1 == 8 pixels high
  matrix.setTextWrap(true); 

  matrix.setCursor(8, 0); // start at top left, with 8 pixel of spacing

  // Disabling Interrupts //
  pinMode(P_TO_A, INPUT);      
  pinMode(A_TO_P, OUTPUT); 
}

void loop() {
  curTime = millis();
  if (curTime >= irTime){
    IR_Detector();
    irTime = millis() + 200;
  }

  curTime = millis();
  if (curTime >= carCountTime){
    Car_Count();
    carCountTime = millis() + 100;  
  }
}

// callback for received data from i2c data wire
void receiveData(int byteCount){
  while(Wire.available()) {
    RECEIVED_CMD = Wire.read();
    
    if (DEBUG == 1) {
      Serial.print("data received: ");
      Serial.println(RECEIVED_CMD);
    }
    
    switch (RECEIVED_CMD)
    {
      case DISPLAY_STOP: // STOP
        matrix.setTextSize(2); 
        matrix.fillScreen(matrix.Color333(0, 0, 0));
        matrix.setCursor(4, 8);
        matrix.setTextColor(matrix.Color333(7,0,0));
        matrix.print("Stop!");
        break;
      case DISPLAY_EMERGENCY_VEHICLES_ONLY: // Emergency Vehicles only
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
      case DISPLAY_PROBLEM: // Stop there is a problem
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
      case DISPLAY_PROCEED_SLOWLY: // Proceed slowly.    
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

// callback for sending data to the raspberry pi
void sendData(){
  if (RECEIVED_CMD == RESET_CAR_COUNT)
  {
    carCount = 0;
  }
  else if (RECEIVED_CMD == WRITE_CAR_COUNT)
  {
    Wire.write(carCount);
  }
  else if (RECEIVED_CMD == RESET_EMERGENCY_FLAG)
  {
    isEmergencyFlag = 0;
  }
  else if (RECEIVED_CMD == WRITE_EMERGENCY_FLAG)
  {
    Wire.write(isEmergencyFlag);
  }
}

#define NUM_PREV_READINGS 3
int distances[NUM_PREV_READINGS] = {0, 0, 0};
int distancesIndex = 0;

void Car_Count()
{
  while (digitalRead(P_TO_A) == HIGH)
  {
    Serial.println("Pi telling me to not disable interrupts");
    //Don't disable interrupts
    
  }
  digitalWrite(A_TO_P, HIGH);
  
  cli(); // disables interrupts
  Serial.println("Disabled Interrupts");
  
  digitalWrite(TRIGPIN, LOW);
  delayMicroseconds(2);
 
  digitalWrite(TRIGPIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIGPIN, LOW);

  // Reads the echoPin, returns the sound wave travel time in microseconds
  duration = pulseIn(ECHOPIN, HIGH);
  sei(); // enables interrupts
  digitalWrite(A_TO_P,LOW);
  Serial.println("Enabled Interrupts");

  // Calculating the distance
  distance = duration*0.034/2;
  distances[distancesIndex % NUM_PREV_READINGS] = distance;
  distancesIndex = (distancesIndex + 1) % NUM_PREV_READINGS;
  if (distances[(distancesIndex-1)%NUM_PREV_READINGS] <= 150 && 
      distances[(distancesIndex-2)%NUM_PREV_READINGS] <= 150 &&
      distance <= 150 &&
      distance >= 0 && enableCount)
  {
    enableCount = false;
    carCount += 1;
  }
  else if (distances[(distancesIndex-1)%NUM_PREV_READINGS] > 150 && 
           distances[(distancesIndex-2)%NUM_PREV_READINGS] > 150 &&
           distance > 150)
  {
    enableCount = true; 
  }
  
    //Prints the distance on the serial Monitor
  if (DEBUG == 1) {
    Serial.print("Distance: ");
    Serial.println(distance);
    Serial.print("Car count: ");
    Serial.println(carCount); 
  }
}

_Bool isEmergency(int* irReadings)
{
  int numZeroes = 0;
  for (int i = 0; i < NUM_READINGS_IR; i++)
  {
    if (irReadings[i] == 0)
      numZeroes++;
  }

  if (numZeroes >= 2)
    return true;
  else
    return false;
}

void IR_Detector()
{
  irReadings[irReadingsIndex] = digitalRead(RECVPIN);
  Serial.println("Current IR reading");
  Serial.println(irReadings[irReadingsIndex]);
  irReadingsIndex = (irReadingsIndex+1) % NUM_READINGS_IR;

  Serial.println("Index");
  Serial.println(irReadingsIndex);

  if (DEBUG == 1) {
    Serial.println("IR Readings:");
    Serial.println(irReadings[0]);
    Serial.println(irReadings[1]);
    Serial.println(irReadings[2]);
    Serial.println(irReadings[3]);
    Serial.println(irReadings[4]);
    Serial.println(irReadings[5]);
    Serial.println(irReadings[6]);
    Serial.println(irReadings[7]);
  }
  
  if (isEmergency(irReadings) == true) {
    isEmergencyFlag = 1;
  }

  if (DEBUG == 1) {
    if (isEmergencyFlag == 1) {
      Serial.println("Approaching");
    }
    else {
      Serial.println("Not");
    }
  }  
}
