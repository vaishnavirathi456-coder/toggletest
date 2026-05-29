/*
  toggle_bridge.ino
  =================
  Companion firmware for toggletest Python library.
  Upload this to your Arduino before using ArduinoBackend.

  Protocol (newline-terminated ASCII):
    PING                         → PONG
    CONFIG:<pin>:<INPUT|OUTPUT>  → OK
    READ:<pin>                   → STATE:<0|1>
    WRITE:<pin>:<0|1>            → OK
*/

#define BAUD_RATE 9600
#define CMD_BUFFER_SIZE 32

char cmdBuffer[CMD_BUFFER_SIZE];
int  cmdIndex = 0;

void setup() {
  Serial.begin(BAUD_RATE);
  while (!Serial) {}
}

void loop() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (cmdIndex > 0) {
        cmdBuffer[cmdIndex] = '\0';
        handleCommand(cmdBuffer);
        cmdIndex = 0;
      }
    } else {
      if (cmdIndex < CMD_BUFFER_SIZE - 1)
        cmdBuffer[cmdIndex++] = c;
    }
  }
}

void handleCommand(const char* cmd) {
  if (strcmp(cmd, "PING") == 0) {
    Serial.println("PONG");
    return;
  }

  if (strncmp(cmd, "CONFIG:", 7) == 0) {
    int pin; char modeStr[8];
    if (sscanf(cmd + 7, "%d:%7s", &pin, modeStr) == 2) {
      if (strcmp(modeStr, "INPUT") == 0)       { pinMode(pin, INPUT);  Serial.println("OK"); }
      else if (strcmp(modeStr, "OUTPUT") == 0) { pinMode(pin, OUTPUT); Serial.println("OK"); }
      else Serial.println("ERROR:UNKNOWN_MODE");
    } else Serial.println("ERROR:BAD_FORMAT");
    return;
  }

  if (strncmp(cmd, "READ:", 5) == 0) {
    int pin = atoi(cmd + 5);
    Serial.print("STATE:");
    Serial.println(digitalRead(pin));
    return;
  }

  if (strncmp(cmd, "WRITE:", 6) == 0) {
    int pin, value;
    if (sscanf(cmd + 6, "%d:%d", &pin, &value) == 2) {
      digitalWrite(pin, value ? HIGH : LOW);
      Serial.println("OK");
    } else Serial.println("ERROR:BAD_FORMAT");
    return;
  }

  Serial.println("ERROR:UNKNOWN_COMMAND");
}