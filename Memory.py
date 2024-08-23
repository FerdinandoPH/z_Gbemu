
import os, random, copy, subprocess
class Memory(bytearray):
    def __init__(self, size=0x10000):
        self.protected=False
        self.div_changed=False
        self.tima_changed=False
        super().__init__(size)
        for i in range(0,size):
            self[i]=random.randint(0,255)
        #region initial_values
        self[0xFFFF] = 0x00
        self[0xFF0F] = 0x00
        self[0xFF00] = 0x00
        self[0xFF04] = 0x00
        self[0xFF05] = 0x00
        self[0xFF06] = 0x00
        self[0xFF07] = 0x00
        #endregion
        self.protected=True
    def __setitem__(self, key, value):
        if self.protected:
            if key in range(0,0x8000): 
                print(f"ROM write attempt ({hex(key)})")
                return
            elif key == 0xFF00: value = (0x3 << 6) | ((value & 0x30)>>4) | (self[0xFF00] & 0x0F)
            elif key == 0xFF04: 
                value = 0
                self.div_changed=True
            elif key == 0xFF05: self.tima_changed=True
        super().__setitem__(key, value)
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