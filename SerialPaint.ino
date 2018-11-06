

#include <gamma.h>


// testshapes demo for RGBmatrixPanel library.
// Demonstrates the drawing abilities of the RGBmatrixPanel library.
// For 32x64 RGB LED matrix.

// WILL NOT FIT on ARDUINO UNO -- requires a Mega, M0 or M4 board

#include <RGBmatrixPanel.h>

// Most of the signal pins are configurable, but the CLK pin has some
// special constraints.  On 8-bit AVR boards it must be on PORTB...
// Pin 8 works on the Arduino Uno & compatibles (e.g. Adafruit Metro),
// Pin 11 works on the Arduino Mega.  On 32-bit SAMD boards it must be
// on the same PORT as the RGB data pins (D2-D7)...
// Pin 8 works on the Adafruit Metro M0 or Arduino Zero,
// Pin A4 works on the Adafruit Metro M4 (if using the Adafruit RGB
// Matrix Shield, cut trace between CLK pads and run a wire to A4).

//#define CLK  8   // USE THIS ON ADAFRUIT METRO M0, etc.
//#define CLK A4 // USE THIS ON METRO M4 (not M0)
#define CLK 11 // USE THIS ON ARDUINO MEGA
#define OE   9
#define LAT 10
#define A   A0
#define B   A1
#define C   A2
#define D   A3

RGBmatrixPanel matrix(A, B, C, D, CLK, LAT, OE, false, 64);

void setup() {

  matrix.begin();
  Serial.begin(9600);
  matrix.fillScreen(matrix.Color333(0, 0, 0));

  // draw some text!
  matrix.setTextSize(2);     // size 1 == 8 pixels high
  matrix.setTextWrap(true); 

  matrix.setCursor(8, 0);    // start at top left, with 8 pixel of spacing
  
}

void loop() {
  if (Serial.available())
  {
    char c = Serial.read();     // Read data into c
    String str;
    switch (c)
    {
      case 'S':
        matrix.setTextSize(2); 
        matrix.fillScreen(matrix.Color333(0, 0, 0));
        matrix.setCursor(4, 8);
        matrix.setTextColor(matrix.Color333(7,0,0));
        matrix.print("Stop!");
        break;
      case 'P':
        matrix.setTextSize(1); 
        matrix.fillScreen(matrix.Color333(0, 0, 0));
        matrix.setCursor(6, 6);
        matrix.setTextColor(matrix.Color333(7,1,0));
        matrix.print("Proceed");
        matrix.setCursor(20, 16);
        matrix.print("Slowly");
        break;
      case 'E':
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
      case 'M':
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
    }
}}
