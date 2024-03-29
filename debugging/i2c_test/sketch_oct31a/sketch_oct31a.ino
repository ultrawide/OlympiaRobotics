#include <Wire.h>

#define SLAVE_ADDRESS 0x04
int number = 0;
int state = 0;

// Car counting ultrasound sensor
int ECHOPIN = 7;
int TRIGPIN = 6;
int distance = 0;
int duration = 0;
int carCount = 0;
bool enableCount = false;

void setup() {
  //pinMode(13, OUTPUT);
  Serial.begin(9600); // start serial for output
  // initialize i2c as slave
  Wire.begin(SLAVE_ADDRESS);
  
  // define callbacks for i2c communication
  Wire.onReceive(receiveData);
  Wire.onRequest(sendData);
  
  Serial.println("I2C Ready!");

  /// ULTRASOUND SETUP ///
  pinMode(TRIGPIN, OUTPUT);   // Sets the trigPin as an output
  pinMode(ECHOPIN, INPUT);  // Sets the echoPin as an input
  Serial.println("Car Count Ready!");
}

void loop() {
  //Car_Count();
  //delay(1000);
}

// callback for received data
void receiveData(int byteCount){

  while(Wire.available()) {
    number = Wire.read();
    Serial.print("data received: ");
    Serial.println(number);
    
  }
}

// callback for sending data
void sendData(){
  Wire.write(number);
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
/*
#include <Wire.h>

#define SLAVE_ADDRESS 0x04
int number = 0;
int state = 0;

// Car counting ultrasound sensor
int ECHOPIN = 7;
int TRIGPIN = 6;

int distance = 0;
int duration = 0;
int carCount = 0;
bool enableCount = false;

void setup() {
	Serial.begin(9600); // start serial for output

	/// I2C SETUP ///
	// initialize i2c as slave
	Wire.begin(SLAVE_ADDRESS);

	// define callbacks for i2c communication
	Wire.onReceive(receiveData);
	Wire.onRequest(sendData);
	Serial.println("I2C Ready!");

	/// ULTRASOUND SETUP ///
	pinMode(TRIGPIN, OUTPUT); 	// Sets the trigPin as an output
	pinMode(ECHOPIN, INPUT);	// Sets the echoPin as an input
	Serial.println("Car Count Sensor Ready!");
}

void loop() {
	//Car_Count();
	delay(100);
}

// callback for received data
void receiveData(int byteCount){
	while(Wire.available()) 
	{
		number = Wire.read();
		Serial.print("data received: ");
		Serial.println(number);

    
	}
}

// callback for sending data
void sendData(){
  Wire.write(number);
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
  //Serial.print("Car Count Distance: ");
  //Serial.println(distance);

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
*/
