void neoEffects(){

switch(neoEffect) {
    case 1: //turn on
    
        strip.fill(neoColor);
        colorMode = 0;
        strip.show();
        lightIsOn = true; 
    break;

    case 2: //turn off
        strip.clear();
        strip.show();
        lightIsOn = false; 
    break;

    case 3: //rotating orange light
    //neoEffectInterval = 100;
       if (millis() - previousNeoEffectMillis >= neoEffectInterval) {
          previousNeoEffectMillis = millis();
          strip.clear();
          for (int i = neoOffset; i < NEO_COUNT; i += 2) {
            strip.setPixelColor(i, strip.Color(255, 165, 0));  // Orange color
            strip.show();
            }
        neoOffset = (neoOffset + 1) % 2;
        } 
    break;

    default:
       ;

}

}
