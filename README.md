# RYLR998-LoRa

Asynchronous transceiver demo program for the [REYAX RYLR998](https://reyax.com/products/rylr998/) 33cm band LoRa module and the Raspberry Pi 4


The python code of this repository was written to work with the REYAX RYLR998 LoRa module, using nothing more than five connections to the GPIO pins of a Raspberry pi 4 Model B Rev 1.5. No electronic components are needed other than five wires and ten female-female GPIO connectors. (Or connect the module directly to a GPIO head, etc., as you wish.) There are no threads here, only asynchronous non-blocking I/O calls.


## Python Module Dependencies

* python 3.9+
* rPI.GPIO
* [asyncio](https://pypi.org/project/asyncio/)
* [aioserial](https://pypi.org/project/aioserial/) 1.3.1+
* [curses](https://docs.python.org/3/library/curses.html) 

`pip install asyncio` and so on should work.

## GPIO connections

The GPIO connections are as follows:

* VDD to 3.3V physical pin 1 on the GPIO
* RST to GPIO 4, physical pin 7
* TXD to GPIO 15 RXD1 this is physical pin 10
* RXD to GPIO 14 TXD1 this is physical pin 8
* GND to GND physical pin 9.

WARNING: get this wrong and you could fry your Raspberry Pi 4 and your REYAX RTLR998. I haven't had problems, knock wood, but the [MIT license](https://github.com/flengyel/RYLR998-LoRa/blob/main/LICENSE) comes with no warranty. Check your connections! Under no circumstances apply 5V to the REYAX. Only 3.3V. 

## Disable Bluetooth and enable uart1 (/dev/ttyS0)


1. Ensure that the login shell over the serial port is disabled, but the serial port is enabled. In `sudo raspi-config`, select Interfacing Options, then select Serial. Answer "no" to "Would you like a login shell to be accessible over serial?" and answer "yes"  to "woud you like the serial port hardware to be enabled?".

2. Disable Bluetooth in ```/boot/config.txt``` by appending 
```bash
disable-bt=1
enable-uart=1 
```
Disable the bluetooth service with 
```bash
sudo systemctl disable hciuart.service
```

3. Enable `uart1` with the device tree overlay facility before running the code. I do this in `/etc/rc.local` with 

```bash
sudo dtoverlay uart1
```

## Disclaimer

This is a work in progress.  I'm taking my time adding IRC-like display functions with the Python curses library slowly and deliberately with all due sloth, so slowly that I would be fired and blacklisted if I were doing this professionally; flunked and expelled without a degree and a boatload of private student loans if I were in college; wiped out and in debt if I sold my life savings worth of deeply in-the-money uncovered calls purchased at zero-days to expiration one minute before the market closes while shorting the underlying security at the strike price instead of covering the calls, and having all the calls immediately exercised in addition to a margin call for the shares I borrowed; and defunded and defrocked if I were an academician. Other than that, it's a labor of love. 
