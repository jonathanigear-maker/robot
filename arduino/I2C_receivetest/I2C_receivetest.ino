#define RIGHT_EYE
//#define LEFT_EYE

#define USE_TFT_ESPI_LIBRARY
#include <lv_xiao_round_screen.h>
#include <TFT_eSPI.h>
#include "clockImage.h"
#include "lampImage.h"
#include "greenTick.h"
#include "redCross.h"
#include "laser.h"
#include "scope.h"
#include "eyes.h"
#include "hourGlass1.h"
#include "hourGlass2.h"
#include "hourGlass3.h"
#include "game.h"
#include "robotEyes.h"

#define LIGHT_BLUE 0x66FF
#define VLIGHT_BLUE 0xCF9E  
#define OFF_WHITE 0xDEFB
#define DARK_GRAY 0x7BCF
#define SPRITE_WIDTH 100  // Adjust the sprite size as needed
#define SPRITE_HEIGHT 100
#define rightEye 0x10
#define leftEye 0x09
#define LASER_PIN D0

//TFT_eSPI tft = TFT_eSPI(); // Initialize the TFT display

static boolean eyeInMotion = false;
static int16_t eyeOldX = 120, eyeOldY = 120, eyeNewX = 120, eyeNewY = 120;
static uint32_t eyeMoveStartTime = 0L;
static int32_t eyeMoveDuration = 0L;
static int8_t eyeX = 0;
static int8_t eyeY = 0;
static int8_t eyeMovePeriod = 0;
static int8_t eyePrevX = 0;
static int8_t eyePrevY = 0;
unsigned long previousMillis = 0;
const long interval = 1000;
int color = TFT_BLACK; 
bool eyeOpen = false;
const int debounceDelay = 500;  // Adjust this value as needed
unsigned long lastDebounceTime = 0;

int pupilSize = 28; //Innitial size of pupil

TFT_eSprite eyeSprite = TFT_eSprite(&tft);
TFT_eSprite backFill = TFT_eSprite(&tft);
TFT_eSprite lidSprite = TFT_eSprite(&tft);
TFT_eSprite hourGlassSprite = TFT_eSprite(&tft);
TFT_eSprite robotEyeSprite = TFT_eSprite(&tft);

// Custom ease curve for eye movements
const uint8_t ease[] = { // Ease in/out curve for eye movements 3*t^2-2*t^3
    0,  0,  0,  0,  0,  0,  0,  1,  1,  1,  1,  1,  2,  2,  2,  3,
    3,  3,  4,  4,  4,  5,  5,  6,  6,  7,  7,  8,  9,  9, 10, 10,
    11, 12, 12, 13, 14, 15, 15, 16, 17, 18, 18, 19, 20, 21, 22, 23,
    24, 25, 26, 27, 27, 28, 29, 30, 31, 33, 34, 35, 36, 37, 38, 39,
    40, 41, 42, 44, 45, 46, 47, 48, 50, 51, 52, 53, 54, 56, 57, 58,
    60, 61, 62, 63, 65, 66, 67, 69, 70, 72, 73, 74, 76, 77, 78, 80,
    81, 83, 84, 85, 87, 88, 90, 91, 93, 94, 96, 97, 98,100,101,103,
    104,106,107,109,110,112,113,115,116,118,119,121,122,124,125,127,
    128,130,131,133,134,136,137,139,140,142,143,145,146,148,149,151,
    152,154,155,157,158,159,161,162,164,165,167,168,170,171,172,174,
    175,177,178,179,181,182,183,185,186,188,189,190,192,193,194,195,
    197,198,199,201,202,203,204,205,207,208,209,210,211,213,214,215,
    216,217,218,219,220,221,222,224,225,226,227,228,228,229,230,231,
    232,233,234,235,236,237,237,238,239,240,240,241,242,243,243,244,
    245,245,246,246,247,248,248,249,249,250,250,251,251,251,252,252,
    252,253,253,253,254,254,254,254,254,255,255,255,255,255,255,255
};

