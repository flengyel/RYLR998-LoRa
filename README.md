# RYLR998-LoRa® 

A python program for 2-way texting with the 33cm band
[REYAX RYLR998](https://reyax.com/products/rylr998/) LoRa® module, 
either with a Raspberry Pi 4, five wires and ten female-female GPIO connectors; or
with a PC and a CP2102 USB 2.0 to TTL serial converter, four wires and 
eight female-female GPIO connectors. 
There are no threads here, only asynchronous non-blocking I/O calls.

## Usage
```bash
usage: rylr998.py [-h] [--debug] [--addr [0..65535]] [--band [902250000..927750000]] [--crfop [0..22]] [--mode [0|1|2,30..60000,30..60000]]
                  [--netid [3..15|18]] [--parameter [7..11,7..9,1..4,4..24]] [--port [/dev/ttyS0-/dev/ttyS999]]
                  [--baud (300|1200|4800|9600|19200|28800|38400|57600|115200)]

options:
  -h, --help            show this help message and exit
  --debug               log DEBUG information

rylr998 config:
  --addr [0..65535]     Module address (0..65535). Default is 0
  --band [902250000..927750000]
                        Module frequency (902250000..927750000) in Hz. NOTE: the full 33cm ISM band limits 902 MHz and 928 MHz are guarded by the
                        maximum configurable bandwidth of 500 KHz (250 KHz on either side of the configured frequency). See the PARAMETER argument
                        for bandwidth configuration. Default: 915125000
  --crfop [0..22]       RF pwr out (0..22) in dBm. NOTE: whenever crfop is set, the module will stop receiving. Transmit at least once after
                        setting crfop to receive normally. Default: 22
  --mode [0|1|2,30..60000,30..60000]
                        Mode 0: transceiver mode. Mode 1: sleep mode. Mode 2,x,y: receive for x msec sleep for y msec and so on, indefinitely.
                        Default: 0
  --netid [3..15|18]    NETWORK ID. Note: PARAMETER values depend on NETWORK ID. Default: 18
  --parameter [7..11,7..9,1..4,4..24]
                        PARAMETER. Set the RF parameters Spreading Factor, Bandwidth, Coding Rate, Preamble. Spreading factor 7..11, default 9.
                        Bandwidth 7..9, where 7 is 125 KHz (only if spreading factor is in 7..9); 8 is 250 KHz (only if spreading factor is in
                        7..10); 9 is 500 KHz (only if spreading factor is in 7..11). Default bandwidth is 7. Coding rate is 1..4, default 4.
                        Preamble is 4..25 if the NETWORK ID is 18; otherwise the preamble must be 12. Default PARAMETER: 9,7,1,12

serial port config:
  --port [/dev/ttyS0-/dev/ttyS999]
                        Serial port device name. Default: /dev/ttyS0
  --baud (300|1200|4800|9600|19200|28800|38400|57600|115200)
                        Serial port baudrate. Default: 115200
```

## Python Module Dependencies

* python 3.9+
* rPI.GPIO
* [asyncio](https://pypi.org/project/asyncio/)
* [aioserial](https://pypi.org/project/aioserial/) 1.3.1+
* [curses](https://docs.python.org/3/library/curses.html) 

`pip install asyncio` and so on should work.

## GPIO connections for the Raspberry Pi

The GPIO connections are as follows:

* VDD to 3.3V physical pin 1 on the GPIO
* RST to GPIO 4, physical pin 7
* TXD to GPIO 15 RXD1 this is physical pin 10
* RXD to GPIO 14 TXD1 this is physical pin 8
* GND to GND physical pin 9.

**WARNING:** get this wrong and you could fry your Raspberry Pi 4 and your REYAX RYLR998 LoRa® module. I haven't had problems, knock wood, but the [MIT license](https://github.com/flengyel/RYLR998-LoRa/blob/main/LICENSE) comes with no warranty. Check your connections! Under no circumstances apply 5V to the RYLR998 LoRa® module. Only 3.3V. 

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

## Connection to a PC with a CP2102 USB 2.0 to TTL module serial converter
Similar to the GPIO, only VDD goes to the 3.3V output of the converter; RX and TX are swapped, as usual; and GND goes to GND.
See the pictures below.
![rylr998module](https://user-images.githubusercontent.com/431946/216791228-058dd28e-4c32-43dd-a351-1a0bd575dc06.jpg)


![CP2102_USB2_to_TTL_module_serial_converter](https://user-images.githubusercontent.com/431946/216791243-bd2dd829-fa44-45e2-9f36-a1b2585429bb.jpg)




## TO DO

* Add parsing of the AT+RESET function. 
* Display the configuration parameters. Mostly done, at startup. A VFO indicator would be nice. 
* Add function key handling for changing configuration parameters, such as frequency, netid, etc.
* But be careful about changing the serial port parameters--you'll be sorry! 
* The python urwid library could be used with the following initialization at  beginning of `xcvr(...)`:

```python
eloop = urwid.AsyncioEventLoop(loop=asyncio.get_event_loop())
uloop = urwid.MainLoop(widget, event_loop=eloop)
uloop.start() # main_loop.py suggests using this instead of run().
```

and immediately before `raise KeyboardInterrupt` within `xcvr(...)` call 

```python
uloop.stop()
```

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
* Screen output is not one character at a time. Instead of calling `refresh()` when a window changes, we call `win.noutrefresh()` and set a dirty bit. 
* If the dirty bit is set, `curses.doupdate()` is called and the dirty bit is reset. This is an optimization.
*  Serial port output cannot be one character at a time, since complete AT commands have to be sent to the RYLR998 through the serial port.
*  Receiving and parsing responses from AT commands takes precedence over sending AT commands, which includes sending text.

## References

Brownlee, J., Ph.D. (2022). [Python Asyncio Jump-Start: Asynchronous Programming And Non-Blocking I/O With Coroutines](https://superfastpython.com/python-asyncio-jump-start/) (Vol. 7, 7 vols., Python Concurrency Jump-Start Series). Retrieved January 22, 2023, from https://superfastpython.com/python-asyncio-jump-start/ ISBN-13 979-8361197620

[curses — Terminal handling for character-cell displays](https://docs.python.org/3/library/curses.html)

 "REYAX RYLR998 RYLR498 LoRa® AT COMMAND GUIDE" (c) 2021 REYAX TECHNOLOGY CO., LTD. Retrieved January 22, 2023, from https://reyax.com//upload/products_download/download_file/LoRa_AT_Command_RYLR998_RYLR498_EN.pdf

## Trademarks

The LoRa® Mark and Logo are trademarks of Semtech Corporation or its affiliates.

---

![REYAXRYLR988TwoWay](https://user-images.githubusercontent.com/431946/214753395-8db614de-1e25-42e7-bde6-571a45fcc902.gif)


This screenshot shows two MobaXTerm sessions running the `rlyr998.py` program in two  Raspberry Pi 4 Bs located at opposite ends of my living room. (The RYLR998 has a range in the tens of kilometers line-of-site.) Each Raspberry Pi has its own REYAX RYLR998 module connected as described below. The yellow text is that of the sender. The received text is magenta. When rylr998.py detects received text, the "LoRa" indicator flashes green if the message is long enough; transmission of text flashes the "LoRa" indicator red. The ADDR (address), RSSI and SNR values of the last received message are shown. Text messages are limited to 40 characters (in this version). 


## Disclaimer

This is a work in progress.  I'm taking my time adding IRC-like display functions with the Python curses library slowly and deliberately with all due sloth, so slowly that I would be fired and blacklisted if I were doing this professionally; flunked and expelled without a degree and a boatload of predatory private student loans at usurious interest rates if I were in college; and defunded and defrocked if I were an academician. I am not affiliated with Semtech Corporation.

