
import os, random, copy, subprocess
class Memory(bytearray):
    def __init__(self, size=0x10000):
        self.protected=False
        self.div_changed=False
        self.tima_changed=False
        self.dma_active = False
        self.dma_cycles = 0
        self.dma_progress = 0
        self.screen = None
        super().__init__(size)
        for i in range(0,size):
            self[i]=random.randint(0,255)
        #region initial_values
        self[0xFFFF] = 0x00 #IE
        self[0xFF0F] = 0x00 #IF
        self[0xFF00] = 0xCF # Joypad
        self[0xFF04] = 0x00 # DIV
        self[0xFF05] = 0x00 # TIMA
        self[0xFF06] = 0x00 # TMA
        self[0xFF07] = 0x00 # TAC
        self[0xFF46] = 0xFF # OAM DMA
        self[0xFF40] = 0x91 # LCDC
        self[0xFF41] = 0x81 # STAT
        self[0xFF42] = 0x00 # SCY
        self[0xFF43] = 0x00 # SCX
        self[0xFF44] = 0x91 # LY
        self[0xFF45] = 0x00 # LYC
        self[0xFF47] = 0xFC # BGP
        self[0xFF4A] = 0x00 # WY
        self[0xFF4B] = 0x00 # WX
        #endregion
        self.protected=True
    def __getitem__(self, key):
        if self.protected:
            if self.dma_active and key not in range(0xFF80,0xFFFF): 
                print(f"DMA active, read attempt to memory ({hex(key)})")
                return 0xFF
        return super().__getitem__(key)
    def __setitem__(self, key, value):
        if self.protected:
            if key in range(0,0x8000): 
                print(f"ROM write attempt ({hex(key)})")
                return
            if self.dma_active and key not in range(0xFF80,0xFFFF): 
                print(f"DMA active, write attempt to memory ({hex(key)})")
                return
            match key:
                case 0xFF00: value = (0x3 << 6) | ((value & 0x30)>>4) | (self[0xFF00] & 0x0F) # Joypad
                case 0xFF04:  # DIV
                    value = 0
                    self.div_changed=True
                case 0xFF05: self.tima_changed=True # TIMA
                case 0xFF46: # OAM DMA
                    if value not in range(0,0xE0):
                        print(f"Invalid OAM DMA source ({hex(value)})")
                        return
                    self.dma_active = True
                    base_addr = value << 8
                    for byte in range(0,0xA0):
                        self[0xFE00+byte] = self[base_addr+byte]
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
            if key in {0xFF44}: #Read only values: LY, 
                print(f"Write attempt to read only memory ({hex(key)})")
                return
        super().__setitem__(key, value)
    def dma_tick(self, cycles):
        self.protected=False
        self.dma_cycles = max(159, self.dma_cycles + cycles)
        self[0xFE00 + self.dma_progress: 0xFE00 + self.dma_cycles] = self[(self[0xFF46] << 8) + self.dma_progress: (self[0xFF46] << 8) + self.dma_cycles]
        self.dma_progress = self.dma_cycles
        if self.dma_cycles >= 159:
            self.dma_active = False
            self.dma_cycles = 0
            self.dma_progress = 0
        self.protected=True
    def write_unprotected(self, key, value):
        self.protected=False
        self.__setitem__(key, value)
        self.protected=True
    def load_rom(self, path,mem_offset=0, rom_offset=0, length=0x8000):
        self.protected=False
        with open(path, 'rb') as f:
            f.seek(rom_offset)
            self[mem_offset:mem_offset+length] = f.read(length)
        self.protected=True
    def load_bios(self, path):
        self.load_rom(path,0,0,0x100)
    def show_memory(self):
        with open("gb_dump.hexd", 'wb') as f:
            f.write(self)
        #os.system(os.path.dirname(os.path.realpath(__file__))+"\\gb_dump.hexd")
        subprocess.Popen([os.path.dirname(os.path.realpath(__file__))+"\\gb_dump.hexd"], shell=True)
    def __deepcopy__(self, memo):
        # Crear una nueva instancia sin llamar a __init__
        new_instance = self.__class__.__new__(self.__class__)
        # Copiar los atributos del objeto original a la nueva instancia
        memo[id(self)] = new_instance
        for k, v in self.__dict__.items():
            setattr(new_instance, k, copy.deepcopy(v, memo))
        # Copiar el contenido del bytearray
        super(Memory, new_instance).__init__(self)
        return new_instance