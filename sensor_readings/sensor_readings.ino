/**
 * ELE495 - Sensör Modülü (Ultrasonik Ölçüm)
 * 
 * Bu kod, dört yönlü HC-SR04 ultrasonik sensörler ile
 * mesafe ölçümü yapar ve değerleri JSON formatında seri porta gönderir.
 * 
 * Sensörler:
 * - Ön (TRIG: D2, ECHO: D3)
 * - Sağ (TRIG: D4, ECHO: D5)
 * - Sol (TRIG: D6, ECHO: D7)
 * - Arka (TRIG: D8, ECHO: D9)
 */

#include <NewPing.h>

// HC-SR04 pin tanımları
#define TRIG_FRONT 2
#define ECHO_FRONT 3
#define TRIG_RIGHT 4
#define ECHO_RIGHT 5
#define TRIG_LEFT 6
#define ECHO_LEFT 7
#define TRIG_BACK 8
#define ECHO_BACK 9

#define MAX_DISTANCE 400 // Maksimum ölçüm mesafesi (cm)

// Sensör nesneleri oluşturuluyor
NewPing sonar_front(TRIG_FRONT, ECHO_FRONT, MAX_DISTANCE);
NewPing sonar_right(TRIG_RIGHT, ECHO_RIGHT, MAX_DISTANCE);
NewPing sonar_left(TRIG_LEFT, ECHO_LEFT, MAX_DISTANCE);
NewPing sonar_back(TRIG_BACK, ECHO_BACK, MAX_DISTANCE);

void setup() {
  Serial.begin(115200); // Seri haberleşme başlatılıyor
  while (!Serial) {
    delay(100); // USB bağlantısı bekleniyor
  }
  Serial.println("DEBUG: Seri haberleşme başlatıldı.");
}

void loop() {
  // Her sensörden mesafe okunuyor (cm)
  float dist_front = sonar_front.ping_cm();
  float dist_right = sonar_right.ping_cm();
  float dist_left  = sonar_left.ping_cm();
  float dist_back  = sonar_back.ping_cm();

  // 0 okuması alınırsa, bu sensör bir şey algılamadı anlamına gelir
  dist_front = (dist_front == 0) ? MAX_DISTANCE : dist_front;
  dist_right = (dist_right == 0) ? MAX_DISTANCE : dist_right;
  dist_left  = (dist_left  == 0) ? MAX_DISTANCE : dist_left;
  dist_back  = (dist_back  == 0) ? MAX_DISTANCE : dist_back;

  // JSON formatında string oluşturuluyor
  String json = "{";
  json += "\"dist_front\":" + String(dist_front, 1) + ",";
  json += "\"dist_right\":" + String(dist_right, 1) + ",";
  json += "\"dist_back\":"  + String(dist_back, 1)  + ",";
  json += "\"dist_left\":"  + String(dist_left, 1);
  json += "}";

  // JSON seri porta yazdırılıyor
  Serial.println(json);

  delay(200); // 200ms bekle (yaklaşık 5Hz güncelleme hızı)
}
