def hex(num):
    if num>=0:
        return "0x"+format(num, 'X')
    return "-0x"+format(-num, 'X')
class Timers:
    def __init__(self, mem):
        self.mem = mem
        self.sub_tima = 0
        self.div = 0
        self.tima = 0
        self.tma = 0
        self.needed_cycles = {0: 256, 1: 4, 2: 16, 3: 64}
    @property
    def div(self):
        return self.mem[0xFF04]
    @div.setter
    def div(self, value):
        self.mem.protected = False
        self.mem[0xFF04] = value & 0xFF
        self.mem.protected = True
    @property
    def tma(self):
        return self.mem[0xFF06]

    @tma.setter
    def tma(self, value):
        self.mem.protected = False
        self.mem[0xFF06] = value & 0xFF
        self.mem.protected = True

    @property
    def tima(self):
        return self.mem[0xFF05]

    @tima.setter
    def tima(self, value):
        self.mem.protected = False
        self.mem[0xFF05] = value & 0xFF
        self.mem.protected = True

    @property
    def tac(self):
        return {"enabled": (self.mem[0xFF07] & 0b100)>>2, "clock": self.mem[0xFF07] & 0b11}

    @tac.setter
    def tac(self, value):
        self.mem.protected = False
        self.mem[0xFF07] = value & 0xFF
        self.mem.protected = True
    def tick(self, cycles):
        self.div += cycles
        if self.tac["enabled"]:
            self.sub_tima += cycles
            needed_cycles = self.needed_cycles[self.tac["clock"]]
            if self.sub_tima >= needed_cycles:
                add_to_tima = self.sub_tima // needed_cycles
                if self.tima + add_to_tima  > 0xFF:
                    self.tima = self.tma
                    self.mem[0xFF0F] |= 0b100
                else:
                    self.tima += add_to_tima
                self.sub_tima %= needed_cycles
    def __str__(self):
        return f"DIV: {hex(self.div)}, TMA: {hex(self.tma)}, TIMA: {hex(self.tima)}, TAC: {self.tac}"