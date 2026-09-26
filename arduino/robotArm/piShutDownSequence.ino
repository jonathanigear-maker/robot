void piShutDownSequence(){

if (queryShutDown == false){

queryShutDown=true;
lastVoiceCommand = millis()-wakeTime*1000;
myArm.setPosition(shutDown, 6, 1000, false);
sendToLeftEye(3, 0, 0, 100);
sendToRightEye(3, 0, 0, 100);
for (int i=0; i< neokey.pixels.numPixels(); i++) {
    neokey.pixels.setPixelColor(i, 0x000000);
}
encB.setRGB(0, 0, 0);
encA.setRGB(0, 0, 0);
strip.clear();
strip.show(); 


}
}
