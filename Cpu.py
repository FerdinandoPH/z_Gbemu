from Memory import Memory
from miscutils import Reg_dict, Flags_dict
class Cpu:
    def __init__(self, memory, debug_level=0):
        self.registers= Reg_dict([("A",0),("F",0),("B",0),("C",0),("D",0),("E",0),("H",0),("L",0),("AF",0),("BC",0),("DE",0),("HL",0)])
        self.flags=Flags_dict([("Z",0),("N",0),("H",0),("C",0)], self.registers)
        self.pc = 0x100
        self.sp = 0xFEEE
        self.instruction = 0
        self.get_name=False
        self.mem= memory
        self.running=True
        self.add_to_pc = 0
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
            **{i:self.ld_8_r8_r8 for i in set(range(0x40,0x80)) - set(range(0x46,0x7F,0x8)) - set(range(0x70,0x78))},
            #**{i:self.ld_8_reg_mem for i in set(range(0x2,0x42,0x10)) | {0x36} | set(range(0x70,0x78)) - {0x76} | {0xE0, 0xE2, 0xEA}},
            **{i:self.ld_8_mem_r8 for i in set(range(0xA,0x4A,0x10)) | set(range(0x46, 0x7F, 0x8)) - {0x76} | {0xF0, 0xF2, 0xFA}}
        }
        self.ld_8_n8_table={0x06: "B", 0x0E: "C", 0x16: "D", 0x1E: "E", 0x26: "H", 0x2E: "L", 0x3E: "A"}
        #region ld_8_r8_r8
        self.ld_8_r8_r8_table={}
        self.ld_8_r8_r8_table["dest"]={
            **{i:"B" for i in set(range(0x40,0x48)) - {0x46}},
            **{i:"C" for i in set(range(0x48,0x50)) - {0x4E}},
            **{i:"D" for i in set(range(0x50,0x58)) - {0x56}},
            **{i:"E" for i in set(range(0x58,0x60)) - {0x5E}},
            **{i:"H" for i in set(range(0x60,0x68)) - {0x66}},
            **{i:"L" for i in set(range(0x68,0x70)) - {0x6E}},
            **{i:"A" for i in set(range(0x78,0x80)) - {0x7E}}
        }
        self.ld_8_r8_r8_table["src"]={
            **{i:"B" for i in set(range(0x40,0x80, 0x8)) - {0x70}},
            **{i:"C" for i in set(range(0x41,0x81, 0x8)) - {0x71}},
            **{i:"D" for i in set(range(0x42,0x82, 0x8)) - {0x72}},
            **{i:"E" for i in set(range(0x43,0x83, 0x8)) - {0x73}},
            **{i:"H" for i in set(range(0x44,0x84, 0x8)) - {0x74}},
            **{i:"L" for i in set(range(0x45,0x85, 0x8)) - {0x75}},
            **{i:"A" for i in set(range(0x47,0x87, 0x8)) - {0x77}}
        }
        #endregion
        self.ld_8_r8_mem_table={"src":{0x0A: "BC", 0x1A: "DE", **{i:"HL" for i in set(range(0x46, 0x7F, 0x8)) - {0x76} | {0x2A, 0x3A}}, 0xF0: "a8", 0xF2: "C", 0xFA: "a16"}, "dest":{**{i:"A" for i in set(range(0x0A, 0x4A, 0x10)) | {0x7E, 0xF0, 0xF2, 0xFA}}, 0x46: "B", 0x4E: "C", 0x56: "D", 0x5E: "E", 0x66: "H", 0x6E: "L"}}
        #endregion
    def tick(self):
        if self.running:
            self.instruction=self.mem.memory[self.pc]
            self.pc = (self.pc + 1) % 0x10000 # For some reason, the PC is incremented before the instruction is executed. This is important for relative jumps
            self.add_to_pc = 0
            try:
                ret_value =  self.opcode_table[self.instruction]()
            except KeyError:
                ret_value =  self.unimplemented_opcode()
            self.pc = (self.pc + self.add_to_pc) % 0x10000
            return ret_value
    def __str__(self):
        old_instruction=self.instruction
        self.get_name=True
        ret_value = "Registers: "+str([f"{i}:{hex(self.registers[i])} " for i in self.registers])+"\nFlags:"+str(self.flags)+"\nPC: "+hex(self.pc)+"  SP: "+hex(self.sp)+"\nInstruction: "# + hex(self.instruction) + " "
        old_pc = self.pc
        ret_value+= self.tick()
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
        No operation. Do nothing for one machine cycle
        '''
        if self.get_name: return "NOP"
    def STOP(self):
        '''
        0x10: STOP
        2 bytes, ? cycles, no flags
        Halt CPU and LCD until button press. Increment the PC afterwards
        '''
        if self.get_name: return "STOP"
        #not implemented yet
        self.add_to_pc = 1
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
    def empty_opcode(self):
        '''
        This opcode doesn't map to any instruction, so if this is the next opcode, something has gone wrong
        '''
        if self.debug_level<2 or self.get_name: return "???"
        self.running=False
    def unimplemented_opcode(self):
        if self.get_name: return "unimpl ("+hex(self.instruction)+")"
        print("Oops, haven't got around to implementing this opcode yet")
        #for now, let's skip to the next instruction
    #endregion
    #region LD_8
    def LD_8(self):
        '''
        This function triages the different LD_8 instructions
        '''
        try:
            return ("LD_8 "+ self.ld_8_table[self.instruction]()) if self.get_name else self.ld_8_table[self.instruction]()
        except KeyError:
            return self.unimplemented_opcode()
    def ld_8_n8(self):
        '''
        LD_8 r8, n8
        Loads an 8-bit immediate value into a register
        2 bytes, 2 cycles, no flags
        Opcodes: 0x06 (B), 0x0E (C), 0x16 (D), 0x1E (E), 0x26 (H), 0x2E (L), 0x3E (A)
        '''
        if self.get_name: return self.ld_8_n8_table[self.instruction]+", #"+hex(self.mem.memory[self.pc])
        self.registers[self.ld_8_n8_table[self.instruction]] = self.mem.memory[self.pc]
        self.add_to_pc = 1
    def ld_8_r8_r8(self):
        '''
        LD_8 r8, r8
        Loads the value of one register into another
        1 byte, 1 cycle, no flags
        Opcodes: 0x40 (B->B), 0x41 (B->C), 0x42 (B->D), 0x43 (B->E), 0x44 (B->H), 0x45 (B->L), 0x47 (B->A), 0x48 (C->B), 0x49 (C->C), 0x4A (C->D), 0x4B (C->E), 0x4C (C->H), 0x4D (C->L), 0x4F (C->A), 0x50 (D->B), 0x51 (D->C), 0x52 (D->D), 0x53 (D->E), 0x54 (D->H), 0x55 (D->L), 0x57 (D->A), 0x58 (E->B), 0x59 (E->C), 0x5A (E->D), 0x5B (E->E), 0x5C (E->H), 0x5D (E->L), 0x5F (E->A), 0x60 (H->B), 0x61 (H->C), 0x62 (H->D), 0x63 (H->E), 0x64 (H->H), 0x65 (H->L), 0x67 (H->A), 0x68 (L->B), 0x69 (L->C), 0x6A (L->D), 0x6B (L->E), 0x6C (L->H), 0x6D (L->L), 0x6F (L->A), 0x78 (A->B), 0x79 (A->C), 0x7A (A->D), 0x7B (A->E), 0x7C (A->H), 0x7D (A->L), 0x7F (A->A)
        '''
        if self.get_name: return self.ld_8_r8_r8_table["dest"][self.instruction]+", "+self.ld_8_r8_r8_table["src"][self.instruction]
        self.registers[self.ld_8_r8_r8_table["dest"][self.instruction]] = self.registers[self.ld_8_r8_r8_table["src"][self.instruction]]
    def ld_8_mem_r8(self):
        '''
        LD_8 r8, [mem]
        Different instructions that load a value from memory into a register
        *1: 1 byte, 2 cycles, no flags
        *2: 2 bytes, 3 cycles, no flags
        *3: 3 bytes, 4 cycles, no flags
        0x0A: LD A, [BC] (*1), 0x1A: LD A, [DE] (*1), 0x46: LD B, [HL] (*1), 0x4E: LD C, [HL] (*1), 0x56: LD D, [HL] (*1), 0x5E: LD E, [HL] (*1), 0x66: LD H, [HL] (*1), 0x6E: LD L, [HL] (*1), 0x7E: LD A, [HL] (*1), 0xF0: LD A, [a8] (*2), 0xF2: LD A, [C] (*1), 0xFA: LD A, [a16] (*3)
        '''
        src = self.ld_8_r8_mem_table["src"][self.instruction]
        is_imm = src in ["a8", "a16"]
        if src == "a8":
            src = self.mem.memory[self.pc]
            self.add_to_pc = 1
        elif src == "a16":
            src = self.mem.memory[self.pc] << 8 | self.mem.memory[self.pc+1]
            self.add_to_pc = 2
        if self.get_name: return self.ld_8_r8_mem_table["dest"][self.instruction]+", ["+("$FF00+"if self.instruction in {0xF0,0xF2} else "")+src+("+" if self.instruction == 0x2A else "-" if self.instruction == 0x3A else "")+"]"
        if not is_imm:
            src = self.mem.memory[self.registers[src]]
        if self.instruction in {0xF0, 0xF2}: src = 0xFF00 + src
        self.registers[self.ld_8_r8_mem_table["dest"][self.instruction]] = src
        if self.instruction in {0x2A, 0x3A}: self.registers[self.ld_8_r8_mem_table["src"][self.instruction]] = (self.registers[self.ld_8_r8_mem_table["src"][self.instruction]]+ (1 if self.instruction == 0x2A else -1)) % 0x10000
    #endregion
    #region pc_change
    def pc_change(self):
        '''
        This function triages the different PC change instructions
        '''
        try:
            return self.changes_pc_table[self.instruction]()
        except KeyError:
            return self.unimplemented_opcode()
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