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
        self.in_prefix = False
        self.IME = False
        self.IME_pending = 0
        self.flag_nomenclature = {"Z": "bool(self.flags[\"Z\"])", "N": "bool(self.flags[\"N\"])", "H": "bool(self.flags[\"H\"])", "C": "bool(self.flags[\"C\"])", "NZ": "not bool(self.flags[\"Z\"])", "NC": "not bool(self.flags[\"C\"])", "NN": "not bool(self.flags[\"N\"])", "NH": "not bool(self.flags[\"H\"])", "True": "True", "False": "False"}
        #region opcode_dict
        self.opcode_table={0x0: self.NOP, 0x10: self.STOP, 0x37: self.SCF, 0x2F: self.CPL, 0x3F:self.CCF, 0x27:self.DAA, 0xCB:self.cb_prefix, **{i:self.di_ei for i in {0xF3, 0xFB}}, **{i:self.LD_8 for i in set(range(2,64,4)) | set(range(0x40,0x80)) - {0x76} | {0xE0, 0xE2, 0xEA, 0xF0, 0xF2, 0xFA}}, **{i:self.pc_change for i in {0x18, 0x20, 0x28, 0x30, 0x38} | {0xC2, 0xC3, 0xCA, 0xD2, 0xDA} | {0xC4, 0xCC, 0xCD, 0xD4, 0xDC} | {0xC0, 0xC8, 0xC9, 0xD0, 0xD8, 0xD9} | set(range(0xC7, 0x100, 0x8))}, 0x76:self.HALT, **{i:self.empty_opcode for i in {0xD3, 0xDB, 0xDD, 0xE3, 0xE4, 0xEB, 0xEC, 0xED, 0xF4, 0xFC, 0xFD}}, **{i:self.CP for i in set(range(0xB8,0xC0)) | {0xFE}}, **{k:self.inc_dec  for i in range(0x03, 0x43, 0x8) for k in range(i,i+3)}, **{i:self.ld_16 for i in set(range(0x1,0x41,0x10)) | {0x8} | {0xF8, 0xF9}}, **{k:self.push_pop for i in range(0xC1, 0x100,0x10) for k in range(i, i+6, 5)}, **{i:self.shift_rot for i in set(range(0x07,0x20,0x8))}, **{i:self.add_sub for i in set(range(0x80, 0xA0)) | {0xC6, 0xCE}}, **{i:self.add_16 for i in set(range(0x9,0x49, 0x10))}, **{i:self.logic_ops for i in set(range(0xA0,0xB8)) | {0xE6, 0xEE, 0xF6}}}
        self.prefix_opcode_table={**{i:self.shift_rot for i in set(range(0x0,0x40))-set(range(0x30,0x38))}, **{i:self.swap for i in set(range(0x30,0x38))}, **{i:self.bit for i in set(range(0x40,0x80))}, **{i:self.res_set for i in set(range(0x80,0x100))}}
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
        #endregion
        #region inc_dec_dict
        self.inc_dec_table={"target":{0x03:"BC", 0x04:"B", 0x05:"B", 0x0B:"BC", 0x0C:"C", 0x0D:"C", 0x13:"DE", 0x14:"D", 0x15:"D", 0x1B:"DE", 0x1C:"E", 0x1D:"E", 0x23:"HL", 0x24:"H", 0x25:"H", 0x2B:"HL", 0x2C:"L", 0x2D:"L", 0x33: "SP", 0x34:"[HL]", 0x35:"[HL]", 0x3B:"SP", 0x3C:"A", 0x3D:"A"}, "op":{0x03:1, 0x04:1, 0x05:-1, 0x0B:1, 0x0C:1, 0x0D:-1, 0x13:1, 0x14:1, 0x15:-1, 0x1B:1, 0x1C:1, 0x1D:-1, 0x23:1, 0x24:1, 0x25:-1, 0x2B:1, 0x2C:1, 0x2D:-1, 0x34:1, 0x35:-1, 0x3C:1, 0x3D:-1}}
        #endregion
        #region ld_16_dict
        self.ld_16_table={"src":{**{i:"n16" for i in set(range(0x1,0x41,0x10))}, 0x8:"SP", 0xF8:"e8", 0xF9:"HL"}, "dest":{0x1:"BC", 0x11: "DE", 0x21:"HL", 0x31:"SP", 0x8:"a16", 0xF8:"HL", 0xF9:"SP"}}
        #endregion
        #region push_pop_dict
        self.push_pop_table={"reg":{0xC1:"BC", 0xC5:"BC", 0xD1:"DE", 0xD5:"DE", 0xE1:"HL", 0xE5:"HL", 0xF1:"AF", 0xF5:"AF"}, "name":{**{i:"POP" for i in range(0xC1, 0xF1, 0x10)}, **{i:"PUSH" for i in range(0xC5, 0xF5, 0x10)}}}
        #endregion
        #region shift_rot_dict
        self.shift_rot_table={"reg":{**{i:"A" for i in set(range(0x07, 0x37, 0x10)) | {0x3F}}, **{i:"B" for i in set(range(0x0, 0x30,0x8)) | {0x38}}, **{i:"C" for i in set(range(0x1, 0x31,0x8)) | {0x39}}, **{i:"D" for i in set(range(0x2, 0x32,0x8)) | {0x3A}}, **{i:"E" for i in set(range(0x3, 0x33,0x8)) | {0x3B}}, **{i:"H" for i in set(range(0x4, 0x34,0x8)) | {0x3C}}, **{i:"L" for i in set(range(0x5, 0x35,0x8)) | {0x3D}}, **{i:"[HL]" for i in set(range(0x6, 0x36,0x8)) | {0x3E}}}, "name_direct":{0x07:"RLCA", 0x0F: "RRCA", 0x17: "RLA", 0x1F: "RRA"}, "name":{**{i:"RLC" for i in range(0x0,0x8)}, **{i:"RRC" for i in range(0x8,0x10)}, **{i:"RL" for i in range(0x10,0x18)}, **{i:"RR" for i in range(0x18,0x20)}, **{i:"SLA" for i in range(0x20,0x28)}, **{i:"SRA" for i in range(0x28,0x30)}, **{i:"SRL" for i in range(0x38,0x40)}}}
        #endregion
        #region add_sub_dict
        self.add_sub_table = {"src":{**{i:"B" for i in range(0x80, 0xA0, 0x8)}, **{i:"C" for i in range(0x81, 0xA1, 0x8)}, **{i:"D" for i in range(0x82, 0xA2, 0x8)}, **{i:"E" for i in range(0x83, 0xA3, 0x8)}, **{i:"H" for i in range(0x84, 0xA4, 0x8)}, **{i:"L" for i in range(0x85, 0xA5, 0x8)}, **{i:"[HL]" for i in range(0x86, 0xA6, 0x8)}, **{i:"A" for i in range(0x87, 0xA7, 0x8)}, **{i:"n8" for i in range(0xC6, 0xE6, 0x8)}}, "name":{**{i:"ADD" for i in set(range(0x80, 0x88)) | {0xC6}}, **{i:"ADC" for i in set(range(0x88, 0x90)) | {0xCE}}, **{i:"SUB" for i in set(range(0x90, 0x98)) | {0xD6}}, **{i:"SBC" for i in set(range(0x98, 0xA0)) | {0xDE}}}}
        #endregion
        #region add_16_dict
        self.add_16_table = {0x9: "BC", 0x19: "DE", 0x29: "HL", 0x39: "SP", 0xE8: "e8"}
        #endregion
        #region logic_ops_dict
        self.logic_ops_table = {"src":{**{i:"B" for i in set(range(0xA0, 0xB1, 0x8))}, **{i:"C" for i in set(range(0xA1, 0xB2, 0x8))}, **{i:"D" for i in set(range(0xA2, 0xB3, 0x8))}, **{i:"E" for i in set(range(0xA3, 0xB4, 0x8))}, **{i:"H" for i in set(range(0xA4, 0xB5, 0x8))}, **{i:"L" for i in set(range(0xA5, 0xB6, 0x8))}, **{i:"[HL]" for i in set(range(0xA6, 0xB7, 0x8))}, **{i:"A" for i in set(range(0xA7, 0xB8, 0x8))}, **{i:"n8" for i in {0xE6, 0xEE, 0xF6}}}, "name":{**{i:"AND" for i in set(range(0xA0, 0xA8)) | {0xE6}}, **{i:"XOR" for i in set(range(0xA8, 0xB0)) | {0xEE}}, **{i:"OR" for i in set(range(0xB0, 0xB8)) | {0xF6}}}}
        #endregion
        #region swap_dict
        self.swap_table = {0x30: "B", 0x31: "C", 0x32: "D", 0x33: "E", 0x34: "H", 0x35: "L", 0x36: "[HL]", 0x37: "A"}
        #endregion
        #region bit_dict
        self.bit_table = {"src":{**{i:"B" for i in set(range(0x40, 0x80, 0x8))}, **{i:"C" for i in set(range(0x41, 0x81, 0x8))}, **{i:"D" for i in set(range(0x42, 0x82, 0x8))}, **{i:"E" for i in set(range(0x43, 0x83, 0x8))}, **{i:"H" for i in set(range(0x44, 0x84, 0x8))}, **{i:"L" for i in set(range(0x45, 0x85, 0x8))}, **{i:"[HL]" for i in set(range(0x46, 0x86, 0x8))}}, "bit":{**{i:0 for i in range(0x40, 0x48)}, **{i:1 for i in range(0x48, 0x50)}, **{i:2 for i in range(0x50, 0x58)}, **{i:3 for i in range(0x58, 0x60)}, **{i:4 for i in range(0x60, 0x68)}, **{i:5 for i in range(0x68, 0x70)}, **{i:6 for i in range(0x70, 0x78)}, **{i:7 for i in range(0x78, 0x80)}}}
        #endregion
        #region res_set_dict
        self.res_set_table = {"src":{**{i:"B" for i in set(range(0x80, 0x100, 0x8))}, **{i:"C" for i in set(range(0x81, 0x101, 0x8))}, **{i:"D" for i in set(range(0x82, 0x102, 0x8))}, **{i:"E" for i in set(range(0x83, 0x103, 0x8))}, **{i:"H" for i in set(range(0x84, 0x104, 0x8))}, **{i:"L" for i in set(range(0x85, 0x105, 0x8))}, **{i:"[HL]" for i in set(range(0x86, 0x106, 0x8))}, **{i:"A" for i in set(range(0x87, 0x107, 0x8))}}, "bit":{**{i:0 for i in set(range(0x80, 0x88)) | set(range(0xC0, 0xC8))}, **{i:1 for i in set(range(0x88, 0x90)) | set(range(0xC8, 0xD0))}, **{i:2 for i in set(range(0x90, 0x98)) | set(range(0xD0, 0xD8))}, **{i:3 for i in set(range(0x98, 0xA0)) | set(range(0xD8, 0xE0))}, **{i:4 for i in set(range(0xA0, 0xA8)) | set(range(0xE0, 0xE8))}, **{i:5 for i in set(range(0xA8, 0xB0)) | set(range(0xE8, 0xF0))}, **{i:6 for i in set(range(0xB0, 0xB8)) | set(range(0xF0, 0xF8))}, **{i:7 for i in set(range(0xB8, 0xC0)) | set(range(0xF8, 0x100))}}, "name":{**{i:"RES" for i in set(range(0x80, 0xC0))}, **{i:"SET" for i in set(range(0xC0, 0x100))}}}
    def tick(self):
        if self.running:
            if not self.get_name:
                if self.IME_pending > 0:
                    self.IME_pending -= 1
                    if self.IME_pending <= 0: self.IME = True
            self.instruction=self.mem[self.pc]
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
    def cb_prefix(self):
        '''
        This function handles the CB prefix
        '''
        self.instruction = self.mem[self.pc]
        self.pc = (self.pc + 1) % 0x10000
        self.in_prefix = True
        try:
            ret_value = self.prefix_opcode_table[self.instruction]()
        except KeyError:
            ret_value = self.unimplemented_opcode()
        self.in_prefix = False
        return ret_value
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
    def SCF(self):
        '''
        0x37: SCF
        Simply sets the carry flag to 1 and clears N and H
        1 byte, 1 cycle, Flags affected: N (0), H (0), C (1)
        '''
        if self.get_name: return "SCF"
        self.flags["N"] = 0
        self.flags["H"] = 0
        self.flags["C"] = 1
    def CPL(self):
        '''
        0x2F: CPL
        Complements the A register
        1 byte, 1 cycle, Flags affected: N (1), H (1)
        '''
        if self.get_name: return "CPL A"
        self.registers["A"] = ~self.registers["A"] & 0xFF
        self.flags["N"] = 1
        self.flags["H"] = 1
    def CCF(self):
        '''
        0x3F: CCF
        Complements the carry flag and clears N and H
        1 byte, 1 cycle, Flags affected: N (0), H (0), C
        '''
        if self.get_name: return "CCF"
        self.flags["N"] = 0
        self.flags["H"] = 0
        self.flags["C"] = int(not bool(self.flags["C"]))
    def DAA(self):
        '''
        0x27: DAA
        Decimal Adjust Accumulator
        1 byte, 1 cycle, Flags affected: Z, N, H (0), C
        '''
        if self.get_name: return "DAA"
        
        a = self.registers["A"]
        
        if not self.flags["N"]:  # After an addition
            if self.flags["H"] or (a & 0x0F) > 9:
                a += 0x06
            if self.flags["C"] or (a & 0xF0) > 0x90:
                a += 0x60
        else:  # After a subtraction
            if self.flags["H"]:
                a = (a - 0x06) & 0xFF
            if self.flags["C"]:
                a -= 0x60
        self.flags["Z"] = int(self.registers["A"] == 0)
        
        self.flags["H"] = 0
        if a >= 0x100:
            self.flags["C"] = 1
        self.registers["A"] = a & 0xFF
    def empty_opcode(self):
        '''
        This opcode doesn't map to any instruction, so if this is the next opcode, something has gone wrong
        '''
        if self.get_name: return "???"
        print("Empty opcode: "+hex(self.instruction))
        self.running=False
    def unimplemented_opcode(self):
        if self.get_name: return "unimpl ("+hex(self.instruction)+")"
        print("Oops, haven't got around to implementing this opcode yet")
        #for now, let's skip to the next instruction
    def di_ei(self):
        '''
        0xF3: DI
        0xFB: EI
        1 byte, 1 cycle, no flags
        Disable/Enable interrupts
        '''
        if self.get_name: return "DI" if self.instruction == 0xF3 else "EI"
        if self.instruction == 0xF3: self.IME = False
        else: self.IME_pending = 2
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
        if self.get_name: return self.ld_8_n8_table[self.instruction]+", $"+hex(self.mem[self.pc])
        self.registers[self.ld_8_n8_table[self.instruction]] = self.mem[self.pc]
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
                src = self.mem[self.pc]
                self.pc = (self.pc + 1) % 0x10000
            elif src == "a16":
                src = self.mem[self.pc+1] << 8 | self.mem[self.pc]
                self.pc = (self.pc + 2) % 0x10000
        if self.get_name: return self.ld_8_r8_mem_table["dest"][self.instruction]+", ["+("$0xFF00+"if self.instruction in {0xF0,0xF2} else "")+(("$"+hex(src)) if is_imm else src)+("+" if self.instruction == 0x2A else "-" if self.instruction == 0x3A else "")+"]"
        if not is_imm: src = self.registers[src]
        if self.instruction in {0xF0, 0xF2}: src = 0xFF00 + src
        src = self.mem[src]
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
            src = self.mem[self.pc]
            self.pc = (self.pc + 1) % 0x10000
        dest = self.ld_8_mem_r8_table["dest"][self.instruction]
        dest_is_imm = dest in ["a8", "a16"]
        if dest_is_imm:
            if dest == "a8":
                dest = self.mem[self.pc]
                self.pc = (self.pc + 1) % 0x10000
            elif dest == "a16":
                dest = self.mem[self.pc+1] << 8 | self.mem[self.pc]
                self.pc = (self.pc + 2) % 0x10000
        if self.get_name: return "["+("$0xFF00+"if self.instruction in {0xE0,0xE2} else "")+(("$"+hex(dest)) if dest_is_imm else dest)+("+" if self.instruction == 0x22 else "-" if self.instruction == 0x32 else "")+"], "+(("$"+hex(src)) if src_is_imm else src)
        if not src_is_imm: src = self.registers[src]
        if not dest_is_imm:
            dest = self.registers[dest]
        if self.instruction in {0xE0, 0xE2}: dest += 0xFF00
        self.mem[dest] = src
        if self.instruction in {0x22, 0x32}: self.registers["HL"] = (self.registers["HL"]+ (1 if self.instruction == 0x22 else -1)) % 0x10000
    #endregion
    #region ld_16
    def ld_16(self):
        '''
        LD_16 r16|[a16]|SP, r16|SP|SP+e8
        Loads a 16-bit value into a register, a memory address or the stack pointer
        1|2|3 bytes, 2|3|5 cycles, no flags
        '''
        src = self.ld_16_table["src"][self.instruction]
        if src == "n16":
            src = self.mem[self.pc+1] << 8 | self.mem[self.pc]
            self.pc = (self.pc + 2) % 0x10000
        elif src == "e8":
            src = self.mem[self.pc]
            if src > 127: src -= 256
            self.pc = (self.pc + 1) % 0x10000
        dest = self.ld_16_table["dest"][self.instruction]
        if dest == "a16":
            dest = self.mem[self.pc+1] << 8 | self.mem[self.pc]
            self.pc = (self.pc + 2) % 0x10000
        if self.get_name: return "LD_16 " + (f"[${hex(dest)}]" if type(dest)==int else dest) + ", " + (("SP + " if self.instruction == 0xF8 else "")+f"${hex(src)}" if type(src)==int else src)
        if src == "SP":
            src = self.sp
        elif src == "HL":
            src = self.registers["HL"]
        elif self.instruction == 0xF8:
            src = (self.sp + src) % 0x10000
        if dest == "SP":
            self.sp = src
        elif type(dest)==int:
            self.mem[dest] = src & 0xFF
            self.mem[dest+1] = src >> 8
        else:
            self.registers[dest] = src
    def push_pop(self):
        '''
        PUSH|POP r16
        Pushes or pops a register pair from the stack
        1 byte, 4 cycles, no flags
        '''
        reg = self.push_pop_table["reg"][self.instruction]
        if self.get_name: return self.push_pop_table["name"][self.instruction]+" "+reg
        if self.push_pop_table["name"][self.instruction] == "PUSH":
            self.sp = (self.sp - 2) % 0x10000
            self.mem[self.sp+1] = self.registers[reg] >> 8
            self.mem[self.sp] = self.registers[reg] & 0xFF
        else:
            self.registers[reg] = self.mem[self.sp+1] << 8 | self.mem[self.sp]
            self.sp = (self.sp + 2) % 0x10000
    #endregion
    #region pc_change
    def pc_change(self):
        '''
        This function is in charge of changing the PC. It's used for JR, JP, CALL, RET and RST
        Documentation to be completed
        '''
        new_pc = self.pc_change_table["new_pc"][self.instruction]
        if new_pc == "a16":
            new_pc = self.mem[self.pc+1] << 8 | self.mem[self.pc]
            self.pc = (self.pc + 2) % 0x10000
        elif new_pc == "e8":
            new_pc = self.mem[self.pc]
            if new_pc > 127: new_pc -= 256
            self.pc = (self.pc + 1) % 0x10000
        if self.get_name: return self.pc_change_table["name"][self.instruction]+((" "+self.pc_change_table["cond"][self.instruction]) if self.pc_change_table["cond"][self.instruction] !="True" else "")+" "+(("$"+("+" if self.pc_change_table["name"][self.instruction] == "JR" and new_pc>=0 else "")+hex(new_pc)) if new_pc != "HL" and self.pc_change_table["name"][self.instruction] !="RET" else "HL" if new_pc == "HL" else "")
        if eval(self.flag_nomenclature[self.pc_change_table["cond"][self.instruction]]):
            if self.pc_change_table["name"][self.instruction] in {"CALL", "RST"}:
                self.sp = (self.sp - 2) % 0x10000
                self.mem[self.sp+1] = self.pc >> 8
                self.mem[self.sp] = self.pc & 0xFF
            elif new_pc == "SP":
                new_pc= self.mem[self.sp+1] << 8 | self.mem[self.sp]
                self.sp = (self.sp + 2) % 0x10000
            elif new_pc == "HL":
                new_pc = self.registers["HL"]
            elif self.pc_change_table["name"][self.instruction] == "JR":
                new_pc = (self.pc + new_pc) % 0x10000
            elif self.instruction == 0xD9: #RETI
                self.IME_pending = 2
            self.pc = new_pc
    #endregion
    #region math
    def CP(self):
        '''
        CP r8, r8|n8|[mem]
        Compare the value of a register with another register, an immediate value or a memory address. The result is stored in the flags
        1|2|1 byte(s) , 1|2|2 cycle(s), Flags affected: Z , N (1), H , C 
        '''
        src = self.cp_src_table[self.instruction]
        if src == "n8":
            src = self.mem[self.pc]
            self.pc = (self.pc + 1) % 0x10000
        if self.get_name: return "CP A, "+(("$"+hex(src)) if type(src)==int else "[HL]" if src == "HL" else src)
        if src == "HL": src = self.mem[self.registers["HL"]]
        elif type(src)!=int: src = self.registers[src]
        self.flags["Z"] = int(self.registers["A"] == src)
        self.flags["N"] = 1
        self.flags["H"] = int((self.registers["A"] & 0xF) < (src & 0xF))
        self.flags["C"] = int(self.registers["A"] < src)
    def inc_dec(self):
        '''
        INC|DEC r8|r16|mem
        Increment or decrement the value of a register, a register pair or a memory address
        1|1|2 byte(s), 1|2|3 cycle(s), Flags affected: Z, N, H (only in 8 bits)
        '''
        target = self.inc_dec_table["target"][self.instruction]
        val = self.inc_dec_table["op"][self.instruction]
        if self.get_name: return ("INC" if val == 1 else "DEC")+" "+target
        num = self.mem[self.registers["HL"]] if target == "[HL]" else self.sp if target == "SP" else self.registers[target]
        if target not in {"AF","BC","DE", "HL", "SP"}:
            self.flags["N"] = max(0,-val)
            self.flags["H"] = int((num & 0xF) == 0xF) if val == 1 else int((num & 0xF) == 0)
            self.flags["Z"] = int((num + val) % 0x100 == 0)
        if target == "[HL]":
            self.mem[self.registers["HL"]] = (num + val) % 0x100
        elif target == "SP":
            self.sp = (self.sp + val) % 0x10000
        else:
            self.registers[target] = (num + val) % (0x100 if target not in {"AF","BC","DE", "HL"} else 0x10000)
    def add_sub(self):
        '''
        ADD|ADC|SUB|SBC A, r8|[mem]|n8
        Performs addition/substraction: A +/- r8|[mem]|n8 (+/- C flag) => A
        1|2|2 cycle(s), 1|1|2 byte(s)
        Flags affected: Z, N(0/1 for +/-), H, C
        '''
        src = self.add_sub_table["src"][self.instruction]
        if src == "n8":
            src = self.mem[self.pc]
            self.pc = (self.pc + 1) % 0x10000
        name = self.add_sub_table["name"][self.instruction]
        if self.get_name: return name+" A, "+(("$"+hex(src)) if type(src)==int else "[HL]" if src == "HL" else src)
        if src == "HL": src = self.mem[self.registers["HL"]]
        elif type(src)!=int: src = self.registers[src]
        if name[2]=="C": src += self.flags["C"]
        if name[0] == "S": src = -src
        a = self.registers["A"]
        self.flags["Z"] = int((a+src) % 0x100 == 0)
        self.flags["N"] = 0 if name[0] == "A" else 1
        if name[0] == "A": 
            self.flags["H"] = int((a & 0xF) + (src & 0xF) > 0xF)
            self.flags["C"] = int(a+src > 0xFF)
        else: 
            self.flags["H"] = int((a & 0xF) < (src & 0xF))
            self.flags["C"] = int(a+src < 0)
        a += src
        self.registers["A"] = a % 0x100
    def add_16(self):
        '''
        ADD HL|SP r16|e8
        Adds a 16-bit value to HL or  an 8 bit value to SP. The carry flag doesn't affect this operation
        1|2 byte(s), 2|4 cycle(s), Flags affected: Z (0, only in ADD SP, e8), N (0), H, C
        '''
        src = self.add_16_table[self.instruction]
        dest = "HL" if self.instruction != 0x39 else "SP"
        if dest == "SP":
            src = self.mem[self.pc]
            if src > 127: src -= 256
            self.pc = (self.pc + 1) % 0x10000
        if self.get_name: return "ADD "+dest+", "+(f"${hex(src)}" if type(src)==int else src)
        if type(src)!=int: src = self.registers[src]
        value = self.sp if dest == "SP" else self.registers[dest]
        self.flags["N"] = 0
        if self.instruction == 0xE8: 
            self.flags["Z"] = 0
            self.flags["H"] = int((value & 0xF) + (src & 0xF) > 0xF)
            self.flags["C"] = int((value & 0xFF) + src > 0xFF)
        else:
            self.flags["H"] = int((value & 0xFFF) + (src & 0xFFF) > 0xFFF)
            self.flags["C"] = int(value + src > 0xFFFF)
        if dest == "SP": self.sp = (self.sp + src) % 0x10000
        else: self.registers[dest] = (value + src) % 0x10000
    #region bit_manipulation
    def shift_rot(self):
        '''
        This function is in charge of the rotate and shift instructions
        Rotate: R L|R _|C r8|[HL] = Rotate Left|Right| through carry|not through Carry
        Shift: S L|R L|A r8|[HL] = Shift Left|Right| Logic|Arithmetic
        1|2 (direct|prefix) byte(s), 2|4 (r8|[mem]) cycles, Flags affected: Z (0 if direct), N (0), H (0), C
        '''
        reg = self.shift_rot_table["reg"][self.instruction]
        name = self.shift_rot_table["name"][self.instruction] if self.in_prefix else self.shift_rot_table["name_direct"][self.instruction]
        if self.get_name: return name+" "+reg
        if reg == "[HL]": value = self.mem[self.registers["HL"]]
        else: value = self.registers[reg]
        aux = self.flags["C"]
        if name[1] =="L":
            self.flags["C"] = value >> 7
            value = (value << 1) & 0xFF
            if name[0] == "R":
                if len(name)==3: value |= self.flags["C"]#There is a C
                else: value |= aux
        else:
            self.flags["C"] = value & 1
            msb = value & 0x80
            value = value >> 1
            if name[0] == "R":
                if len(name)==3: value |= self.flags["C"] << 7
                else: value |= aux << 7
            elif name[2]=="A" and msb==1: value |= 0x80
        if self.in_prefix and value == 0: self.flags["Z"] = 1
        else: self.flags["Z"] = 0
        self.flags["N"] = 0
        self.flags["H"] = 0
        if reg == "[HL]": self.mem[self.registers["HL"]] = value
        else: self.registers[reg] = value
    def swap(self):
        '''
        SWAP r8|[HL]
        Swaps the upper and lower nibbles of a register or a memory address
        2 byte(s), 2|4 cycle(s), Flags affected: Z, N (0), H (0), C (0)
        '''
        reg = self.swap_table[self.instruction]
        if self.get_name: return "SWAP "+reg
        if reg == "[HL]": value = self.mem[self.registers["HL"]]
        else: value = self.registers[reg]
        value = (value >> 4) | (value << 4)
        self.flags["Z"] = int(value == 0)
        self.flags["N"] = 0
        self.flags["H"] = 0
        self.flags["C"] = 0
        if reg == "[HL]": self.mem[self.registers["HL"]] = value
        else: self.registers[reg] = value
    def bit(self):
        
        '''
        BIT b, r8|[HL]
        Tests the value of the b th bit in a register or a memory address using the Z flag
        2 byte(s), 2| cycle(s), Flags affected: Z, N (0), H (1)
        '''
        bit = self.bit_table[self.instruction]
        reg = self.bit_table[self.instruction]
        if self.get_name: return "BIT "+str(bit)+", "+reg
        if reg == "[HL]": value = self.mem[self.registers["HL"]]
        else: value = self.registers[reg]
        self.flags["Z"] = int(not bool(value & (1 << bit)))
    def res_set(self):
        '''
        RES|SET b, r8|[HL]
        Resets or sets the b th bit in a register or a memory address
        2 byte(s), 2|4 cycle(s), Flags affected: none
        '''
        bit = self.res_set_table["bit"][self.instruction]
        reg = self.res_set_table["reg"][self.instruction]
        name = self.res_set_table["name"][self.instruction]
        if self.get_name: return name+" "+str(bit)+", "+reg
        if reg == "[HL]": value = self.mem[self.registers["HL"]]
        else: value = self.registers[reg]
        if name == "SET": value |= 1 << bit
        else: value &= ~(1 << bit)
    #endregion
    #endregion
    #region logic_ops
    def logic_ops(self):
        '''
        AND|OR|XOR A, r8|[mem]|n8
        Makes a bitwise AND|OR|XOR between A and a register, a byte in memory or an immediate 8 bit value. All operations take the same time

        1|1|2 bytes, 1|2|2 cycles, Flags affected: Z, N (0), H(1), C (0)
        '''
        src = self.logic_ops_table["src"][self.instruction]
        if src == "n8":
            src = self.mem[self.pc]
            self.pc = (self.pc + 1) % 0x10000
        name = self.logic_ops_table["name"][self.instruction]
        if self.get_name: return name+" A, "+(("$"+hex(src)) if type(src)==int else "[HL]" if src == "HL" else src)
        if src == "HL": src = self.mem[self.registers["HL"]]
        elif type(src)!=int: src = self.registers[src]
        if name == "AND":
            self.registers["A"] &= src
        elif name == "OR":
            self.registers["A"] |= src
        elif name == "XOR":
            self.registers["A"] ^= src
        self.flags["Z"] = int(self.registers["A"] == 0)
        self.flags["N"] = 0
        self.flags["H"] = 1
        self.flags["C"] = 0
    #endregion
    #endregion