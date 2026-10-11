
//LIBRARIES
#include "HUSKYLENS.h"
#include "DFRobot_DF2301Q.h"
#include "Adafruit_NeoKey_1x4.h"
#include "seesaw_neopixel.h"
#include "HSVtoRGB.h"
#include <EncBreakout.h>
#include <CuteBuzzerSounds.h>
#include <Adafruit_NeoPixel.h>
#include <xArmServoController.h>
#include <Wire.h>
#include <FABRIK2D.h>
#include "DFRobot_MatrixLidar.h"

//DEFINITIONS
#define NEO_PIN     7
#define MOUTH_PIN 6
#define NEO_COUNT  32
#define MOUTH_COUNT 35
#define speakerPin 5
#define leftEyeTouchPin 9
#define rightEyeTouchPin 10
#define leftEye 0x9
#define rightEye 0x10
#define INTERRUPT_PIN 2
#define BLUE_BUTTON 16
#define RED_BUTTON 15

//#define USE_DF2301Q
//#define USE_ENCODERS
#define USE_MATRIX_LIDAR

//INSTANCE CLASSES

#ifdef USE_DF2301Q
DFRobot_DF2301Q_I2C DF2301Q;
#endif

#ifdef USE_ENCODERS
EncBreakout encA(Wire, 0x0E, EncBreakout::DEFAULT_BRIGHTNESS, 1, 2);
EncBreakout encB(Wire, 0x0F, EncBreakout::DEFAULT_BRIGHTNESS, 1, 2);
#endif

#ifdef USE_MATRIX_LIDAR
  DFRobot_MatrixLidar_I2C tof(0x31);
  uint16_t lidarData[16];
  bool lidarReady = false;
#endif

HUSKYLENS huskylens;

Adafruit_NeoKey_1x4 neokey;
Adafruit_NeoPixel strip(NEO_COUNT, NEO_PIN, NEO_GRBW + NEO_KHZ800);
Adafruit_NeoPixel pixels = Adafruit_NeoPixel(MOUTH_COUNT, MOUTH_PIN, NEO_GRB + NEO_KHZ800);
xArmServoController myArm = xArmServoController(xArm, Serial1);


//GLOBAL VARIABLES
  //general
 bool laserBool = false;
 bool lampBool = false;
 bool AIBool = false;
 bool queryShutDown = false;
 const unsigned long I2CdelayTime = 10; // Delay time in milliseconds
 unsigned long previousI2CMillis = 0;
 int I2CFunction = 1; // Keep track of the current function
 
//Buttons
const unsigned long buttondelayTime = 100; // Delay time in milliseconds
 unsigned long previousButtonMillis = 0;
 int16_t countA = 0;
 int16_t lastCountA = -1;
 int16_t countB = 0;
 int16_t buttonCountA = 0;
 int16_t lastCountB = -1;
 volatile int state = LOW;
 volatile bool pressed = false;
 int rotationCount = 0; // Count of full rotations
 int previousRotationCount = 0; // Previous rotation count
 bool buttonAPressActive = false;
 unsigned long buttonAStartTime = 0;
 bool buttonBPressActive = false;
 unsigned long buttonBStartTime = 0;
 bool buttonCPressActive = false;
 unsigned long buttonCStartTime = 0;
 bool buttonDPressActive = false;
 unsigned long buttonDStartTime = 0; 

 //voiceCode
 uint8_t CMDID = 0;
 unsigned long lastVoiceCommand = 0;
 uint16_t wakeTime = 60;
 uint16_t listenTime = 60;

 //visionCode
 bool faceRecognition = false;
 bool tagRecognition = false;
 bool objectRecognition = false;
 bool trigger = false;
 bool faceFirstSpotted = false;
 unsigned long nothingInterestingTimer = 0;
 unsigned long faceLastSeenTimer = 0;
 uint16_t xBlock = 120;
 uint16_t yBlock = 120;
 uint16_t xBlockWidth = 10;
 uint16_t yBlockWidth = 10;
   
 //eyeMovement
 static int32_t eyeTimeToNextMove = 0L;
 static int8_t eyeMovePeriod= 120;
 static int16_t eyeMoveInterval = 3000;
 static int16_t blinkInterval = 3000;
 static int8_t eyeX = 50;
 static int8_t eyeY = 40;
 int32_t lookingArea =80;
 unsigned long previousRandomEyeMillis = 0;
 unsigned long previousTrackingEyeMillis = 0;
 unsigned long previousBlinkMillis = 0;
 bool eyeOpen = true;   //a bool to keep track if the eyes are open or closed
 int8_t eyeMode = 1;  ///not suer hwat this is. possibly same as above
  
 //neoPixel
 uint32_t neoColor = strip.Color(0,0,0,255);
 uint8_t neoEffect = 0;
 uint8_t neoOffset = 0;
 unsigned long previousNeoEffectMillis = 0;
 int16_t neoEffectInterval = 100; 
 uint16_t pixel = 0;
 uint16_t hue = 0;
 uint8_t colorMode = 0;
 uint8_t brightness = 100;
 uint8_t brightnessTest = 100;
 uint8_t red = 0;
 uint8_t green = 0;
 uint8_t blue = 0;
 uint8_t white = 0;
 bool lightIsOn = false;
 bool lightIsWhite = true;
 
 //mouth variables
 int previousMouthInputValue = 0;
 int MouthInputValue = 0;
 
 //xArmServo
 uint16_t tiltAngle = 500;
 unsigned long previousTiltMillis = 0;
 int16_t tiltInterval = 1000;
 int16_t servo6 = 0;  //ROTATATION
 int16_t servo3 = 0;   //HEAD UPDOWN
 int16_t  targetServo6 = 0;  //ROTATATION
 int16_t targetServo3 = 0;   //HEAD UPDOWN
 int16_t servoPositions[7] = {0};
 //touch
