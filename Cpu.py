from Memory import Memory
from miscutils import Reg_dict, Flags_dict
def hex(num):
    if num>=0:
        return "0x"+format(num, 'X')
    return "-0x"+format(-num, 'X')
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
        self.add_to_sp = 0
        self.cycles = 0 #unused for now
        self.flag_nomenclature = {"Z": "bool(self.flags[\"Z\"])", "N": "bool(self.flags[\"N\"])", "H": "bool(self.flags[\"H\"])", "C": "bool(self.flags[\"C\"])", "NZ": "not bool(self.flags[\"Z\"])", "NC": "not bool(self.flags[\"C\"])", "NN": "not bool(self.flags[\"N\"])", "NH": "not bool(self.flags[\"H\"])", "True": "True", "False": "False"}
        #region opcode_dict
        self.opcode_table={
            0x0: self.NOP, 0x10: self.STOP, **{i:self.LD_8 for i in set(range(2,64,4)) | set(range(0x40,0x80)) - {0x76} | {0xE0, 0xE2, 0xEA, 0xF0, 0xF2, 0xFA}}, **{i:self.pc_change for i in {0x18, 0x20, 0x28, 0x30, 0x38} | {0xC2, 0xC3, 0xCA, 0xD2, 0xDA} | {0xC4, 0xCC, 0xCD, 0xD4, 0xDC} | {0xC0, 0xC8, 0xC9, 0xD0, 0xD8, 0xD9} | set(range(0xC7, 0x100, 0x8))}, 0x76:self.HALT, **{i:self.empty_opcode for i in {0xD3, 0xDB, 0xDD, 0xE3, 0xE4, 0xEB, 0xEC, 0xED, 0xF4, 0xFC, 0xFD}}, **{i:self.cp for i in set(range(0xB8,0xC0)) | {0xFE}}}#**{i:self.ld_16 for i in set(range(0x1,0x41,0x10)) | {0x8} | set.union(*[{i,i+4} for i in range (0xC1,0x101,0x10)]) | {0xF8, 0xF9}},
        #endregion
        #region pc_change_dict
        self.pc_change_table={"new_pc":{**{i:"e8" for i in set(range(0x20,0x40,0x8)) | {0x18}}, **{i:"a16" for i in set(range(0xC2,0xE2,0x8)) | {0xC3, 0xCD} | set(range(0xC4,0xE4,0x8))}, 0xE9:"HL", **{i:"SP" for i in set(range(0xC0,0xE0,0x8)) | {0xC9, 0xD9}}, **{i:i-0xC7 for i in set(range(0xC7,0x100,0x8))}}, "cond":{**{i: "True" for i in {0x18, 0xC3, 0xCD, 0xE9, 0xC9} | set(range(0xC7,0x100,0x8))}, **{i: "NZ" for i in {0x20, 0xC0, 0xC2, 0xC4}}, **{i: "Z" for i in {0x28, 0xC8, 0xCA, 0xCC}}, **{i: "NC" for i in {0x30, 0xD0, 0xD2, 0xD4}}, **{i: "C" for i in {0x38, 0xD8, 0xDA, 0xDC}}}, "name": {**{i:"JR" for i in set(range(0x20,0x40,0x8)) | {0x18}}, **{i: "JP" for i in set(range(0xC2,0xE2,0x8)) | {0xC3, 0xE9}}, **{i:"CALL" for i in set(range(0xC4,0xE4,0x8)) | {0xCD}}, **{i:"RET" for i in set(range(0xC0,0xE0,0x8)) | {0xC9, 0xD9}}, **{i:"RST" for i in set(range(0xC7,0x100,0x8))}}}
        #endregion
        #region LD_8_dict
        self.ld_8_table={
            **{i:self.ld_8_n8 for i in set(range(0x06,0x3F,0x8))-{0x36}},
            **{i:self.ld_8_r8_r8 for i in set(range(0x40,0x80)) - set(range(0x46,0x7F,0x8)) - set(range(0x70,0x78))},
            **{i:self.ld_8_mem_r8 for i in set(range(0x2,0x42,0x10)) | {0x36} | set(range(0x70,0x78)) - {0x76} | {0xE0, 0xE2, 0xEA}},
            **{i:self.ld_8_r8_mem for i in set(range(0xA,0x4A,0x10)) | set(range(0x46, 0x7F, 0x8)) - {0x76} | {0xF0, 0xF2, 0xFA}}
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
        self.ld_8_mem_r8_table={"src":{**{i:"A" for i in set(range(0x02,0x42,0x10))|{0x77, 0xE0, 0xE2, 0xEA}}, 0x70:"B", 0x71:"C", 0x72:"D", 0x73:"E", 0x74:"H", 0x75:"L",0x36:"n8"}, "dest":{0x02:"BC", 0x12:"DE", **{i:"HL" for i in set(range(0x70, 0x78)) - {0x76} | {0x22, 0x32, 0x36}}, 0xE0: "a8", 0xE2: "C", 0xEA: "a16"}}
        #endregion
        #region cp_dict
        self.cp_src_table={0xB8:"B", 0xB9:"C", 0xBA:"D", 0xBB:"E", 0xBC:"H", 0xBD:"L", 0xBE:"HL", 0xBF:"A", 0xFE:"n8"}
    def tick(self):
        if self.running:
            self.instruction=self.mem.memory[self.pc]
            self.pc = (self.pc + 1) % 0x10000 # For some reason, the PC is incremented before the instruction is executed. This is important for relative jumps
            try:
                ret_value =  self.opcode_table[self.instruction]()
            except KeyError:
                ret_value =  self.unimplemented_opcode()
            return ret_value

    def __str__(self):
        old_instruction=self.instruction
        self.get_name=True
        ret_value = "Registers: "+str([f"{i}:{hex(self.registers[i])} " for i in self.registers])+"\nFlags:"+str([f"{i}:{self.flags[i]}" for i in self.flags])+"\nPC: "+hex(self.pc)+"  SP: "+hex(self.sp)+"\nInstruction: "# + hex(self.instruction) + " "
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
        self.pc = (self.pc + 1) % 0x10000
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
        if self.get_name: return self.ld_8_n8_table[self.instruction]+", $"+hex(self.mem.memory[self.pc])
        self.registers[self.ld_8_n8_table[self.instruction]] = self.mem.memory[self.pc]
        self.pc = (self.pc + 1) % 0x10000
    def ld_8_r8_r8(self):
        '''
        LD_8 r8, r8
        Loads the value of one register into another
        1 byte, 1 cycle, no flags
        Opcodes: 0x40 (B->B), 0x41 (B->C), 0x42 (B->D), 0x43 (B->E), 0x44 (B->H), 0x45 (B->L), 0x47 (B->A), 0x48 (C->B), 0x49 (C->C), 0x4A (C->D), 0x4B (C->E), 0x4C (C->H), 0x4D (C->L), 0x4F (C->A), 0x50 (D->B), 0x51 (D->C), 0x52 (D->D), 0x53 (D->E), 0x54 (D->H), 0x55 (D->L), 0x57 (D->A), 0x58 (E->B), 0x59 (E->C), 0x5A (E->D), 0x5B (E->E), 0x5C (E->H), 0x5D (E->L), 0x5F (E->A), 0x60 (H->B), 0x61 (H->C), 0x62 (H->D), 0x63 (H->E), 0x64 (H->H), 0x65 (H->L), 0x67 (H->A), 0x68 (L->B), 0x69 (L->C), 0x6A (L->D), 0x6B (L->E), 0x6C (L->H), 0x6D (L->L), 0x6F (L->A), 0x78 (A->B), 0x79 (A->C), 0x7A (A->D), 0x7B (A->E), 0x7C (A->H), 0x7D (A->L), 0x7F (A->A)
        '''
        if self.get_name: return self.ld_8_r8_r8_table["dest"][self.instruction]+", "+self.ld_8_r8_r8_table["src"][self.instruction]
        self.registers[self.ld_8_r8_r8_table["dest"][self.instruction]] = self.registers[self.ld_8_r8_r8_table["src"][self.instruction]]
    def ld_8_r8_mem(self):
        '''
        LD_8 r8, [mem]
        Different instructions that load a value from memory into a register
        *1: 1 byte, 2 cycles, no flags
        *2: 2 bytes, 3 cycles, no flags
        *3: 3 bytes, 4 cycles, no flags
        0x0A: LD A, [BC] (*1), 0x1A: LD A, [DE] (*1), 0x46: LD B, [HL] (*1), 0x4E: LD C, [HL] (*1), 0x56: LD D, [HL] (*1), 0x5E: LD E, [HL] (*1), 0x66: LD H, [HL] (*1), 0x6E: LD L, [HL] (*1), 0x7E: LD A, [HL] (*1), 0xF0: LD A, [a8] (*2), 0xF2: LD A, [C] (*1), 0xFA: LD A, [a16] (*3), 0x2A: LD A, [HL+] (*1), 0x3A: LD A, [HL-] (*1)
        '''
        src = self.ld_8_r8_mem_table["src"][self.instruction]
        is_imm = src in ["a8", "a16"]
        if is_imm:
            if src == "a8":
                src = self.mem.memory[self.pc]
                self.pc = (self.pc + 1) % 0x10000
            elif src == "a16":
                src = self.mem.memory[self.pc+1] << 8 | self.mem.memory[self.pc]
                self.pc = (self.pc + 2) % 0x10000
        if self.get_name: return self.ld_8_r8_mem_table["dest"][self.instruction]+", ["+("$0xFF00+"if self.instruction in {0xF0,0xF2} else "")+(("$"+hex(src)) if is_imm else src)+("+" if self.instruction == 0x2A else "-" if self.instruction == 0x3A else "")+"]"
        if not is_imm: src = self.registers[src]
        if self.instruction in {0xF0, 0xF2}: src = 0xFF00 + src
        src = self.mem.memory[src]
        self.registers[self.ld_8_r8_mem_table["dest"][self.instruction]] = src
        if self.instruction in {0x2A, 0x3A}: self.registers["HL"] = (self.registers["HL"]+ (1 if self.instruction == 0x2A else -1)) % 0x10000
    def ld_8_mem_r8(self):
        '''
        LD_8 [mem], r8 
        Different instructions that load a value from a register into memory. Excepcionally, 0x36's source is an immediate value, I didn't want to make a new function just for that
        *1: 1 byte, 2 cycles, no flags
        *2: 2 bytes, 3 cycles, no flags
        *3: 3 bytes, 4 cycles, no flags
        0x02: LD [BC], A (*1), 0x12: LD [DE], A (*1), 0x70: LD [HL], B (*1), 0x71: LD [HL], C (*1), 0x72: LD [HL], D (*1), 0x73: LD [HL], E (*1), 0x74: LD [HL], H (*1), 0x75: LD [HL], L (*1), 0x77: LD [HL], A (*1), 0xE0: LD [a8], A (*2), 0xE2: LD [C], A (*1), 0xEA: LD [a16], A (*3), 0x22: LD [HL+], A (*1), 0x32: LD [HL-], A (*1), 0x36: LD [HL], n8 (*1)
        self.ld_8_mem_r8_table
        '''
        src = self.ld_8_mem_r8_table["src"][self.instruction]
        src_is_imm = src == "n8"
        if src_is_imm:
            src = self.mem.memory[self.pc]
            self.pc = (self.pc + 1) % 0x10000
        dest = self.ld_8_mem_r8_table["dest"][self.instruction]
        dest_is_imm = dest in ["a8", "a16"]
        if dest_is_imm:
            if dest == "a8":
                dest = self.mem.memory[self.pc]
                self.pc = (self.pc + 1) % 0x10000
            elif dest == "a16":
                dest = self.mem.memory[self.pc+1] << 8 | self.mem.memory[self.pc]
                self.pc = (self.pc + 2) % 0x10000
        if self.get_name: return "["+("$0xFF00+"if self.instruction in {0xE0,0xE2} else "")+(("$"+hex(dest)) if dest_is_imm else dest)+("+" if self.instruction == 0x22 else "-" if self.instruction == 0x32 else "")+"], "+(("$"+hex(src)) if src_is_imm else src)
        if not src_is_imm: src = self.registers[src]
        if not dest_is_imm:
            dest = self.registers[dest]
        if self.instruction in {0xE0, 0xE2}: dest += 0xFF00
        self.mem.memory[dest] = src
        if self.instruction in {0x22, 0x32}: self.registers["HL"] = (self.registers["HL"]+ (1 if self.instruction == 0x22 else -1)) % 0x10000
    #endregion
    #region pc_change
    def pc_change(self, implicit=None):
        '''
        This function is in charge of changing the PC. It's used for JR, JP, CALL, RET and RST
        Documentation to be completed
        '''
        new_pc = self.pc_change_table["new_pc"][self.instruction]
        if new_pc == "a16":
            new_pc = self.mem.memory[self.pc+1] << 8 | self.mem.memory[self.pc]
            self.pc = (self.pc + 2) % 0x10000
        elif new_pc == "e8":
            new_pc = self.mem.memory[self.pc]
            if new_pc > 127: new_pc -= 256
            self.pc = (self.pc + 1) % 0x10000
        if self.get_name and implicit is None: return self.pc_change_table["name"][self.instruction]+((" "+self.pc_change_table["cond"][self.instruction]) if self.pc_change_table["cond"][self.instruction] !="True" else "")+" "+(("$"+("+" if self.pc_change_table["name"][self.instruction] == "JR" and new_pc>=0 else "")+hex(new_pc)) if new_pc != "HL" and self.pc_change_table["name"][self.instruction] !="RET" else "HL" if new_pc == "HL" else "")
        if eval(self.flag_nomenclature[self.pc_change_table["cond"][self.instruction]]):
            if self.pc_change_table["name"][self.instruction] in {"CALL", "RST"}:
                self.sp = (self.sp - 2) % 0x10000
                self.mem.memory[self.sp+1] = self.pc >> 8
                self.mem.memory[self.sp] = self.pc & 0xFF
            elif new_pc == "SP":
                new_pc= self.mem.memory[self.sp+1] << 8 | self.mem.memory[self.sp]
                self.sp = (self.sp + 2) % 0x10000
            elif new_pc == "HL":
                new_pc = self.registers["HL"]
            elif self.pc_change_table["name"][self.instruction] == "JR":
                new_pc = (self.pc + new_pc) % 0x10000
            elif self.instruction == 0xD9: #RETI
                print("IME set (placeholder)")
            self.pc = new_pc

    #endregion
    def cp(self):
        '''
        CP r8, r8|n8|[mem]
        Compare the value of a register with another register, an immediate value or a memory address. The result is stored in the flags
        1(r8,mem) | 2 (n8) byte(s) , 1(r8) | 2(n8,mem) cycle(s), Flags affected: Z, N, H, C
        '''
        src = self.cp_src_table[self.instruction]
        if src == "n8":
            src = self.mem.memory[self.pc]
            self.pc = (self.pc + 1) % 0x10000
        if self.get_name: return "CP A, "+(("$"+hex(src)) if type(src)==int else "[HL]" if src == "HL" else src)
        if src == "HL": src = self.mem.memory[self.registers["HL"]]
        elif type(src)!=int: src = self.registers[src]
        self.flags["Z"] = int(self.registers["A"] == src)
        self.flags["N"] = 1
        self.flags["H"] = int((self.registers["A"] & 0xF) < (src & 0xF))
        self.flags["C"] = int(self.registers["A"] < src)
    #endregion