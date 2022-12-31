# RYLR998-LoRa

Demo transmit and receive program for the REYAX RYLR998 LoRa module

This code below was written to work with the REYAX RYLR998 LoRa module, using nothing more than five connections to the GPIO pins of a Raspberry 4 Model B Rev 1.5. No electronic components are needed other than five wires and ten female-female GPIO connectors. (Or connect the module directly to a GPIO head, etc., as you wish.)


### GPIO connections

The GPIO connections are as follows:

* VDD to 3.3V physical pin 1 on the GPIO
* RST to GPIO 4, physical pin 7
* TXD to GPIO 15 RXD1 this is physical pin 10
* RXD to GPIO 14 TXD1 this is physical pin 8
* GND to GND physical pin 9.

### Disable Bluetooth and enable uart1 (/dev/ttyS0)

Disable Bluetooth in ```/boot/config.txt``` by appending 

```bash
disable-bt=1
enable-uart=1 
```

Ensure that the serial port is enabled, but the console is disabled--use `sudo raspi-config` for this. Disable the bluetooth service with 

```bash
sudo systemctl disable hciuart.service
```

Enable `uart1` with the device tree overlay facility before running the code. I do this in `/etc/rc.local` with 

```bash
sudo dtoverlay uart1
```

