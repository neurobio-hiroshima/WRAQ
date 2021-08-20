/*
firmware for WRAQ_WiFi
Date: 2020.04.14
Code: Hidenori Aizawa@Hiroshima University

Library dependencies
Ambient ESP32 ESP8266 library (ver. 1.0.1) by Ambient Data (needs installation)
RTClib library (ver. 1.13.0) by Adafruit (needs installation)
WiFi library (ver. 1.2.7) by Arduino (built-in)
Wire library by Arduino (built-in)
*/  

// include dependent librararies
#include <Ambient.h>
#include <WiFi.h>
#include <Wire.h>
#include "driver/rtc_io.h"
#include <RTClib.h>

//////////////// Key Settings ///////////////////
RTC_DATA_ATTR const char* ssid = "XXXXX"; // change this to your WiFi network available
RTC_DATA_ATTR const char* password = "YYYYY"; // change this to your passphrase to the WiFi network
RTC_DATA_ATTR unsigned int channelId = 12345; // channel ID issued by Ambient Data, specific to a WRAQ-WiFi
RTC_DATA_ATTR const char* writeKey = "XXXXX"; // write key issued by Ambient Data, specific to a WRAQ-WiFi

/////////////// Global Objects ////////////////////
RTC_DS3231 rtc;
WiFiClient client;
Ambient ambient;
DateTime now;

#define NSAMPLES  60 //  Number of samples with which a colloection of data is uploaded at a time
#define SLEEP_DURATION 64 // Duration in deep sleep to save battery in second
#define WIFI_TIMEOUT 10000  // Timeout to wait for WiFi connection in second
#define SDA 21  // pin number used for SDA in i2c protocol
#define SCL 22  // pin number used for SCL in i2c protocol

#define SECONDS_IN_DAY   86400   // 24 * 60 * 60 s
#define SECONDS_IN_HOUR  3600    // 60 * 60 s

// pin number used to collect the number of wheel revolution from binary counter and cds photoresistor
#define QA 25
#define QB 26
#define QC 27
#define QD 13
#define QE 5
#define QF 16
#define QG 17
#define QH 4
#define CDS_INPUT 36

// pin mumber used to drive cds and to clear the binary counter
gpio_num_t pin_cds_pow = GPIO_NUM_12; // used to enpower cds and trigger RCK on binary counter to update register
gpio_num_t pin_cclr = GPIO_NUM_14; // used to turn the clear pin (CCLR) to reset the binary counter

// variales used to keep data before uploading to the Ambient server
RTC_DATA_ATTR int sampleIdx = 0;
RTC_DATA_ATTR int cdsValue[NSAMPLES + 1];
RTC_DATA_ATTR int nRevolution[NSAMPLES + 1];
RTC_DATA_ATTR unsigned int unix_seconds[NSAMPLES + 1];

////////////// Setup ///////////////////
void setup() {
  // Initial setting to begin serial monitor
  Serial.begin(115200);
  setCpuFrequencyMhz(80);
  Serial.println("Serial started");
  Wire.begin(SDA, SCL); // Assign the pins as SDA / SCL used in i2c protocol
  if (! rtc.begin()) {  // initiate real time clock (RTC) module to refer to the timestamp 
    while (1);
  }
  Serial.println("RTC began!");
  if (rtc.lostPower()) {  // reset the time in RTC when the battery ran out or replaced
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  }

  // initiate the pins enpowering cds and clearing the binary counter
  rtc_gpio_init(pin_cds_pow); // cds_power and also for RCK on counter to update register
  rtc_gpio_init(pin_cclr); // CCLR
  rtc_gpio_set_direction(pin_cds_pow, RTC_GPIO_MODE_OUTPUT_ONLY);
  rtc_gpio_set_direction(pin_cclr, RTC_GPIO_MODE_OUTPUT_ONLY);
  rtc_gpio_set_level(pin_cds_pow, 0); 
  rtc_gpio_set_level(pin_cclr, 1); 

  // setting all the pins connected to the binary counter as inputs
  pinMode(QA, INPUT); // QA
  pinMode(QB, INPUT); // QB
  pinMode(QC, INPUT); // QC
  pinMode(QD, INPUT); // QD
  pinMode(QE, INPUT); // QE
  pinMode(QF, INPUT); // QF
  pinMode(QG, INPUT); // QG
  pinMode(QH, INPUT); // QH

  delay(10);
}

