from Cpu import Cpu
from Memory import Memory
global breakpoints
breakpoints={"PC":set(), "OPCODE":set(), "MEM_WATCH":{}}
def init(args):
    global cpu, mem, debug_level
    mem = Memory()
    debug_level = 0
    mem.load_rom(args.rom)
    cpu = Cpu(mem)
    main_loop(args)
def main_loop(args):
    global cpu, mem, debug_level, breakpoints
    while cpu.running:
        if cpu.pc in breakpoints["PC"]:
            debug_level=0
            print("Breakpoint hit at PC: "+hex(cpu.pc))
        if mem.memory[cpu.pc] in breakpoints["OPCODE"]:
            debug_level=0
            print("Breakpoint hit at opcode: "+hex(cpu.mem[cpu.pc]))
        for address in breakpoints["MEM_WATCH"]:
            if eval(str(mem.memory[address])+breakpoints["MEM_WATCH"][address][0]+breakpoints["MEM_WATCH"][address][1]):
                debug_level=0
                print("Breakpoint hit at memory address: "+hex(address),", now the value is: "+str(mem.memory[address]))
        if debug_level<=0:
            exit=False
            print(cpu)
            #print("Debug menu")
            while not exit:
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
                elif answer[0]=='q':
                    exit=True
                    cpu.running=False
                elif answer[0]=='c':
                    exit=True
                    debug_level=1
                elif answer[0]=='r':
                    exit=True
                    init(args)
                elif answer[0]=='s':
                    exit=True
                elif answer[0] == 'i':
                    exit=True #Add breakpoint here
                elif answer[0]=='m':
                    mem.dump()
                elif answer[0]=='p':
                    print(cpu)
                elif answer[0]=='b':
                    br_help="Usage: b ([i]nstruction|[o]pcode|[m]em watch) (address for mem watch if m ) (condition for mem watch if m) (address|opcode|value)"
                    answer=answer.split(" ")
                    answer.pop(0)
                    if len(answer)<1: 
                        print(br_help)
                        continue
                    elif len(answer)==1: answer.insert(0,"i")
                    if answer[0]=="i":
                        try:
                            if int(answer[1],16)<0 or int(answer[1],16)>0xFFFF:
                                raise ValueError
                            breakpoints["PC"].append(int(answer[1],16))
                        except ValueError:
                            print("Invalid address")
                            print(br_help)
                    elif answer[0]=="o":
                        try:
                            if int(answer[1],16)<0 or int(answer[1],16)>0xFF: raise ValueError
                            breakpoints["OPCODE"].append(int(answer[1],16))
                        except ValueError:
                            print("Invalid opcode")
                            print(br_help)
                    elif answer[0]=="m":
                        try:
                            if int(answer[1],16)<0 or int(answer[1],16)>0xFF: raise ValueError
                            if answer[2] not in ["<",">","==","<=",">=","!="]: raise ValueError
                            if answer[3].lower() == "x": answer[3] = mem.memory[answer[1]]
                            if not answer[3].isdigit(): raise ValueError
                            breakpoints["MEM_WATCH"][answer[1]] = (answer[2], answer[3])
                        except ValueError:
                            print("Invalid mem watch")
                            print(br_help)
                    else: print(br_help)
                elif answer[0] == 'd':
                    dbr_help="Usage: d ([i]nstruction|[o]pcode|[m]em watch) (address|opcode|address)"
                    answer=answer.split(" ")
                    answer.pop(0)
                    if len(answer)<1:
                        print(dbr_help)
                        continue
                    elif len(answer)==1: answer.insert(0,"i")
                    if answer[0]=="i":
                        try:
                            if int(answer[1],16)<0 or int(answer[1],16)>0xFFFF: raise ValueError
                            breakpoints["PC"].remove(int(answer[1],16))
                        except ValueError:
                            print("Invalid address")
                            print(dbr_help)
                    elif answer[0]=="o":
                        try:
                            if int(answer[1],16)<0 or int(answer[1],16)>0xFF: raise ValueError
                            breakpoints["OPCODE"].remove(int(answer[1],16))
                        except ValueError:
                            print("Invalid opcode")
                            print(dbr_help)
                    elif answer[0]=="m":
                        try:
                            if int(answer[1],16)<0 or int(answer[1],16)>0xFF: raise ValueError
                            del(breakpoints["MEM_WATCH"][answer[1]])
                        except ValueError:
                            print("Invalid mem watch")
                            print(dbr_help)
                    else: print(dbr_help)
                elif answer[0] == 'w':
                    print(breakpoints)
                elif answer[0] == 'x':
                    print("Clearing all breakpoints")
                    breakpoints={"PC":set(), "OPCODE":set(), "MEM_WATCH":{}}
        cpu.tick()