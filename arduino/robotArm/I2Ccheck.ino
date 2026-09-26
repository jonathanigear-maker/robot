void i2cCheck(){
  
  byte error, address;
  int nDevices;
   
  nDevices = 0;
  for(address = 1; address < 127; address++ )
  {
    //Serial.println(address);
  Wire.beginTransmission(address);
    error = Wire.endTransmission();
 
    if (error == 0)
    {
     Serial.print("I2C device found at address 0x");
      if (address<16)  Serial.print("0");
       Serial.print(address,HEX);
       Serial.println(", ");
 
      nDevices++;
    }
    }
    
Serial.println("");
while (nDevices < 5) {}
  }
