  //laser on
  void laserOn(){
        huskylens.writeAlgorithm(ALGORITHM_OBJECT_RECOGNITION);
        myArm.setPosition(lookfront, 6, 1000, false);
        laserBool = true;
        lampBool = false;
        faceRecognition = false;
        tagRecognition = false;
        objectRecognition = true;
           sendToLeftEye(5, eyeX, eyeY, eyeMovePeriod);
           sendToRightEye(5, eyeX, eyeY, eyeMovePeriod);
        cute.play(S_HAPPY_SHORT);
  }

   void laserOff(){
        huskylens.writeAlgorithm(ALGORITHM_FACE_RECOGNITION);
        laserBool = false;
        lampBool = false;
        faceRecognition = true;
        tagRecognition = false;
        objectRecognition = false;
           sendToLeftEye(6, eyeX, eyeY, eyeMovePeriod);
           sendToRightEye(6, eyeX, eyeY, eyeMovePeriod);
        cute.play(S_HAPPY_SHORT);
   }
