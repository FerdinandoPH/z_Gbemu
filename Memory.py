
import os
class Memory:
    def __init__(self):
        self.memory = bytearray(0x10000)
    def load_rom(self, path,mem_offset=0, rom_offset=0, length=0x8000):
        with open(path, 'rb') as f:
            f.seek(rom_offset)
            self.memory[mem_offset:mem_offset+length] = f.read(length)
    def load_bios(self, path):
        self.load_rom(path,0,0,0x100)
    def show_memory(self):
        with open("gb_dump.hexd", 'wb') as f:
            f.write(self.memory)
        os.system(os.path.dirname(os.path.realpath(__file__))+"\\gb_dump.hexd")