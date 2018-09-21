// # Editor     : ZRH from DFRobot
// # Date       : 29.08.2014


// # Product name: URM V4.0 ultrasonic sensor
// # Product SKU : SEN0001
// # Version     : 1.0


// # Description:
// # The Sketch for scanning 180 degree area 3-500cm detecting range
// # The sketch for using the URM37 PWM trigger pin mode from DFRobot  
// #   and writes the values to the serialport
// # Connection:
// #       Vcc (Arduino)    -> Pin 1 VCC (URM V4.0)
// #       GND (Arduino)    -> Pin 2 GND (URM V4.0)
// #       Pin 3 (Arduino)  -> Pin 4 ECHO (URM V4.0)
// #       Pin 5 (Arduino)  -> Pin 6 COMP/TRIG (URM V4.0)
// #       Pin A0 (Arduino) -> Pin 7 DAC (URM V4.0)
// # Working Mode: PWM trigger pin  mode.
#include <Wire.h>

// Ultrasound Sensor 1
#define  Measure  1     //Mode select
int URECHO = 10; //3         // PWM Output 0-25000US,Every 50US represent 1cm
int URTRIG = 11; //5        // PWM trigger pin
int sensorPin = A0;     // select the input pin for the potentiometer
int sensorValue = 0;    // variable to store the value coming from the sensor

// Ultrasound Sensor 2
int COUNTTRIG = 13;
int COUNTECHO = 12;


unsigned int distanceMeasured = 0;
unsigned int carcount_distance = 0;
unsigned int carcount_duration = 0;
unsigned int carCount = 0;
bool enableCount = false;
int carInProximity = 0;

//i2C
#define SLAVE_ADDRESS 0x06
uint8_t cmd = 0;



void setup() 
{
  //Serial initialization
  Serial.begin(9600);                        // Sets the baud rate to 9600
  pinMode(URTRIG,OUTPUT);                    // A low pull on pin COMP/TRIG
  digitalWrite(URTRIG,HIGH);                 // Set to HIGH 
  pinMode(URECHO, INPUT);                    // Sending Enable PWM mode command
  delay(500);
  Serial.println("Init the sensor 1");
  
  pinMode(COUNTTRIG, OUTPUT); // Sets the trigPin as an output
  pinMode(COUNTECHO, INPUT);  // Sets the echoPin as an input
  
  // Init I2C
  Wire.begin(SLAVE_ADDRESS);
  Wire.onReceive(receiveData);
  Wire.onRequest(sendData);
  Serial.println("Ready!");  
}

void loop()
{
  PWM_Mode(); // Car Proximity
  Car_Count();
  delay(1000);
} 

// Car Count 
void Car_Count()
{
  digitalWrite(COUNTTRIG, LOW);
  delayMicroseconds(2);
 
  digitalWrite(COUNTTRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(COUNTTRIG, LOW);
 
  // Reads the echoPin, returns the sound wave travel time in
  // microseconds
  carcount_duration = pulseIn(COUNTECHO, HIGH);
  
  // Calculating the distance
  carcount_distance = carcount_duration*0.034/2;

  //Prints the distance on the serial Monitor
  Serial.print("Car Count Distance: ");
  Serial.println(carcount_distance);
  
  if (carcount_distance <= 150 && enableCount)
  {
    enableCount = false;
    carCount += 1;
    Serial.print("Car count: ");
    Serial.println(carCount); 
  }
  else if (carcount_distance > 150)
  {
    enableCount = true; 
  }
}

// Car Detection Logic Goes Here
void PWM_Mode()                              // a low pull on pin COMP/TRIG  triggering a sensor reading
{ 
  Serial.print("Distance Measured=");
  digitalWrite(URTRIG, LOW);
  digitalWrite(URTRIG, HIGH);               // reading Pin PWM will output pulses  
  
  unsigned long LowLevelTime = pulseIn(URECHO, LOW) ;
  distanceMeasured = LowLevelTime /50;   // every 50us low level stands for 1cm
  Serial.println(distanceMeasured);

  // pseudo code for car detection
  if (distanceMeasured <= 1000)
    carInProximity = 1;
  else
    carInProximity = 0;

  if (carInProximity)
    Serial.println("Object detected");
  else
    Serial.println("No object detected");
}

void receiveData(int byteCount)
{
  while(Wire.available())
  {
    cmd = Wire.read();
    Serial.print("data received: ");
    Serial.println(cmd);
    
    if (cmd == 1) // testing command to increment count
    {
      carCount++;
    }
    else if (cmd == 2) // testing command to decrement count
    {
      carCount--;
    }
    else if (cmd == 3) // command to clear count
    {
      carCount = 0;
    }
    else if (cmd == 4)
    {
      //carCount = carCount;
      //Serial.print("received get car count");
      // return count without changing it
    }
  }
}

void sendData()
{
  Wire.write(carCount);
  Serial.print("data sent: ");
  Serial.println(carCount);
}
