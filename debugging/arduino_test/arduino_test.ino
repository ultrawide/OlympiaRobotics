

// DEBUG
#define DEBUG 1 // set DEBUG 0 to turn off print statements

// Car Counting US Sensor PINS
int ECHOPIN = 2;
int TRIGPIN = 3;

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

// IR Sensor Variables
int isEmergency = 0;

void setup() {
  if (DEBUG == 1)
  {
    Serial.begin(9600); // start serial for output
  }
  
  /// ULTRASOUND SETUP ///
  pinMode(TRIGPIN, OUTPUT); // Sets the trigPin as an output
  pinMode(ECHOPIN, INPUT);  // Sets the echoPin as an input
  Serial.println("Car Count Ready!");
}


void loop() {
  curTime = millis();
  
  if (curTime >= irTime){
    IR_Detector();
    irTime = millis() + 300;
  }

  curTime = millis();
  if (curTime >= carCountTime){
    Car_Count();
    carCountTime = millis() + 3000;  
  }
}
void Car_Count()
{
  cli(); // disables interrupts
  digitalWrite(TRIGPIN, LOW);
  delayMicroseconds(2);
 
  digitalWrite(TRIGPIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIGPIN, LOW);

  // Reads the echoPin, returns the sound wave travel time in microseconds
  duration = pulseIn(ECHOPIN, HIGH);
  sei(); // enables interrupts

  // Calculating the distance
  distance = duration*0.034/2;
  
  if (distance <= 150 && distance >= 0 && enableCount)
  {
    enableCount = false;
    carCount += 1;
  }
  else if (distance > 150)
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

void IR_Detector()
{
  if (digitalRead(12) == 0) {
    isEmergency = 1;
  }

  if (DEBUG == 1) {
    if (isEmergency == 1) {
      Serial.println("Approaching");
    }
    else {
      Serial.println("Not");
    }
  }  
}
/*
#define NUM_READINGS 5
#define ABOVE_THRESHHOLD 1
#define BELOW_THRESHHOLD 0
#define DISTANCE_THRESHHOLD 150
int distanceFlag = BELOW_THRESHHOLD;

// This function tries to reduce false noisy readings by
// making NUM_READINGS additional readings to confirm it
int confirmReading(int currentReading, int* distanceFlag)
{
	int distance = 0;
	int duration = 0;

	if (distanceFlag == ABOVE_THRESHOLD && currentReading > DISTANCE_THRESHHOLD)
		return 0;

	if (distanceFlag == BELOW_THRESHHOLD && currentReading < DISTANCE_THRESHHOLD)
		return 0;

	cli(); // disables interrupts

	for (int i = 0; i < NUM_READINGS; i++)
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
		
		if (distanceFlag == ABOVE_THRESHHOLD && distance > DISTANCE_THRESHHOLD)
			return 0;
		
		if (distanceFlag == BELOW_THRESHHOLD && distance < DISTANCE_THRESHHOLD)
			return 0;
	}

	sei(); // enables interrupts
	
	if (distanceFlag == ABOVE_THRESHHOLD)
		*distanceFlag = BELOW_THRESHHOLD;
	else
		*distanceFlag = ABOVE_THRESHHOLD;

	return 1;
}

*/
