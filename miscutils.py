
# class Mod_int (int) :
#     def __new__(cls, value, mod):
#         return super(Mod_int, cls).__new__(cls, value % mod)
#     def __init__ (self, value, mod):
#         super().__init__()
#         self.value = value % mod
#         self.mod = mod
#     def __add__(self, other):
#         return Mod_int(self.value + (other.value if isinstance(other,Mod_int) else other) , self.mod)
#     def __sub__(self, other):
#         return Mod_int(self.value - (other.value if isinstance(other,Mod_int) else other), self.mod)
#     def __mul__(self, other):
#         return Mod_int(self.value * (other.value if isinstance(other,Mod_int) else other), self.mod)
#     def __truediv__(self, other):
#         return Mod_int(self.value // (other.value if isinstance(other,Mod_int) else other), self.mod)
#     def __mod__(self, other):
#         return Mod_int(self.value % (other.value if isinstance(other,Mod_int) else other), self.mod)
#     def __exp__(self, other):
#         return Mod_int(self.value ** (other.value if isinstance(other,Mod_int) else other), self.mod)
#     def __iadd__(self, other):
#         self.value += (other.value if isinstance(other,Mod_int) else other)
#         return self
#     def __isub__(self, other):
#         self.value -= (other.value if isinstance(other,Mod_int) else other)
#         return self
#     def __imul__(self, other):
#         self.value *= (other.value if isinstance(other,Mod_int) else other)
#         return self
#     def __itruediv__(self, other):
#         self.value //= (other.value if isinstance(other,Mod_int) else other)
#         return self
#     def __imod__(self, other):
#         self.value %= (other.value if isinstance(other,Mod_int) else other)
#         return self
#     def __iexp__(self, other):
#         self.value **= (other.value if isinstance(other,Mod_int) else other)
#         return self
#     def __neg__(self):
#         return Mod_int(-self.value, self.mod)
#     def __eq__(self, other):
#         return self.value == (other.value if isinstance(other,Mod_int) else other)
#     def __ne__(self, other):
#         return self.value != (other.value if isinstance(other,Mod_int) else other)
#     def __lt__(self, other):
#         return self.value < (other.value if isinstance(other,Mod_int) else other)
#     def __gt__(self, other):
#         return self.value > (other.value if isinstance(other,Mod_int) else other)
#     def __le__(self, other):
#         return self.value <= (other.value if isinstance(other,Mod_int) else other)
#     def __ge__(self, other):
#         return self.value >= (other.value if isinstance(other,Mod_int) else other)
#     def __hash__(self):
#         return hash(self.value)
#     def set(self, new_value):
#         self.value = new_value % self.mod
#         return self.value
#     def get(self):
#         return self.value
#     def __str__(self):
#         return str(self.value)
#     def __int__(self):
#         return self.value
#     def __float__(self):
#         return float(self.value)
#     def __index__(self):
#         return self.value
    
class Reg_dict(dict):
    def __getitem__(self, key):
        if key in ["AF", "BC", "DE", "HL"]:
            if key == "AF":
                return (super().__getitem__('A') << 8) | super().__getitem__('F')
            elif key == "BC":
                return (super().__getitem__('B') << 8) | super().__getitem__('C')
            elif key == "DE":
                return (super().__getitem__('D') << 8) | super().__getitem__('E')
            elif key == "HL":
                return (super().__getitem__('H') << 8) | super().__getitem__('L')
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        if key in ["AF", "BC", "DE", "HL"]:
            if value not in range(0, 0x10000):
                print(f"OV: {key} ({hex(value)})")
                value = value % 0x10000
            if key == "AF":
                super().__setitem__('A', value >> 8)
                super().__setitem__('F', value & 0xFF)
            elif key == "BC":
                super().__setitem__('B', value >> 8)
                super().__setitem__('C', value & 0xFF)
            elif key == "DE":
                super().__setitem__('D', value >> 8)
                super().__setitem__('E', value & 0xFF)
            elif key == "HL":
                super().__setitem__('H', value >> 8)
                super().__setitem__('L', value & 0xFF)
        else:
            if value not in range(0, 0x100):
                print(f"OV: {key} ({hex(value)})")
                value = value % 0x100
            if key == "F":
                value = value & 0xF0
            super().__setitem__(key, value)
class Flags_dict(dict):
    def __init__(self,start_dict,regs:Reg_dict):
        super().__init__(start_dict)
        self.regs=regs
    def __getitem__(self, key):
        if key in ["Z", "N", "H", "C"]:
            if key == "Z":
                return (self.regs["F"] & 0x80) >> 7
            elif key == "N":
                return (self.regs["F"] & 0x40) >> 6
            elif key == "H":
                return (self.regs["F"] & 0x20) >> 5
            else:
                return (self.regs["F"] & 0x10) >> 4
        return super().__getitem__(key)
    def __setitem__(self, key, value):
        if key in ["Z", "N", "H", "C"]:
            if key == "Z":
                self.regs["F"] = (self.regs["F"] & 0x7F) | (value << 7)
            elif key == "N":
                self.regs["F"] = (self.regs["F"] & 0xBF) | (value << 6)
            elif key == "H":
                self.regs["F"] = (self.regs["F"] & 0xDF) | (value << 5)
            else:
                self.regs["F"] = (self.regs["F"] & 0xEF) | (value << 4)
        else:
            super().__setitem__(key, value)