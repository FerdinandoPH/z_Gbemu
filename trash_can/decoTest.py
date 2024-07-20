from miscutils import Mod_int
class Celsius:
    def __init__(self, temperature=0):
        self.temperature = temperature
        self.pc= Mod_int(0x100, 0x10000)
    def to_fahrenheit(self):
        return (self.temperature * 1.8) + 32

    @property
    def temperature(self):
        print("Getting value...")
        return self._temperature

    @temperature.setter
    def temperature(self, value):
        print("Setting value...")
        if value < -273.15:
            raise ValueError("Temperature below -273 is not possible")
        self._temperature = value
    @property
    def pc(self):
        return self._pc
    @pc.setter
    def pc(self, value):
        self._pc = Mod_int(value, 0x10000)


# create an object
human = Celsius(37)

print(human.temperature)

print(human.to_fahrenheit())