uint16_t debounceDelay = 500;  // Adjust this value as needed
unsigned long lastDebounceTime = 0;

//kinematics
int lengths[] = {102, 97, 160}; // 3DOF arm where shoulder to elbow is 102mm, elbow to wrist is 97mm and wrist to end effector is 160mm.
Fabrik2D fabrik2D(4, lengths); // The arm has 4 joints; one in the origin, the elbow, the wrist and the end effector.
float ang = 0;
float radius = 30;
//float x_offset = 150;
//float y_offset = 150;
xArmServo servosToRead[6] = {
  {1, 0},
  {2, 0},
  {3, 0},
  {4, 0},
  {5, 0},
  {6, 0}
};
 

 xArmServo lookfront[] = {{1, 900}, //this is the claw servo
                     {2, 500},
                     {3, 265},
                     {4, 815},
                     {5, 715},
                     {6, 500}};//this is the rotation servo

 xArmServo lookleft[] = {{1, 900},//this is the claw servo
                      {2, 500},
                      {3, 50},
                      {4, 500},
                      {5, 600},
                      {6, 100}}; //this is the rotation servo

 xArmServo lookright[] = {{1, 900}, //this is the claw servo
                      {2, 500},
                      {3, 50},
                      {4, 500},
                      {5, 600},
                      {6, 900}}; //this is the rotation servo

xArmServo situp[] = {{2, 900}, //this is the head rotation servo
                     {3, 100},
                     {4, 850},
                     {5, 950}};//this is 25 kg  servo

xArmServo shutDown[] = {{1,900}, //this is the claw servo
                       {2, 500},
                       {3, 33},
                       {4, 950},
                       {5, 873},
                       {6, 500}}; //this is the rotation servo
 
//

//SETUP FUNCTION RUNS ON BOOT
void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(speakerPin, OUTPUT);
  pinMode(leftEyeTouchPin, INPUT_PULLUP);
  pinMode(rightEyeTouchPin, INPUT_PULLUP);
  pinMode(INTERRUPT_PIN, INPUT_PULLUP);
  pinMode(RED_BUTTON, OUTPUT);
  pinMode(BLUE_BUTTON, OUTPUT);

  digitalWrite(RED_BUTTON, HIGH);
  digitalWrite(BLUE_BUTTON, HIGH);

  //attachInterrupt(digitalPinToInterrupt(INTERRUPT_PIN), handleInterrupt, CHANGE);
  Serial.begin(9600);
  Serial.println("Serial started at 9600 Baud Rate");
  delay(5000);
  fabrik2D.setTolerance(0.5);

  Wire.begin();
  Serial.println(F("wire started"));


    //INITIALISE THE LIDAR
