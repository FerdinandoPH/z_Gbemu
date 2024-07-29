
import os, random
class Memory(bytearray):
    def __init__(self, size=0x10000):
        self.rom_protected=False
        super().__init__(size)
        for i in range(0,size):
            self[i]=random.randint(0,255)
        self.rom_protected=True
    def __setitem__(self, key, value):
        if self.rom_protected and key in range(0,0x8000):
            print("ROM write attempt")
            return
        super().__setitem__(key, value)
    def load_rom(self, path,mem_offset=0, rom_offset=0, length=0x8000):
        self.rom_protected=False
        with open(path, 'rb') as f:
            f.seek(rom_offset)
            self[mem_offset:mem_offset+length] = f.read(length)
        self.rom_protected=True
    def load_bios(self, path):
        self.load_rom(path,0,0,0x100)
    def show_memory(self):
        with open("gb_dump.hexd", 'wb') as f:
            f.write(self)
        os.system(os.path.dirname(os.path.realpath(__file__))+"\\gb_dump.hexd")