void setup() {
  Serial.begin(9600);
  //Wire.stretchClock(false);
  pinMode(TOUCH_INT, INPUT_PULLUP);
  pinMode(LASER_PIN, OUTPUT);
  digitalWrite(LASER_PIN, LOW);
  
  #ifdef RIGHT_EYE
  Wire.begin(rightEye);
  #endif

  #ifdef LEFT_EYE
  Wire.begin(leftEye);
  #endif

  Wire.onRequest(requestEvent);
  Wire.onReceive(receiveEvent);
  tft.init();
  tft.setRotation(0); // Adjust rotation as needed for your display
  tft.setPivot(120, 120);
  tft.fillScreen(TFT_BLACK);
  tft.setTextSize(2);
  tft.setTextColor(TFT_WHITE);

   eyeSprite.createSprite(SPRITE_WIDTH,SPRITE_HEIGHT);
   backFill.createSprite(SPRITE_WIDTH,SPRITE_HEIGHT);
   lidSprite.createSprite(240,240);
   hourGlassSprite.createSprite(150,102);
   hourGlassSprite.setPivot(75, 51);
   tft.fillScreen(OFF_WHITE);
   eyeSprite.fillSprite(OFF_WHITE);
   backFill.fillSprite(OFF_WHITE);
   hourGlassSprite.fillSprite(OFF_WHITE);
   robotEyeSprite.createSprite(140,140);
   robotEyeSprite.setPivot(70, 70);  
   robotEyeSprite.fillSprite(OFF_WHITE); 
   eyeSprite.fillSmoothCircle(SPRITE_WIDTH/2, SPRITE_HEIGHT/2, SPRITE_HEIGHT/2-6, TFT_BLACK, OFF_WHITE);
   eyeSprite.fillSmoothCircle(SPRITE_WIDTH/2, SPRITE_HEIGHT/2, SPRITE_HEIGHT/2-7, LIGHT_BLUE, TFT_BLACK);
   eyeSprite.fillSmoothCircle(SPRITE_WIDTH/2, SPRITE_HEIGHT/2, pupilSize+2, TFT_BLUE, LIGHT_BLUE);
   eyeSprite.fillSmoothCircle(SPRITE_WIDTH/2, SPRITE_HEIGHT/2, pupilSize, TFT_BLACK, TFT_BLUE);    
   eyeSprite.fillSmoothCircle(SPRITE_WIDTH/2+pupilSize/2, SPRITE_HEIGHT/2+pupilSize/2, 5, TFT_WHITE, TFT_BLACK);
   //eyeSprite.pushSprite(120+eyeX-SPRITE_WIDTH/2, 120+eyeY-SPRITE_HEIGHT/2);
   eyeLids(170,170);
   tft.setSwapBytes(true);
   //hourGlassSprite.setSwapBytes(true);
   
   //tft.fillScreen(0xFFFF);
   //tft.pushImage(26,25,187,189,clock_187x189x16);
   //delay(6000);
   //tft.fillScreen(0xFFFF);
   //tft.pushImage(19,46,201,148,lamp_201x148x16);
   //delay(6000);
   //tft.fillScreen(0x0509);
   //tft.pushImage(62,45,116,149,tick_116x149x16);
   //delay(6000);
   //tft.fillScreen(0xE8E5);
   //tft.pushImage(60,63,119,113,redCross_119x113x16);
   //delay(6000);
   //tft.fillScreen(0xFFE0);
   //tft.pushImage(24,11,192,218,laser_192x218x16);
   //delay(6000);
   //tft.fillScreen(0x0000);
   //tft.pushImage(0,0,241,240,scope_241x240x16);


   //delay(6000);
   //tft.fillScreen(OFF_WHITE);
   //tft.pushImage(50,52,140,135,eyeBlue_140x135x16);
   //delay(6000);
   //tft.fillScreen(OFF_WHITE);
   //tft.pushImage(50,52,140,135,eyeGreen_140x135x16);
   //delay(6000);
   //tft.fillScreen(OFF_WHITE);
   //tft.pushImage(50,52,140,135,eyeRed_140x135x16);
   //delay(6000);
   tft.fillScreen(OFF_WHITE);
robotEyeSprite.pushImage(0,0,140,140,eyeBlue_140x140x16);

int radius = 10;
int direction = 10;


//TEST ANIMATION TO MAK EROBOT EYE ROTATE - not that good...
//     for (int i = 0; i < 1000; ++i) {
//          robotEyeSprite.pushRotated(i * 36); // Assuming pushRotated takes an angle in degrees
//
//         radius += direction;
//         if (i % 100 == 0) {
//         // Toggle direction every 100 iterations
//         direction = -direction;
//        }
//      tft.fillSmoothCircle(120, 120, radius, TFT_BLACK, OFF_WHITE);
//      delay(100);
//      }
//delay(6000);


//tft.fillScreen(OFF_WHITE);
//tft.setSwapBytes(false);
//hourGlassSprite.pushRotated(0);
//tft.setSwapBytes(true);
//hourGlassSprite.fillSprite(OFF_WHITE);
//hourGlassSprite.pushRotated(0);
//hourGlassSprite.fillSprite(OFF_WHITE);
//hourGlassSprite.pushImage(0,0,150,102,hourGlass1_150x102x16);
//hourGlassSprite.pushRotated(0);




//blink();
//delay(20000);
}

void loop() {
unsigned long currentMillis = millis();

  //if (currentMillis - previousMillis >= interval) {
  //      previousMillis = currentMillis;
  //color = (color == TFT_BLACK) ? TFT_RED : TFT_BLACK;
  //tft.fillCircle(120,220,10,color);
  //}

}

void requestEvent() {
 if (chsc6x_is_pressed()) {Wire.write(0x01);}

  }

void receiveEvent(int bytes) {
   
     if (bytes >= 1 + 1 + 1 + 1 ) {
     
    byte command = Wire.read();  // Read the first byte (command)
    eyeX = Wire.read();
    eyeY = Wire.read();
    eyeMovePeriod = Wire.read();  // Read the last byte (command)
    


    switch(command){

    case 1: //sending eye position  
    if (eyeOpen == false){
      eyeOpen = true;
      tft.fillScreen(OFF_WHITE);
      }

      backFill.fillSprite(OFF_WHITE);
      eyeSprite.pushToSprite(&backFill,eyeX-eyePrevX, eyeY-eyePrevY);
      eyeSprite.pushSprite(120+eyeX-SPRITE_WIDTH/2, 120+eyeY-SPRITE_HEIGHT/2);
      backFill.pushSprite(120+eyePrevX-SPRITE_WIDTH/2,120+eyePrevY-SPRITE_HEIGHT/2);
    
         eyePrevX=eyeX;
         eyePrevY=eyeY;
    break;

 case 2: //prompt to close eyes
 closeEyes();
 break; 

case 3: //prompt to open eyes
 openEyes();
 break;   

 case 4: //prompt to blink
 blink();
 break;  

 case 5: //prompt to toggle laser on
 laserOn();
 break;       

 case 6: //prompt to toggle laser off
 laserOff();
 break;       

 case 7: //prompt to open eyes quickly
 openEyesFast();
 break; 

 default:
   //tft.fillScreen(OFF_WHITE)
   ;
    }
    // Now, you have the received data in command, x, y, t1, and t2 variables.
  }
  //tft.fillScreen(TFT_RED);
}