#ifdef USE_MATRIX_LIDAR

  Serial.println("LIDAR: Initialising...");

  if (tof.begin() == 0) {

    Serial.println("LIDAR: Connected");

    if (tof.setRangingMode(eMatrix_4x4) == 0) {
      lidarReady = true;
      Serial.println("LIDAR: Ready (4x4)");
    } else {
      Serial.println("LIDAR: Failed to set 4x4 mode");
    }

  } else {
    Serial.println("LIDAR: Initialisation failed");
  }

#endif







   //INITIATE HUSKY LENS
   Serial.println("checking husky lens...");
   while (!huskylens.begin(Wire)) {
   Serial.println("husky lens begin failed!");
   delay(100);
   }
   Wire.beginTransmission(0x32);
   int error = Wire.endTransmission();
   if (error == 0){Serial.println("huskylens found at 0x50");
    #define HUSKYLENS_OK
   }
   else{Serial.print("Huskylens error = ");
        Serial.println(error);
   }
   #ifdef HUSKYLENS_OK
    huskylens.writeAlgorithm(ALGORITHM_FACE_RECOGNITION);
    faceRecognition = true;
    tagRecognition = false;
    Serial.println("Huskylens ok!");
   #endif
  

  
  //initialise NeoKey
  if (!neokey.begin(0x30)) {
    Serial.println("Could not start NeoKey, check wiring?");
    while(1) delay(10);
   }
   Wire.beginTransmission(0x30);
   error = Wire.endTransmission();
   if (error == 0){Serial.println("neokey found at 0x32");
    #define NEOKEY_OK
   }
   else{Serial.print("neokey error = ");
        Serial.println(error);
   }
   #ifdef NEOKEY_OK
    neokey.pixels.setPixelColor(0, 0xFF0000);
    neokey.pixels.show();
    Serial.println("neokey ok!");
   #endif

  //initilise Mic
#ifdef USE_DF2301Q

while (!(DF2301Q.begin())) {
    Serial.println("Communication with device failed");
    delay(100);
}

Wire.beginTransmission(0x64);
error = Wire.endTransmission();

if (error == 0) {
    Serial.println("DF2301Q MIC found at 0x64");
    DF2301Q.setVolume(4);
    DF2301Q.setMuteMode(0);
    DF2301Q.setWakeTime(listenTime);
}

#endif
  


  //INITIALISE ENCODER A
  #ifdef USE_ENCODERS
  if(!encA.initialise())
   {
   while(true)
   delay(10);
   }
   Wire.beginTransmission(0x0E);
   error = Wire.endTransmission();
   if (error == 0){Serial.println("Enoder A found at 0x0E");
   #define ENCA_OK
   }
   else{Serial.print("Encoder A error = ");
    Serial.println(error);
   }
   #ifdef ENCA_OK
   #endif

     //INITIALISE ENCODER B
  if(!encB.initialise())
   {
   while(true)
   delay(10);
   }
   Wire.beginTransmission(0x0F);
   error = Wire.endTransmission();
   if (error == 0){Serial.println("Enoder B found at 0x0E");
   #define ENCB_OK
   }
   else{Serial.print("Encoder B error = ");
    Serial.println(error);
   }
   #ifdef ENCB_OK
   #endif
   #endif

//LEFT EYE CHECK();
   Wire.beginTransmission(0x09);
   error = Wire.endTransmission();
   if (error == 0){Serial.println("Left Eye found at 0x09");
   #define LEFTEYE_OK
   }
   else{Serial.print("Left Eye error = ");
    Serial.println(error);
   }
   

   Wire.beginTransmission(0x10);
   error = Wire.endTransmission();
   if (error == 0){Serial.println("Right Eye found at 0x10");
   #define RIGHTEYE_OK
   }
   else{Serial.print("Right Eye error = ");
    Serial.println(error);
   }









delay(1000);



while (digitalRead(INTERRUPT_PIN) != LOW) {
    #ifdef NEOKEY_OK
    neokey.pixels.setPixelColor(0, 0xFF0000);
    neokey.pixels.show();
    delay(500);
    neokey.pixels.setPixelColor(0, 0x000000);
    neokey.pixels.show();
    delay(500);
    #endif
  }


