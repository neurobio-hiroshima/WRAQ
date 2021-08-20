/*
Arduino firmware for Adafruit adalogger used in WRAQ
Date: 2020.04.14
Code: Hidenori Aizawa@Hiroshima University
output log format: date as yyyy-mm-dd hh:mm:ss, [sensor output]

Library dependencies
RTCZero library (ver. 1.5.2) by Arduino (needs installation)
SD library (ver. 1.2.4) by Arduino (built-in)
*/  

////////////////////////////////////////////////////////////
//#define ECHO_TO_SERIAL // Allows serial output if uncommented
////////////////////////////////////////////////////////////

//////////////// Including library  ///////////////////
#include <SD.h>
#include <RTCZero.h>  // include RTCZero library

#define cardSelect 4  // Set the pin used for uSD

//////////////// Key Settings ///////////////////
#define SampleIntSec 4 // RTC - Sample interval in seconds
#define SamplesPerCycle 15  // Number of samples to buffer before uSD card flush is called

/* Change these values to set the current initial time */
const uint8_t hours = 11;
const uint8_t minutes = 17;
const uint8_t seconds = 0;
/* Change these values to set the current initial date */
const uint8_t day = 29;
const uint8_t month = 12;
const uint8_t year = 20;
bool H24 = true;

/////////////// Global Objects ////////////////////
RTCZero rtc;    // Create RTC object
File logfile;   // Create file object
int NextAlarmSec; // Variable to hold next alarm time in seconds
unsigned int CurrentCycleCount;  // Num of smaples in current cycle, before uSD flush call

////////////// Setup ///////////////////
void setup() {
  // initializing real time clock
  rtc.begin(H24);    // Start the RTC in 24hr mode
  rtc.setTime(hours, minutes, seconds);   // Set the time
  rtc.setDate(day, month, year);    // Set the date

  // initializing the serial monitor for debugging (not used in recording)
  #ifdef ECHO_TO_SERIAL
    while (! Serial); // Wait until Serial is ready
    Serial.begin(9600);
    Serial.println("\r\nWRAQ system");
  #endif

  // setting pins of arduino as input or output
  pinMode(5, INPUT); // input from Q3 pin of binary counter 4520N
  pinMode(6, INPUT); // input from Q2 pin of binary counter 4520N
  pinMode(9, INPUT); // input from Q1 pin of binary counter 4520N
  pinMode(10, INPUT); // input from Q0 pin of binary counter 4520N
  pinMode(11, OUTPUT); // output to RES pin of binary counter 4520N
  pinMode(12, OUTPUT); // output for cdS photoresistor
  pinMode(13, OUTPUT); // output for LED to blink upon error
  digitalWrite(13, LOW);
  
  // see if the card is present and can be initialized:
  if (!SD.begin(cardSelect)) {
    Serial.println("Card init. failed! or Card not present");
    error(2);     // Two red flashes means no card or card init failed.
  }

  // prepare file named unused so far to save new data (e.g., ANALOG01.CSV)
  char filename[15];
  strcpy(filename, "ANALOG00.CSV");
  for (uint8_t i = 0; i < 100; i++) {
    filename[6] = '0' + i/10;
    filename[7] = '0' + i%10;
    // create if the filename does not exist, do not open existing, write, sync after write
    if (! SD.exists(filename)) {
      break;
    }
  }

  // open file in uSD card
  logfile = SD.open(filename, FILE_WRITE);

  // check if the log file was created 
  #ifdef ECHO_TO_SERIAL
    if( ! logfile ) {
          Serial.print("Couldn't create "); 
      Serial.println(filename);
      error(3);
    }
    Serial.print("Logging to "); 
    Serial.println(filename);
  #endif

  pinMode(13, OUTPUT); // output to LED to blink upon error
  digitalWrite(13, LOW);
}

///////////////////// Loop //////////////////////
void loop() {
  CurrentCycleCount += 1;     //  Increment samples in current uSD flush cycle
  delay(10);
  
  #ifdef ECHO_TO_SERIAL
    SerialOutput();           // Only logs to serial if ECHO_TO_SERIAL is uncommented at start of code
  #endif
  
  SdOutput();                 // Output to uSD card

  // Code to limit the number of power hungry writes to the uSD
  if( CurrentCycleCount >= SamplesPerCycle ) {
    logfile.flush();
    CurrentCycleCount = 0;
    #ifdef ECHO_TO_SERIAL
      Serial.println("logfile.flush() called");
    #endif
  }

///////// Interval Timing and Sleep Code ////////////////
  NextAlarmSec = (NextAlarmSec + SampleIntSec) % 60;   // i.e. 65 becomes 5
  rtc.setAlarmSeconds(NextAlarmSec); // RTC time to wake, currently seconds only
  rtc.enableAlarm(rtc.MATCH_SS); // Match seconds only
  delay(50); // Brief delay prior to sleeping not really sure its required
  
  rtc.standbyMode();    // Sleep until next alarm match
  
  // Code re-starts here after sleep !
}

