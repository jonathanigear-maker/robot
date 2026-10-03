   void eyeLids(uint8_t lidPositionA, uint8_t lidPositionB) {

    
    //Pupil
   lidSprite.fillSprite(OFF_WHITE);
   eyeSprite.pushToSprite(&lidSprite,120+eyeX-SPRITE_WIDTH/2, 120+eyeY-SPRITE_HEIGHT/2);
  //TOP eye lid
  lidSprite.fillRect(0,0, lidPositionA, 240,TFT_BLACK);
  lidSprite.fillRectHGradient(0,0, lidPositionA-5, 240,0xaedc,0x0370);

  //bottom lid
  lidSprite.fillRect(lidPositionB,0, lidPositionB, 240,TFT_BLACK);
  lidSprite.fillRectHGradient(lidPositionB+5,0, lidPositionB, 240,0x1433,0xaedc);
  lidSprite.pushSprite(0, 0);
  }