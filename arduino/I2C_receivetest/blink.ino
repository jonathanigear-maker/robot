void blink()
{
    eyeLids(70,190);
    delay(eyeMovePeriod/10);
    eyeLids(140,170);
    delay(eyeMovePeriod/2);
    eyeLids(170,170);
    delay(eyeMovePeriod);
    eyeLids(100,190);
    delay(eyeMovePeriod/2);
    eyeLids(70,190);
    delay(eyeMovePeriod/10);
    eyeLids(0,240);
    eyeSprite.pushSprite(120+eyeX-SPRITE_WIDTH/2, 120+eyeY-SPRITE_HEIGHT/2);
}