///////////////   Functions   //////////////////
void SerialOutput() { // Report what is saved to uSD for sure in the serial monitor 
  // reading binary counter
  int Q0 = digitalRead(5);
  int Q1 = digitalRead(6);
  int Q2 = digitalRead(9);
  int Q3 = digitalRead(10);
  int nRevolution = Q0*1 + Q1*2 + Q2*4 + Q3*8;
  // resetting binary counter
  digitalWrite(11, HIGH);
  delay(10);
  digitalWrite(11, LOW);
  // reading cds value
  digitalWrite(12, HIGH);
  delay(10);
  int cdsValue = analogRead(5);
  digitalWrite(12, LOW);

// Formatting for file out put yyyy-mm-dd hh:mm:ss, nRevolution, cds
  Serial.print(rtc.getYear()+2000);
  Serial.print("-");
  if(rtc.getMonth()<10){  // Use two digits to represent month to keep consistency in date format
    Serial.print("0");
  }
  Serial.print(rtc.getMonth());
  Serial.print("-");
  if(rtc.getDay()<10){  // Use two digits to represent day to keep consistency in date format
    Serial.print("0");
  }
  Serial.print(rtc.getDay());
  Serial.print(" ");
  Serial.print(rtc.getHours());
  Serial.print(":");
  if(rtc.getMinutes()<10) // Use two digits to represent minute to keep consistency in date format
    Serial.print('0');      
  Serial.print(rtc.getMinutes());
  Serial.print(":");
  if(rtc.getSeconds()<10) // Use two digits to represent second to keep consistency in date format
    Serial.print('0');     
  Serial.print(rtc.getSeconds());
  Serial.print(",");
  Serial.print(nRevolution);   // Print the number of revolution  
  Serial.print(",");
  Serial.println(cdsValue);   // Print the cds value  
}

void SdOutput() { // Save data to uSD
  // reading binary counter 
  int Q0 = digitalRead(5);
  int Q1 = digitalRead(6);
  int Q2 = digitalRead(9);
  int Q3 = digitalRead(10);
  int nRevolution = Q0*1 + Q1*2 + Q2*4 + Q3*8;
 
  // resetting binary counter
  digitalWrite(11, HIGH);
  delay(10);
  digitalWrite(11, LOW);
  digitalWrite(12, HIGH);
  delay(10);
  // reading cds value
  int cdsValue = analogRead(5);
  digitalWrite(12, LOW);
  
// Formatting for file out put yyyy-mm-dd hh:mm:ss, nRevolution, cds
  logfile.print(rtc.getYear()+2000);
  logfile.print("-");
  if(rtc.getMonth()<10){  // Use two digits to represent month to keep consistency in date format
    logfile.print("0");
  }
  logfile.print(rtc.getMonth());
  logfile.print("-");
  if(rtc.getDay()<10){  // Use two digits to represent day to keep consistency in date format
    logfile.print("0");
  }
  logfile.print(rtc.getDay());
  logfile.print(" ");
  logfile.print(rtc.getHours());
  logfile.print(":");
  if(rtc.getMinutes() < 10) // Use two digits to represent minute to keep consistency in date format
    logfile.print('0');      
  logfile.print(rtc.getMinutes());
  logfile.print(":");
  if(rtc.getSeconds() < 10) // Use two digits to represent second to keep consistency in date format
    logfile.print('0');      
  logfile.print(rtc.getSeconds());
  logfile.print(",");
  logfile.print(nRevolution);   // save the number of revolution to uSD card
  logfile.print(",");
  logfile.println(cdsValue);   // save cds value to uSD card
}

// Write data header.
void writeHeader() {
  logfile.println("DD:MM:YYYY hh:mm:ss, nRevolution, cds");
}

// blink out an error code
void error(uint8_t errno) {
  while(1) {
    uint8_t i;
    for (i=0; i<errno; i++) {
      digitalWrite(13, HIGH);
      delay(100);
      digitalWrite(13, LOW);
      delay(100);
    }
    for (i=errno; i<10; i++) {
      delay(200);
    }
  }
}
