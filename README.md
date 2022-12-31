# RYLR998-LoRa

Demo program for the REYAX RYLR998 LoRa module

This code below was written to work with the REYAX RYLR998 LoRa module, using nothing more than five connections to the GPIO pins of a Rasperry 4 Model B Rev 1.5. No electronic components are needed other than five wires and ten female-female GPIO connectors. (Or connect the module directly to a GPIO head, etc., as you wish.)

The GPIO connections are as follows:

* VDD to 3.3V physical pin 1 on the GPIO
* RST to GPIO 4, physical pin 7
* TXD to GPIO 15 RXD1 this is physical pin 10
* RXD to GPIO 14 TXD1 this is physical pin 8
* GND to GND physical pin 9.
