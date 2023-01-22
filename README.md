# RYLR998-LoRa

Asynchronous transceiver python program for 2-way texting with the 
[REYAX RYLR998](https://reyax.com/products/rylr998/) 33cm band LoRa 
module and the Raspberry Pi 4. Get on the air with a Rasperry Pi 4 Model B 
Rev 1.5, a RYLR998 module, five wires and ten female-female GPIO connectors.
There are no threads here, only asynchronous non-blocking I/O calls.


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

This is a work in progress.  I'm taking my time adding IRC-like display functions with the Python curses library slowly and deliberately with all due sloth, so slowly that I would be fired and blacklisted if I were doing this professionally; flunked and expelled without a degree and a boatload of predatory private student loans at usurious interest rates if I were in college; and defunded and defrocked if I were an academician. 

> **POZZO:**    
     It's a disgrace. But there you are.   
  **ESTRAGON:**   
     Nothing we can do about it.           
-- Samuel Beckett. Waiting for Godot, Act 1.

## Non-animated screenshot

I'll get to an animated screenshot. For now, this screenshot shows two MobaXTerm sessions running the `rlyr998.py` program in a Raspberry Pi side-by-side. The Raspberry Pi 4 Bs are located at opposite ends of my living room. Each Raspberry Pi has its own REYAX RYLR998 module connected as above. The yellow text is that of the sender. The received text is magenta. When rylr998.py detects received text, the "LoRa" indicator flashes green; transmission of text flashes the "LoRa" indicator red. The ADDR (address), RSSI and SNR values of the last received message are shown. Text messages are limited to 40 characters (in this version). The screenshot exemplifies the conversation possible at the highest level of the amateur radio art. That's not why I wrote the code, of course. I wrote it to learn asyncio and curses. 

![image](https://user-images.githubusercontent.com/431946/213901591-2c250043-eabe-4aa4-af2a-d68fee45ad12.png)

## TO DO

* Add parsing of the AT+RESET function. Though this will set CRFOP to 22dBm, which does require a license (I have one). 
* Display the configuration parameters.
* Add a task queue for ATcmd() tasks. This is to avoid ERR=16, which occurs when an AT command is sent before another finishes. You wouldn't want that to happen.
* Add function key handling for changing configuration parameters, such as frequency, netid, etc.
* But be careful about changing the serial port parameters--you'll be sorry! 
* I thought about using urwid, but urwid wants you to run in its loop, and I want urwid to run in my transceiver loop. I am toying with the idea of inverting urwid so that it runs in the asyncio event loop with the curses wrapper function. I would call this "widur." 
* You could make the windows resizable. Dunno.
* Rewrite in micropython for the Raspberry Pico. 

## TO NOT DO

* No threads! Asyncio only.

## Markovian Design

* All the action takes place in the main loop,`xcvr(stdscr)`, one **input** character at a time, as a function of the state and the current input character.
* Input means keyboard and serial port input from the REYAX RYLR998 module.
* Keyboard input is non-blocking and raw--almost vegan. 
* An "empty" character is allowed--in fact we like empty characters.
* Output means screen (curses) output and serial port output of AT commands to the REYAX RYLR998 module.
* Screen output is not one character at a time. Instead of calling `refresh()` when a window changes, we call `win.noutrefresh()` and set a dirty bit. At the beginning of the transceiver loop, if the dirty bit is set, `curses.doupdate()` is called and the dirty bit is reset. This is an optimization.
*  Serial port output cannot be one character at a time, since complete AT commands have to be sent to the RYLR998 through the serial port.
*  Receiving and parsing responses from AT commands takes precedence over transmitting and sending configuration commands and parameter queries.
