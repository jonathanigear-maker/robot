void openEyes()
{
      eyeX = 0;
      eyeY = 0;
    eyeLids(140,170);
    delay(500);
      eyeX = 0;
      eyeY = -40;
    eyeLids(140,170);
    delay(500);
      eyeX = 0;
      eyeY = 0;
    eyeLids(140,170);
    delay(500);
          eyeX = 0;
      eyeY = 40;
    eyeLids(140,170);
    delay(500);
      eyeX = 0;
      eyeY = 0;
    eyeLids(140,170);
    delay(500);
          eyeX = 0;
      eyeY = 0;
        eyePrevX=eyeX;
        eyePrevY=eyeY;
    eyeLids(140,170);
    delay(500);
    eyeLids(100,190);
    delay(5);
    eyeLids(70,190);
    delay(5);
    eyeLids(30,240);
    delay(5);
    eyeLids(0,240);
}

void openEyesFast()
{
      eyeX = 0;
      eyeY = 0;
    eyeLids(140,170);
    delay(500);
    eyeLids(100,190);
    delay(5);
    eyeLids(70,190);
    delay(5);
    eyeLids(30,240);
    delay(5);
    eyeLids(0,240);
}


void closeEyes() 
{
      eyeX = -100;
      eyeY = 0;
    eyeLids(70,190);
    delay(10);
    eyeLids(100,190);
    delay(10);
    eyeLids(140,170);
    delay(500);
    eyeLids(170,170);
}