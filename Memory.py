
import os, random, copy, subprocess, colorama
class Memory(bytearray):
    def __init__(self, size=0x10000):
        self.div_changed=False
        self.tima_changed=False
        self.dma_active = False
        self.cpu = None
        self.dma_cycles = 0
        self.dma_progress = 0
        self.screen = None
        super().__init__(size)
        for i in range(0,size):
            self.write_unprotected(i, random.randint(0,255))
        #region initial_values

        self.write_unprotected(0xFFFF, 0x00) #IE
        self.write_unprotected(0xFF0F, 0x00) #IF
        self.write_unprotected(0xFF00, 0xCF) # Joypad
        self.write_unprotected(0xFF04, 0x00) # DIV
        self.write_unprotected(0xFF05, 0x00) # TIMA
        self.write_unprotected(0xFF06, 0x00) # TMA
        self.write_unprotected(0xFF07, 0x00) # TAC
        self.write_unprotected(0xFF46, 0xFF) # OAM DMA
        self.write_unprotected(0xFF40, 0x91) # LCDC
        self.write_unprotected(0xFF41, 0x81) # STAT
        self.write_unprotected(0xFF42, 0x00) # SCY
        self.write_unprotected(0xFF43, 0x00) # SCX
        self.write_unprotected(0xFF44, 0x91) # LY
        self.write_unprotected(0xFF45, 0x00) # LYC
        self.write_unprotected(0xFF47, 0xFC) # BGP
        self.write_unprotected(0xFF4A, 0x00) # WY
        self.write_unprotected(0xFF4B, 0x00) # WX
        #endregion
    def __getitem__(self, key, protected = True):
        if protected:
            if self.dma_active and key not in range(0xFF80,0xFFFF): 
                print(colorama.Fore.YELLOW+f"DMA active, read attempt to memory ({hex(key)}) at {hex(self.cpu.pc)}"+colorama.Style.RESET_ALL)
                return 0xFF
        return super().__getitem__(key)
    def __setitem__(self, key, value, protected = True):
        if protected:
            if key in range(0,0x8000): 
                print(colorama.Fore.YELLOW+f"ROM write attempt ({hex(key)}) at {hex(self.cpu.pc)}"+colorama.Style.RESET_ALL)
                return
            if self.dma_active and key not in range(0xFF80,0xFFFF): 
                print(colorama.Fore.YELLOW+f"DMA active, write attempt to memory ({hex(key)}) at {hex(self.cpu.pc)}"+colorama.Style.RESET_ALL)
                return
            match key:
                case 0xFF00: value = (0x3 << 6) | ((value & 0x30)>>4) | (self[0xFF00] & 0x0F) # Joypad
                case 0xFF04:  # DIV
                    value = 0
                    self.div_changed=True
                case 0xFF05: self.tima_changed=True # TIMA
                case 0xFF46: # OAM DMA
                    if value not in range(0,0xE0):
                        print(colorama.Fore.YELLOW+f"Invalid OAM DMA source ({hex(value)}) at {hex(self.cpu.pc)}"+colorama.Style.RESET_ALL)
                        return
                    self.dma_active = True
                case 0xFF40: # LCDC
                    if self.screen is not None:
                        value_list = [bool(int(i)) for i in format(value, '08b')]
                        self.screen.enabled = value_list[7]
                        self.screen.window_map_src = 0x9C00 if value_list[6] else 0x9800
                        self.screen.window_enabled = value_list[5]
                        self.screen.tile_src = 0x8000 if value_list[4] else 0x8800
                        self.screen.bg_map_src = 0x9C00 if value_list[3] else 0x9800
                        self.screen.sprite_height = 16 if value_list[2] else 8
                        self.screen.sprite_enabled = value_list[1]
                        self.screen.bg_window_enabled = value_list[0]
                case 0xFF41: # STAT
                    value &= 0b11111000
                    value |= self[0xFF41] & 0b111
            if key in {0xFF44}: #Read only values: LY, 
                print(colorama.Fore.YELLOW+f"Write attempt to read only memory ({hex(key)}) at {hex(self.cpu.pc)}"+colorama.Style.RESET_ALL)
                return
        super().__setitem__(key, value)
    def dma_tick(self, cycles):

        self.dma_cycles = min(159, self.dma_cycles + cycles)
        #self.__setitem__(0xFE00 + self.dma_progress: 0xFE00 + self.dma_cycles, self[(self[0xFF46] << 8) + self.dma_progress: (self[0xFF46] << 8) + self.dma_cycles], False)
        for i in range(self.dma_progress, self.dma_cycles):
            self.write_unprotected(0xFE00 + i, self.read_unprotected((self.read_unprotected(0xFF46)<<8)+i))#self[(self[0xFF46] << 8) + i])
        self.dma_progress = self.dma_cycles
        if self.dma_cycles >= 159:
            self.dma_active = False
            self.dma_cycles = 0
            self.dma_progress = 0
    def write_unprotected(self, key, value):
        self.__setitem__(key, value, False)
    def read_unprotected(self, key):
        return self.__getitem__(key, False)
    def load_rom(self, path,mem_offset=0, rom_offset=0, length=0x8000):
        with open(path, 'rb') as f:
            f.seek(rom_offset)
            for i in range(mem_offset,mem_offset+length):
                self.write_unprotected(i, f.read(1)[0])
    def load_bios(self, path):
        self.load_rom(path,0,0,0x100)
    def show_memory(self):
        with open("gb_dump.hexd", 'wb') as f:
            f.write(self)
        #os.system(os.path.dirname(os.path.realpath(__file__))+"\\gb_dump.hexd")
        subprocess.Popen([os.path.dirname(os.path.realpath(__file__))+"\\gb_dump.hexd"], shell=True)
    def str_info(self):
        return "" if not self.dma_active else f"DMA Active ({self.dma_progress}/159)\n"