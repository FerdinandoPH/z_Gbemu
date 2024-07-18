
class Memory:
    def __init__(self):
        self.memory = bytearray(0xFFFF)
    def load_rom(self, path,mem_offset=0, rom_offset=0, length=0x8000):
        with open(path, 'rb') as f:
            f.seek(rom_offset)
            self.memory[mem_offset:mem_offset+length] = f.read(length)
    def load_bios(self, path):
        self.load_rom(path,0,0,0x100)
        