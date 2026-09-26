#define CENTER_PIXEL  17   // Center pixel index (zero-based)

void mouthEffects(int MouthInputValue) {
  MouthInputValue=sqrt(MouthInputValue);
  // Map the input value to the number of pixels
  int numPixels = map(MouthInputValue, 0, 16, 0, 17);
  //Serial.print(MouthInputValue);
  //Serial.print(" , ");
  //Serial.println(numPixels);
  // Determine whether to expand or contract based on the comparison with the previous input value
  if (MouthInputValue > previousMouthInputValue) {
    // Expand from the center to both sides, one pixel at a time
    for (int i = 0; i < numPixels; i++) {
      int leftPixelIndex = CENTER_PIXEL - i;
      int rightPixelIndex = CENTER_PIXEL + i;
      if (leftPixelIndex >= 0) {
        pixels.setPixelColor(leftPixelIndex, interpolateColor(i, numPixels));
      }
      if (rightPixelIndex < MOUTH_COUNT) {
        pixels.setPixelColor(rightPixelIndex, interpolateColor(i, numPixels));
      }
      pixels.show();
    }
  } else {
    // Contract back to the center, one pixel at a time
    for (int i = previousMouthInputValue; i >= numPixels; i--) {
      int leftPixelIndex = CENTER_PIXEL - i;
      int rightPixelIndex = CENTER_PIXEL + i;
      if (leftPixelIndex >= 0) {
        pixels.setPixelColor(leftPixelIndex, 0);
      }
      if (rightPixelIndex < MOUTH_COUNT) {
        pixels.setPixelColor(rightPixelIndex, 0);
      }
      pixels.show();
    }
  }

  // Update the previous input value
  previousMouthInputValue = MouthInputValue;
}

uint32_t interpolateColor(int index, int totalPixels) {
  float ratio = float(index) / float(totalPixels - 1);
  uint8_t r = 255 * ratio;
  uint8_t g = 255 * (1 - ratio);
  uint8_t b = 0;
  return pixels.Color(r, g, b);
}

int mapLog(int x, int in_min, int in_max, int out_min, int out_max) {
  // Apply logarithmic mapping
  float logValue = log10((float)x / 255 * 9 + 1);
  return map(logValue, 0, log10(10), out_min, out_max);
}
