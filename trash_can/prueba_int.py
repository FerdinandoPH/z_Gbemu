class Mod_int(int):
    def __new__(cls, value, mod):
        return super(Mod_int, cls).__new__(cls, value % mod)
    def __init__(self, value, mod):
        super().__init__()
        self.value=value % mod
        self.mod=mod
    def __get__(self, instance, owner):
        return self.value
    def __set__(self, instance, value):
        self.value = value % self.mod

mi_var=Mod_int(100, 256)
#mi_var = 257 # Quiero que, en vez de que mi_var se convierta en un int, permanezca como Mod_int y tenga el valor 1
print(mi_var) # Debería imprimir 1