//INITIALSE NEO STRIPS AND BUZZER
  cute.init(speakerPin);
  strip.begin();           // INITIALIZE NeoPixel strip object (REQUIRED)
  strip.show();            // Turn OFF all pixels ASAP
  strip.setBrightness(255);

  pixels.begin();           // INITIALIZE NeoPixel strip object (REQUIRED)
  pixels.show();            // Turn OFF all pixels ASAP
  pixels.setBrightness(255);
  
//open eye animation
#ifdef LEFTEYE_OK
sendToLeftEye(3, eyeX, eyeY, 50);
#endif
#ifdef RIGHTEYE_OK
sendToRightEye(3, eyeX, eyeY, 50);
#endif
delay(2000);

Serial.println("start");
  
Serial1.begin(9600);
delay(500);
myArm.setPosition(lookfront, 6, 1000, false);
faceLastSeenTimer=millis();
kinematics();

}


//MAIN LOOP TO CALL OTHER FUNCTIONS USING A DELAY BETWEEN I2C CALLS
void loop() {
  
  unsigned long currentI2CMillis = millis();
  unsigned long currentButtonMillis = millis();
  queryTouch();   //looks to see if the eye was touched
  queryButton();   //looks to see if a button was touched
  //strip.show();   //updates the neopixels (possibly not meeded here)
  
    neoEffects();

    if (faceLastSeenTimer + 10000 <=millis()){
       trigger = false;}
    if (MouthInputValue > 0)
       {
      MouthInputValue  = MouthInputValue-1;
      mouthEffects(MouthInputValue);}
    //mouthEffects();
    talkToRaspberryPI();
  
    if (pressed == true){
    buttonPress();
    #ifdef USE_ENCODERS
    encoder();
    #endif
    pressed = false;
    }
  

    //This code is just to slow down the I2C traffic.
   if (currentI2CMillis - previousI2CMillis >= I2CdelayTime) {
    switch (I2CFunction) {
      case 1:
        //Serial.println("case 1");
        #ifdef USE_DF2301Q
        checkForSound();
        #endif          
        previousI2CMillis = currentI2CMillis;
        I2CFunction++;
      break;

      case 2:
        //Serial.println("case 2");
        if (eyeOpen ==true )  {
        checkForFace();
        Serial.print("VISION ");
        Serial.print(xBlock);
        Serial.print(" ");
        Serial.print(yBlock);
        Serial.println();}
        previousI2CMillis = currentI2CMillis;
        I2CFunction++;
      break;

      case 3:
        //Serial.println("case 3");
        if (eyeOpen ==true )  {eyeMovement();}
        previousI2CMillis = currentI2CMillis;
        I2CFunction++;
      break;        

      case 4:

        for (uint8_t i = 1; i <= 6; i++) {
          servoPositions[i] = myArm.getPosition(i);
        }

        Serial.print("SERVOS");

        for (uint8_t i = 1; i <= 6; i++) {
          Serial.print(" ");
          Serial.print(servoPositions[i]);
        }

        Serial.println();

        previousI2CMillis = currentI2CMillis;
        I2CFunction++;

      break;

      case 5:
        //Serial.println("case 5");
       nothingInteresting(); 
       previousI2CMillis = currentI2CMillis;
       I2CFunction++;
      break;

      case 6:
      //Serial.println("case 6");
       headTilt();
       previousI2CMillis = currentI2CMillis;
       I2CFunction++;
      break;

      case 7:
      //Serial.println("case 7");
       talkToRaspberryPI();
       //Serial.println("! Hello raspberry PI");
       previousI2CMillis = currentI2CMillis; //not actually I2C but lets use anyway.
       #ifdef USE_MATRIX_LIDAR
        I2CFunction++;
      #else
        I2CFunction = 1;
      #endif
      break;

      #ifdef USE_MATRIX_LIDAR
      case 8:
      //Serial.println("case 8");
        if (lidarReady) {
          if (tof.getAllData(lidarData) == 0) {
            Serial.print("LIDAR");

            for (uint8_t i = 0; i < 16; i++) {
              Serial.print(" ");
              Serial.print(lidarData[i]);
            }

            Serial.println();
          }
        }

        previousI2CMillis = currentI2CMillis;
        I2CFunction = 1;
      break;
      #endif

      default:
        // Handle unexpected values of currentFunction
      break;
    }
  }  
}
