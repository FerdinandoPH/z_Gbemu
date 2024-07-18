from typing import Any


class Mod_int :
    def __init__ (self, value, mod):
        self.value = value % mod
        self.mod = mod
    def __add__(self, other):
        return Mod_int(self.value + (other.value if isinstance(other,Mod_int) else other) , self.mod)
    def __sub__(self, other):
        return Mod_int(self.value - (other.value if isinstance(other,Mod_int) else other), self.mod)
    def __mul__(self, other):
        return Mod_int(self.value * (other.value if isinstance(other,Mod_int) else other), self.mod)
    def __truediv__(self, other):
        return Mod_int(self.value // (other.value if isinstance(other,Mod_int) else other), self.mod)
    def __mod__(self, other):
        return Mod_int(self.value % (other.value if isinstance(other,Mod_int) else other), self.mod)
    def __exp__(self, other):
        return Mod_int(self.value ** (other.value if isinstance(other,Mod_int) else other), self.mod)
    def __iadd__(self, other):
        self.value += (other.value if isinstance(other,Mod_int) else other)
        return self
    def __isub__(self, other):
        self.value -= (other.value if isinstance(other,Mod_int) else other)
        return self
    def __imul__(self, other):
        self.value *= (other.value if isinstance(other,Mod_int) else other)
        return self
    def __itruediv__(self, other):
        self.value //= (other.value if isinstance(other,Mod_int) else other)
        return self
    def __imod__(self, other):
        self.value %= (other.value if isinstance(other,Mod_int) else other)
        return self
    def __iexp__(self, other):
        self.value **= (other.value if isinstance(other,Mod_int) else other)
        return self
    def __neg__(self):
        return Mod_int(-self.value, self.mod)
    def __eq__(self, other):
        return self.value == (other.value if isinstance(other,Mod_int) else other)
    def __ne__(self, other):
        return self.value != (other.value if isinstance(other,Mod_int) else other)
    def __lt__(self, other):
        return self.value < (other.value if isinstance(other,Mod_int) else other)
    def __gt__(self, other):
        return self.value > (other.value if isinstance(other,Mod_int) else other)
    def __le__(self, other):
        return self.value <= (other.value if isinstance(other,Mod_int) else other)
    def __ge__(self, other):
        return self.value >= (other.value if isinstance(other,Mod_int) else other)
    def set(self, new_value):
        self.value = new_value % self.mod
        return self.value
    def get(self):
        return self.value
    def __str__(self):
        return str(self.value)
    def __int__(self):
        return self.value
    def __float__(self):
        return float(self.value)