rgbasm hw.asm -o hw.o
rgblink hw.o -o hw.gb
rgbfix -v -p 0xff hw.gb