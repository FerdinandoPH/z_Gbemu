from Memory import Memory
from miscutils import Reg_dict
class Cpu:
    def __init__(self, memory, debug_level=0):
        self.registers= Reg_dict([("A",0),("F",0),("B",0),("C",0),("D",0),("E",0),("H",0),("L",0),("AF",0),("BC",0),("DE",0),("HL",0)])
        self.pc = 0x100
        self.sp = 0xFEEE
        self.instruction = 0
        self.get_name=False
        self.mem= memory
        self.running=True
        #region opcode_dict
        self.opcode_table={
            0x0: self.NOP,
            0x10: self.STOP,
            #**{i:self.ld_16 for i in set(range(0x1,0x41,0x10)) | {0x8} | set.union(*[{i,i+4} for i in range (0xC1,0x101,0x10)]) | {0xF8, 0xF9}},
            **{i:self.LD_8 for i in set(range(2,64,4)) | set(range(0x40,0x80)) - {0x76} | {0xE0, 0xE2, 0xEA, 0xF0, 0xF2, 0xFA}},
            **{i:self.pc_change for i in {0x18, 0x20, 0x28, 0x30, 0x38} | {0xC2, 0xC3, 0xCA, 0xD2, 0xDA} | {0xC4, 0xCC, 0xCD, 0xD4, 0xDC} | {0xC0, 0xC8, 0xC9, 0xD0, 0xD8, 0xD9} | set(range(0xC7, 0x100, 0x8))},
            0x76:self.HALT,
            **{i:self.empty_opcode for i in {0xD3, 0xDB, 0xDD, 0xE3, 0xE4, 0xEB, 0xEC, 0xED, 0xF4, 0xFC, 0xFD}}
        }

        self.changes_pc_table={
            #0x18:self.jr_e8,
            #**{i:self.jr_cond_e8 for i in set(range(0x20,0x40,0x8))},
            0xC3:self.jp_a16,
            #**{i:self.jp_cond_a16 for i in set(range(0xC2,0xE2,0x8))},
            #0xE9:self.jp_hl,
            #0xCD:self.call_a16,
            #**{i:self.call_cond_a16 for i in set(range(0xC4,0xE4,0x8))},
            #0xC9:self.ret,
            #**{i:self.ret_cond for i in set(range(0xC0,0xE0,0x8))},
            #**{i:self.rst for i in set(range(0xC7,0x100,0x8))}
        }
        #endregion
        #region LD_8_dict
        self.ld_8_table={
            **{i:self.ld_8_n8 for i in set(range(0x06,0x3F,0x8))-{0x36}},
            #**{i:self.ld_8_r8_r8 for i in set(range(0x40,0x80)) - set(range(0x46,0x7F,0x8)) - set(range(0x70,0x78))},
            #**{i:self.ld_8_reg_mem for i in set(range(0x2,0x42,0x10)) | {0x36} | set(range(0x70,0x78)) - {0x76} | {0xE0, 0xE2, 0xEA}},
            #**{i:self.ld_8_mem_reg for i in set(range(0xA,0x4A,0x10)) | set(range(0x46, 0x7F, 0x8)) - {0x76} | {0xF0, 0xF2, 0xFA}}
        }
        self.ld_8_n8_table={0x06: "B", 0x0E: "C", 0x16: "D", 0x1E: "E", 0x26: "H", 0x2E: "L", 0x3E: "A"}
        #endregion
    def tick(self):
        self.instruction=self.mem.memory[self.pc]
        self.pc+=1
        try:
            self.opcode_table[self.instruction]()
        except KeyError:
            self.unimplemented_opcode()
    def __str__(self):
        old_instruction=self.instruction
        self.instruction=self.mem.memory[self.pc]
        self.get_name=True
        ret_value = "Registers: "+str([f"{i}:{hex(self.registers[i])} " for i in self.registers])+"\nPC: "+hex(self.pc)+"\nSP: "+hex(self.sp)+"\nInstruction: "# + hex(self.instruction) + " "
        old_pc = self.pc
        self.pc+=1
        ret_value+=self.opcode_table[self.instruction]()
        self.pc = old_pc
        self.get_name=False
        self.instruction=old_instruction
        return ret_value
    #region opcodes
    #region misc
    def NOP(self):
        '''
        0x00: NOP
        1 byte, 1 cycle, no flags
        No operation. Do nothing for one machine cycle. Increment the PC afterwards
        '''
        if self.get_name: return "NOP"
        self.pc+=1
    def STOP(self):
        '''
        0x10: STOP
        2 bytes, ? cycles, no flags
        Halt CPU and LCD until button press. Increment the PC by 2 afterwards
        '''
        if self.get_name: return "STOP"
        #not implemented yet
        self.pc+=1
    def HALT(self):
        '''
        0x76: HALT
        1 byte, ? cycles, no flags
        Halt CPU until an interrupt occurs. Increment the PC afterwards
        If the IME is set, the handler will be called. Otherwise, it depends on whether there is an interrupt pending. 
        
        If there isn't, the CPU will be halted until an interrupt occurs, where the CPU will resume its work, but won't handle the interrupt until the next instruction is executed. 
        
        If there is an interrupt pending, the CPU will continue execution, but it will read the next byte twice due to a bug
        '''
        if self.get_name: return "HALT"
        #not implemented yet
        self.pc+=1
    def empty_opcode(self):
        '''
        This opcode doesn't map to any instruction, so if this is the next opcode, something has gone wrong
        '''
        if self.debug_level<2 or self.get_name: return "???"
        self.running=False
    def unimplemented_opcode(self):
        if self.get_name: return "unimpl"
        print("Oops, haven't got around to implementing this opcode yet")
        #for now, let's skip to the next instruction
        self.pc+=1
    #endregion
    #region LD_8
    def LD_8(self):
        '''
        This function triages the different LD_8 instructions
        '''
        if self.get_name: return "LD_8 "+ self.ld_8_table[self.instruction]()
        try:
            return self.ld_8_table[self.instruction]()
        except KeyError:
            self.unimplemented_opcode()
    def ld_8_n8(self):
        '''
        0x06 (B), 0x0E (C), 0x16 (D), 0x1E (E), 0x26 (H), 0x2E (L), 0x3E (A): LD_8 r8, n8
        Loads an 8-bit immediate value into a register
        2 bytes, 2 cycles, no flags
        '''
        if self.get_name: return self.ld_8_n8_table[self.instruction]+", #"+hex(self.mem.memory[self.pc])
        self.registers[self.ld_8_n8_table[self.instruction]] = self.mem.memory[self.pc]
        self.pc+=1
    #endregion
    #region pc_change
    def pc_change(self):
        '''
        This function triages the different PC change instructions
        '''
        try:
             return self.changes_pc_table[self.instruction]()
        except KeyError:
            self.unimplemented_opcode()
    def jp_a16(self):
        '''
        0xC3: JP a16
        Jump to a 16-bit immediate address
        3 bytes, 4 cycles, no flags
        '''
        if self.get_name: return "JP #"+hex(self.mem.memory[self.pc+1] << 8 | self.mem.memory[self.pc])
        self.pc = self.mem.memory[self.pc+1] << 8 | self.mem.memory[self.pc]
    #endregion

    #endregion