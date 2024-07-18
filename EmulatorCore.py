from .Cpu import Cpu
from .Memory import Memory
cpu = Cpu()
memory = Memory()
def init(args):
    memory.load_rom(args.rom)
    main_loop(args)
def main_loop(args):
    while True:
        cpu.tick()