/********************************************************
 * FABRIK2D 3DOF example
 * Creating the FABRIK object and moving the end effector in a circular motion.
 * You can use whichever unit you want for coordinates, lengths and tolerances as long as you are consistent.
 * Default unit is millimeters.
 ********************************************************/

void kinematics() {

  // Move x and y in a circular motion
  float x = -100;
  float y = 100;

  ang = ((int)(ang + 1)) % 360;

  // Solve inverse kinematics given the coordinates x and y, the desired tool angle and the list of lengths for the arm.
  fabrik2D.solve(y, x, lengths);

  // Angles are printed in degrees.
  // The function calls below shows how easy it is to get the results from the inverse kinematics solution.
  Serial.print(fabrik2D.getAngle(0)* 57296 / 1000);
  Serial.print("\t");
  Serial.print(fabrik2D.getAngle(1)* 57296 / 1000);
  Serial.print("\t");
  Serial.print(fabrik2D.getAngle(2)* 57296 / 1000);
  Serial.print("\t");
  Serial.print(fabrik2D.getX(0));
  Serial.print("\t");
  Serial.print(fabrik2D.getY(0));
  Serial.print("\t");
  Serial.print(fabrik2D.getX(1));
  Serial.print("\t");
  Serial.print(fabrik2D.getY(1));
  Serial.print("\t");
  Serial.print(fabrik2D.getX(2));
  Serial.print("\t");
  Serial.print(fabrik2D.getY(2));
  Serial.print("\t");
  Serial.print(fabrik2D.getX(3));
  Serial.print("\t");
  Serial.println(fabrik2D.getY(3));

  //delay(50);
}
