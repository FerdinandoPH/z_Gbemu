from .Memory import Memory
from .miscutils import Mod_int
class Cpu:
    def __init__(self):
        self.registers= {'A':Mod_int(0, 2**8), 'B':Mod_int(0, 2**8), 'C':Mod_int(0, 2**8), 'D':Mod_int(0, 2**8), 'E':Mod_int(0, 2**8), 'F':Mod_int(0, 2**8), 'H':Mod_int(0, 2**8), 'L':Mod_int(0, 2**8)}
        self.pc = Mod_int(0x100, 2**16)
        self.sp = Mod_int(0xFEEE, 2**16)
        self.instruction = 0
        self.memory= Memory()
        self.debug_level = 0
        self.running=True
        self.opcode_table={
            {0x0}: self.NOP,
            {0x10}: self.STOP,
            set(range(0x1,0x41,0x10)) | {0x8} | set.union(*[{i,i+4} for i in range (0xC1,0x101,0x10)]) | {0xF8, 0xF9}:self.ld_16,
            set(range(2,64,4)) | set(range(0x40,0x80)) - {0x76} | {0xE0, 0xE2, 0xEA, 0xF0, 0xF2, 0xFA}:self.LD_8,
            {0x18, 0x20, 0x28, 0x30, 0x38} | {0xC2, 0xC3, 0xCA, 0xD2, 0xDA} | {0xC4, 0xCC, 0xCD, 0xD4, 0xDC} | {0xC0, 0xC8, 0xC9, 0xD0, 0xD8, 0xD9} | set(range(0xC7, 0x100, 0x8)):self.pc_change,
            {0x76}:self.HALT,
            {0xD3, 0xDB, 0xDD, 0xE3, 0xE4, 0xEB, 0xEC, 0xED, 0xF4, 0xFC, 0xFD}:self.empty_opcode
        }
        self.ld_8_table={
            set(range(0x06,0x3F,0x8))-{0x36}:self.ld_8_n8,
            set(range(0x40,0x80)) - set(range(0x46,0x7F,0x8)) - set(range(0x70,0x78)):self.ld_8_reg_reg,
            set(range(0x2,0x42,0x10)) | {0x36} | set(range(0x70,0x78)) - {0x76} | {0xE0, 0xE2, 0xEA}:self.ld_8_reg_mem,
            set(range(0xA,0x4A,0x10)) | set(range(0x46, 0x7F, 0x8)) - {0x76} | {0xF0, 0xF2, 0xFA}:self.ld_8_mem_reg
        }
        self.changes_pc_table={
            {0x18}: self.jr_e8,
            set(range(0x20,0x40,0x8)): self.jr_cond,

        }
    def tick(self):
        pass
    def NOP(self):
        '''
        0x00: NOP
        1 byte, 1 cycle
        No operation. Do nothing for one machine cycle. Increment the PC afterwards
        '''
        if (self.debug_level==0):
            print("NOP")
        self.pc+=1
    def STOP(self):
        '''
        0x10: STOP
        2 bytes, ? cycles
        Halt CPU and LCD until button press. Increment the PC by 2 afterwards
        '''
        if (self.debug_level==0):
            print("STOP")
        #not implemented yet
        self.pc+=1
    def HALT(self):
        '''
        0x76: HALT
        1 byte, ? cycles
        Halt CPU until an interrupt occurs. Increment the PC afterwards
        If the IME is set, the handler will be called. Otherwise, it depends on whether there is an interrupt pending. 
        
        If there isn't, the CPU will be halted until an interrupt occurs, where the CPU will resume its work, but won't handle the interrupt until the next instruction is executed. 
        
        If there is an interrupt pending, the CPU will continue execution, but it will read the next byte twice due to a bug
        '''
        if (self.debug_level==0):
            print("HALT")
        #not implemented yet
        self.pc+=1
    def empty_opcode(self):
        '''
        This opcode doesn't map to any instruction, so if this is the next opcode, something has gone wrong
        '''
        if (self.debug_level<2):
            print("Invalid opcode")
        self.running=False
    def unimplemented_opcode(self):
        print("Oops, haven't got around to implementing this opcode yet")
        #for now, let's skip to the next instruction
        self.pc+=1
    def LD_8(self):
        '''
        This function triages the different LD_8 instructions
        '''
        if (self.debug_level==0):
            print("LD 8 ")
        self.pc+=1