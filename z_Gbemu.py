import argparse, pygame, colorama
import os,sys
from tkinter import filedialog
from tkinter import Tk
def get_rom_tk():
    root= Tk()
    root.geometry('0x0')
    root.iconify()
    #root.overrideredirect(True)
    file_path = filedialog.askopenfilename()
    root.destroy()
    if not file_path:
        sys.exit()
    return file_path
def parse_arguments():
    parser = argparse.ArgumentParser(description='GB Emulator')
    parser.add_argument('rom', type=str, help='Path to the ROM file', default=get_rom_tk(), nargs="?")
    return parser.parse_args()
if __name__ == '__main__':
    from EmulatorCore import init
    pygame.init()
    colorama.init()
    os.environ["SDL_VIDEO_WINDOW_POS"] = "500,30"
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
    args = parse_arguments()
    print(args.rom)
    init(args)