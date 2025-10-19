// EEPROM_slave_fixed.ino
#include <93C46.h>

/*
  EEPROM slave for Python master.
  Commands (send terminated by newline '\n'):
    READ_BIN        - request raw 128 bytes
    READ_HEX        - request human-readable hex dump
    READ_TEXT       - request printable ASCII text
    WRITE_BIN <N>   - accept N bytes and flash to EEPROM (N <= 128)
*/

#define pCS 7
#define pSK 9
#define pDI 10
#define pDO 11

eeprom_93C46 e(pCS, pSK, pDI, pDO);

// EEPROM config
bool eightBitMode = true; // 8-bit mode -> 128 bytes
const int EEPROM_BYTES = 128;

void setup() {
  Serial.begin(115200);
  e.set_mode(eightBitMode ? EEPROM_93C46_MODE_8BIT : EEPROM_93C46_MODE_16BIT);
  delay(100);
  Serial.println("EEPROM Slave Ready");
}

uint8_t readByte(int addr) {
  word w = e.read(addr);
  return (uint8_t)(w & 0xFF);
}

void writeByte(int addr, uint8_t val) {
  e.write(addr, (word)val);
  delay(5); // small pause for write stability
}

void sendHexDump() {
  Serial.println("BEGIN_HEX");
  for (int i = 0; i < EEPROM_BYTES; i += 16) {
    if (i < 0x10) Serial.print('0');
    Serial.print(i, HEX);
    Serial.print(": ");
    for (int j = 0; j < 16; ++j) {
      uint8_t b = readByte(i + j);
      if (b < 0x10) Serial.print('0');
      Serial.print(b, HEX);
      if (j < 15) Serial.print(' ');
    }
    Serial.println();
  }
  Serial.println("END_HEX");
}

void sendTextDump() {
  Serial.println("BEGIN_TEXT");
  for (int i = 0; i < EEPROM_BYTES; ++i) {
    uint8_t b = readByte(i);
    if (b >= 32 && b <= 126) {
      Serial.write(b);
    } else {
      Serial.write('.');
    }
  }
  Serial.println();
  Serial.println("END_TEXT");
}

void sendBinDump() {
  Serial.print("BEGIN_BIN ");
  Serial.println(EEPROM_BYTES);
  for (int i = 0; i < EEPROM_BYTES; ++i) {
    uint8_t b = readByte(i);
    Serial.write(b);
  }
  Serial.println();
  Serial.println("END_BIN");
}

// compute 16-bit checksum
uint16_t checksum16(const uint8_t *buf, int n) {
  uint32_t s = 0;
  for (int i = 0; i < n; ++i) s += buf[i];
  return (uint16_t)(s & 0xFFFF);
}

void loop() {
  if (!Serial.available()) {
    delay(5);
    return;
  }

  String line = Serial.readStringUntil('\n');
  line.trim();

  if (line.length() == 0) return;

  if (line.equalsIgnoreCase("READ_BIN")) {
    sendBinDump();
    return;
  }

  if (line.equalsIgnoreCase("READ_HEX")) {
    sendHexDump();
    return;
  }

  if (line.equalsIgnoreCase("READ_TEXT")) {
    sendTextDump();
    return;
  }

  if (line.startsWith("WRITE_BIN")) {
    int spaceIndex = line.indexOf(' ');
    int N = 0;
    if (spaceIndex > 0) {
      String num = line.substring(spaceIndex + 1);
      N = num.toInt();
    }
    if (N <= 0 || N > EEPROM_BYTES) {
      Serial.print("ERR Invalid length ");
      Serial.println(N);
      return;
    }

    Serial.println("READY");

    uint8_t buf[EEPROM_BYTES];
    int got = 0;
    unsigned long start = millis();
    while (got < N && (millis() - start) < 5000UL) { // 5s timeout
      if (Serial.available()) {
        int r = Serial.readBytes(buf + got, N - got);
        if (r > 0) got += r;
      } else {
        delay(1);
      }
    }
    if (got != N) {
      Serial.print("ERR Timeout got=");
      Serial.println(got);
      return;
    }

    // Write to EEPROM
    e.ew_enable();
    for (int i = 0; i < N; ++i) {
      writeByte(i, buf[i]);
    }
    e.ew_disable();

    // Verify checksum
    uint8_t verifyBuf[EEPROM_BYTES];
    for (int i = 0; i < N; ++i) verifyBuf[i] = readByte(i);
    uint16_t sum = checksum16(verifyBuf, N);
    Serial.print("OK ");
    Serial.println(sum);
    return;
  }

  Serial.print("ERR Unknown command: ");
  Serial.println(line);
}
