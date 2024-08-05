import os, sys
nombre = sys.argv[1]
os.system("rgbasm -o "+nombre+".o "+nombre+".asm")
os.system("rgblink -o "+nombre+".gb "+nombre+".o")
os.system("rgbfix -v -p 0xff "+nombre+".gb")