///////////////////// Loop //////////////////////
void loop()
{
  // enpower cds and move counter data to register
  rtc_gpio_set_level(pin_cds_pow, 1);
  delay(10);

  // read the values from the binary counter
  int ValA = digitalRead(QA);
  int ValB = digitalRead(QB);
  int ValC = digitalRead(QC);
  int ValD = digitalRead(QD);
  int ValE = digitalRead(QE);
  int ValF = digitalRead(QF);
  int ValG = digitalRead(QG);
  int ValH = digitalRead(QH);
  // calculate the number of revolution 
  int nRevBuf = ValA * 1 + ValB * 2 + ValC * 4 + ValD * 8 + ValE * 16 + ValF * 32 + ValG * 64 + ValH * 128;

  sampleIdx = sampleIdx + 1; // increment the sample index
  nRevolution[sampleIdx] = nRevBuf; // keep the number of wheel revolution to the current variable
  cdsValue[sampleIdx] = analogRead(CDS_INPUT);  // keep the cds data to the current variable

  now = rtc.now();  // obtain the current timestamp from RTC
  // Reporting the current timestamp to the serial monitor for sure
  Serial.print("now: ");
  Serial.print(now.year()); Serial.print("-");
  Serial.print(now.month()); Serial.print("-");
  Serial.print(now.day()); Serial.print(" ");
  Serial.print(now.hour()); Serial.print(":");
  Serial.print(now.minute()); Serial.print(":");
  Serial.println(now.second());
  unix_seconds[sampleIdx] = now.unixtime(); // timestamp converted into unixtime to save memory
  // Reporting the current timestamp as unixtime together with the number of revolution (nRev) and cds data (cdS)
  Serial.print("now.unixtime: ");
  Serial.println(now.unixtime());
  Serial.print("nRev: ");
  Serial.println(nRevolution[sampleIdx]);    
  Serial.print("cdS: ");
  Serial.println(cdsValue[sampleIdx]);
   
  // resetting binary counter (negative logic)
  rtc_gpio_set_level(pin_cclr, 0); 
  delay(10);
  rtc_gpio_set_level(pin_cclr, 1);
  delay(10);

  // upload a collection of data to the Ambient server when sample index reached at NSAMPLES you set
  if (sampleIdx > NSAMPLES - 1) {
    // connecting to WiFi
    connectToWiFi();
    // prepare data to be uploaded in a JSON format
    char buffer[50 +  85 * (NSAMPLES + 1)];
    sprintf(buffer, "{\"writeKey\":\"%s\",\"data\" : [", writeKey);
    for (int i = 1; i < NSAMPLES+1 ; i++) {
      sprintf(&buffer[strlen(buffer)], "{\"created\" : %d000, \"d%d\" : \"%d\", \"d%d\" : \"%d\"},",
              unix_seconds[i], 1, nRevolution[i], 2, cdsValue[i]);
    }
    buffer[strlen(buffer) - 1] = '\0';
    sprintf(&buffer[strlen(buffer)], "]}\r\n");
    // upload the data to the Ambient server
    ambient.begin(channelId, writeKey, &client); // initializing Ambient with channel ID and write key
    int sent = ambient.bulk_send(buffer); // sending data to Ambient
    Serial.println(buffer);     // report the uploaded contents to the serial monitor for sure
    sampleIdx = 0; // resetting sample index to move to the next round of data collection 
  }
  // Move to the deep sleep mode while the binary counter collect the data to save battery
  goToDeepSleep();
}


///////////////   Functions   //////////////////
// Move to the deep sleep mode while the binary counter collect the data to save battery
void goToDeepSleep() {
  // setting before going to sleep
  Serial.println("Going to sleep...");
  WiFi.disconnect(true);
  WiFi.mode(WIFI_OFF);
  btStop();
  // setting output pins the same condition while the microcontroller is in deep sleep mode
  rtc_gpio_init(pin_cds_pow);
  rtc_gpio_init(pin_cclr);
  rtc_gpio_set_direction(pin_cds_pow, RTC_GPIO_MODE_OUTPUT_ONLY);
  rtc_gpio_set_direction(pin_cclr, RTC_GPIO_MODE_OUTPUT_ONLY);
  rtc_gpio_set_level(pin_cds_pow, 0);
  rtc_gpio_set_level(pin_cclr, 1);
  esp_sleep_pd_config(ESP_PD_DOMAIN_RTC_PERIPH, ESP_PD_OPTION_ON);
  // setting when to wake up and going to sleep
  esp_sleep_enable_timer_wakeup(SLEEP_DURATION * 1000 * 1000);
  esp_deep_sleep_start();
}

// connecting to WiFi
void connectToWiFi() {
  // beginning with WiFi session with your network ssid and passphrase
  Serial.println("connecting to WiFi ...");
  WiFi.begin(ssid, password);

  // Keep track of when we started our attempt to get a WiFi connection
  unsigned long startAttemptTime = millis();

  // Keep looping while we're not connected AND haven't reached the timeout
  while (WiFi.status() != WL_CONNECTED && 
          millis() - startAttemptTime < WIFI_TIMEOUT){
    delay(10);
  }

  // Make sure that we're actually connected, otherwise go to deep sleep
  if(WiFi.status() != WL_CONNECTED){
    Serial.println("FAILED");
    goToDeepSleep();
  }
}
