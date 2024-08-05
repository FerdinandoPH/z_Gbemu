from Cpu import Cpu
from Memory import Memory
from Timers import Timers
import time
ctrl_c_counter = 0
def hex(num):
    if num>=0:
        return "0x"+format(num, 'X')
    return "-0x"+format(-num, 'X')
def emu_init(args):
    global breakpoints
    breakpoints={"PC":set(), "OPCODE":set(), "MEM_WATCH":{}, "REG_WATCH":{}}
    init(args)
def init(args):
    global cpu, mem, debug_level, timer
    mem = Memory(0x10000)
    debug_level = 0
    mem.load_rom(args.rom)
    cpu = Cpu(mem)
    timer = Timers(mem)
    main_loop(args)
def main_loop(args):
    global cpu, mem, debug_level, breakpoints, ctrl_c_counter, timer
    while cpu.state != "QUIT":
        try:
            if cpu.IME and cpu.state != "STOPPED":
                if cpu.IME:
                    cpu.check_interrupts(debug_level)
            if cpu.pc in breakpoints["PC"]:
                debug_level=0
                print("Breakpoint hit at PC: "+hex(cpu.pc))
            if mem[cpu.pc] in breakpoints["OPCODE"]:
                debug_level=0
                print("Breakpoint hit at opcode: "+hex(mem[cpu.pc]))
            for address in breakpoints["MEM_WATCH"]:
                if eval(str(mem[address])+breakpoints["MEM_WATCH"][address][0]+breakpoints["MEM_WATCH"][address][1]):
                    debug_level=0
                    print("Memwatch triggered at memory address: "+hex(address),", now the value is: "+hex(mem[address]))
            for reg in breakpoints["REG_WATCH"]:
                if eval(str(cpu.registers[reg])+breakpoints["REG_WATCH"][reg][0]+breakpoints["REG_WATCH"][reg][1]):
                    debug_level=0
                    print("Regwatch triggered at register: "+reg,", now the value is: "+hex(cpu.registers[reg]))
            if debug_level<=0:
                exit=False
                print(timer)
                print(cpu)
                #print("Debug menu")
                while not exit:
                    ctrl_c_counter=0
                    answer = input("Enter command (h for help): ")
                    if len(answer)<1:
                        exit=True
                    elif answer[0]=='h':
                        print("h: Help")
                        print("q: Quit")
                        print("c: Continue")
                        print("r: Reset")
                        print("s: Step")
                        print("m: Memory dump")
                        print("p: Processor dump")
                        print("i: python debugger")
                        print("b: Add breakpoint")
                        print("d: Delete breakpoint")
                        print("w: See all breakpoints")
                        print("x: Clear all breakpoints")
                        print("t: See timers")
                    elif answer[0]=='q':
                        exit=True
                        cpu.state="QUIT"
                        print("Quitting...")
                    elif answer[0]=='c':
                        exit=True
                        debug_level=1
                    elif answer[0]=='r':
                        exit=True
                        print("Resetting...")
                        init(args)
                    elif answer[0]=='s':
                        exit=True
                    elif answer[0] == 'i':
                        pass #Add breakpoint here
                    elif answer[0]=='m':
                        mem.show_memory()
                    elif answer[0]=='p':
                        print(cpu)
                    elif answer[0]=='b':
                        br_help="Usage: b ([i]nstruction|[o]pcode|[m]em watch | [r]eg watch) (address for mem/reg watch if m/r ) (condition for mem/reg watch if m/r) (address|opcode|value|value)"
                        answer=answer.split(" ")
                        answer.pop(0)
                        if len(answer)<1: 
                            print(br_help)
                            continue
                        elif len(answer)==1: answer.insert(0,"i")
                        if answer[0]=="i":
                            try:
                                if int(answer[1],16) not in range(0,0x10000):
                                    raise ValueError
                                breakpoints["PC"].add(int(answer[1],16))
                            except ValueError:
                                print("Invalid address")
                                print(br_help)
                        elif answer[0]=="o":
                            try:
                                if int(answer[1],16) not in range(0,0x100): raise ValueError
                                breakpoints["OPCODE"].add(int(answer[1],16))
                            except ValueError:
                                print("Invalid opcode")
                                print(br_help)
                        elif answer[0]=="m":
                            try:
                                if int(answer[1],16) not in range(0,0x10000): raise ValueError
                                if answer[2] not in ["<",">","==","<=",">=","!="]: raise ValueError
                                if answer[3].lower() == "x": answer[3] = mem[answer[1]]
                                if int(answer[3],16) not in range(0,256): raise ValueError
                                breakpoints["MEM_WATCH"][answer[1]] = (answer[2], "0x"+answer[3])
                            except ValueError:
                                print("Invalid mem watch")
                                print(br_help)
                        elif answer[0]=="r":
                            try:
                                answer[1]=answer[1].upper()
                                if answer[1] not in {"A","B","C","D","E","F","H","L","AF","BC","DE","HL"}: raise ValueError
                                if answer[2] not in ["<",">","==","<=",">=","!="]: raise ValueError
                                if answer[3].lower() == "x": answer[3] = cpu.registers[answer[1]]
                                if int(answer[3],16) not in (range(0,0x10000) if answer[1] in {"AF","BC","DE","HL"} else range(0,0x100)): raise ValueError
                                breakpoints["REG_WATCH"][answer[1]] = (answer[2], "0x"+answer[3])
                            except ValueError:
                                print("Invalid reg watch")
                                print(br_help)
                        else: print(br_help)
                    elif answer[0] == 'd':
                        dbr_help="Usage: d ([i]nstruction|[o]pcode|[m]em watch|[r]eg watch) (address|opcode|address|register)"
                        answer=answer.split(" ")
                        answer.pop(0)
                        if len(answer)<1:
                            print(dbr_help)
                            continue
                        elif len(answer)==1: answer.insert(0,"i")
                        if answer[0]=="i":
                            try:
                                if int(answer[1],16) not in range(0,0x10000): raise ValueError
                                breakpoints["PC"].remove(int(answer[1],16))
                            except (ValueError, KeyError):
                                print("Invalid address")
                                print(dbr_help)
                        elif answer[0]=="o":
                            try:
                                if int(answer[1],16) not in range(0,0x100): raise ValueError
                                breakpoints["OPCODE"].remove(int(answer[1],16))
                            except (ValueError, KeyError):
                                print("Invalid opcode")
                                print(dbr_help)
                        elif answer[0]=="m":
                            try:
                                if int(answer[1],16) not in range(0,0x10000): raise ValueError
                                del(breakpoints["MEM_WATCH"][answer[1]])
                            except (ValueError, KeyError):
                                print("Invalid mem watch")
                                print(dbr_help)
                        elif answer[0]=="r":
                            try:
                                answer[1]=answer[1].upper()
                                if answer[1] not in {"A","B","C","D","E","F","H","L","AF","BC","DE","HL"}: raise ValueError
                                del(breakpoints["REG_WATCH"][answer[1]])
                            except (ValueError, KeyError):
                                print("Invalid reg watch")
                                print(dbr_help)
                        else: print(dbr_help)
                    elif answer[0] == 'w':
                        print("Breakpoints: {",end = " ")
                        print("PC:", [hex(i) for i in breakpoints["PC"]], end = ", ")
                        print("OPCODE:", [hex(i) for i in breakpoints["OPCODE"]], end = ", ")
                        print("MEM_WATCH:", [f"{hex(i)} {breakpoints['MEM_WATCH'][i][0]} {breakpoints['MEM_WATCH'][i][1]}" for i in breakpoints["MEM_WATCH"]], end = ", ")
                        print("REG_WATCH:", [f"{i} {breakpoints['REG_WATCH'][i][0]} {breakpoints['REG_WATCH'][i][1]}" for i in breakpoints["REG_WATCH"]], end = " ")
                        print("}")
                    elif answer[0] == 'x':
                        print("Clearing all breakpoints")
                        breakpoints={"PC":set(), "OPCODE":set(), "MEM_WATCH":{}, "REG_WATCH":{}}
                    elif answer[0] == 't':
                        print(timer)
            if cpu.state == "RUNNING":
                cpu.tick()
            if cpu.state != "STOPPED":
                timer.tick(cpu.cycles)
        except KeyboardInterrupt as e:
            print("Ctrl+C detected")
            debug_level=0
            ctrl_c_counter+=1
            if ctrl_c_counter>1:
                print(e.with_traceback())
                print("Exiting...")
                break
