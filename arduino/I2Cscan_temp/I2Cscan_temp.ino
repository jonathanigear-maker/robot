#include <Wire.h>
#include "DFRobot_MatrixLidar.h"

// --------------------------------------------------------------------------
// DFRobot 8x8 Matrix LiDAR
// --------------------------------------------------------------------------

DFRobot_MatrixLidar_I2C tof(0x31);

uint16_t buf[64];
bool lidarReady = false;

// --------------------------------------------------------------------------
// Setup
// --------------------------------------------------------------------------

void setup() {

  Serial.begin(9600);
  delay(2000);

  Serial.println();
  Serial.println("================================");
  Serial.println("DFRobot Matrix LiDAR Test");
  Serial.println("I2C Address: 0x31");
  Serial.println("================================");

  // Initialise I2C
  Serial.println("TEST 1: Starting I2C");

  Wire.begin();
  //Wire.setClock(100000);

  Serial.println("TEST 2: I2C ready");

  // Check whether device responds
  Wire.beginTransmission(0x31);
  byte error = Wire.endTransmission();

  Serial.print("TEST 3: I2C scan result = ");
  Serial.println(error);

  if (error != 0) {
    Serial.println("ERROR: No device responding at 0x31");
    return;
  }

  Serial.println("TEST 4: Starting LiDAR begin");

  int result = tof.begin();

  Serial.print("TEST 5: LiDAR begin result = ");
  Serial.println(result);

  if (result != 0) {
    Serial.println("ERROR: LiDAR begin failed");
    return;
  }

  Serial.println("TEST 6: Setting 4x4 mode");

unsigned long start = millis();

int modeResult = tof.setRangingMode(eMatrix_4x4);

Serial.print("Mode setup took: ");
Serial.print(millis() - start);
Serial.println(" ms");

Serial.print("TEST 7: Mode result = ");
Serial.println(modeResult);


  Serial.print("TEST 7: Mode result = ");
  Serial.println(result);

  if (result != 0) {
    Serial.println("ERROR: Cannot configure 8x8 mode");
    return;
  }

  lidarReady = true;

  Serial.println("================================");
  Serial.println("LiDAR READY!");
  Serial.println("================================");
}

// --------------------------------------------------------------------------
// Loop
// --------------------------------------------------------------------------

void loop(void){
  tof.getAllData(buf);
  for(uint8_t i = 0; i < 4; i++){
    Serial.print("Y");
    Serial.print(i);
    Serial.print(": ");
    for(uint8_t j = 0; j < 4; j++){
      Serial.print(buf[i * 4 + j]);
      Serial.print(",");
    }
    Serial.println("");
  }
  Serial.println("------------------------------");
  delay(10);
}