from miscutils import Mod_int
a = Mod_int(100, 256)
a.set(200)
a+=55
for i in range(1,a.get()):
    print(i)