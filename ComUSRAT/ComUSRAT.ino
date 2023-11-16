#include <TimerThree.h>
#include <math.h>

void rts();

unsigned int buffer_size = 200;
unsigned int buffer_read[200];
unsigned int buffer_send[200];
float sample_rate = 400; // Hz
bool bufferFlag = false;
bool sendFlag = false;
static unsigned long counter = 0;
static unsigned int pos = 0;
bool level = 0;        // value output to the LED

void setup() {
  // initialize serial communications at 115200 bps:
  Serial.begin(115200);
  Timer3.initialize(1 / sample_rate * 1000000); 
  Timer3.attachInterrupt(rts);
  pinMode(LED_BUILTIN, OUTPUT);
}

void rts(){
  // Every 500 ms
  if (counter % 200 == 0)
  {
    // blink led
    level = !level;
    digitalWrite(LED_BUILTIN, level);
  }
  buffer_read[pos] = analogRead(A0);    
  // buffer_read[pos] = int(512 * 0.5 *(sin(2 * PI * counter * 60 / sample_rate) + 1));

  pos++;
  if (pos == buffer_size)
  {
    for (unsigned int i = 0; i < buffer_size; i++)
      buffer_send[i] = buffer_read[i];
    
    bufferFlag = true;
    pos = 0;
  }
  counter++;
}

void loop() 
{
  if (Serial.available() > 0)
  {
    sendFlag = true;
  }

  if (bufferFlag && sendFlag)
  {
    char data = Serial.read();
    if (data == 's')
    { 
      for (unsigned int i = 0; i < buffer_size; i++)
      {
        int high = buffer_send[i] / 256;
        int low = buffer_send[i] % 256;
        Serial.write(high);
        Serial.write(low);
      }
      bufferFlag = false;
      sendFlag = false;
    }
  }
}
