from Cpuold import Cpu
from Memory import Memory
from Timers import Timers
from Lcd import Lcd
import time, threading, pygame
from traceback import print_exc
ctrl_c_counter = 0
def hex(num):
    if num>=0:
        return "0x"+format(num, 'X')
    return "-0x"+format(-num, 'X')
def init(args):
    #global cpu, mem, debug_level, timer, screen, screen_thread, dbg_screen_thread, stop_event
    breakpoints={"PC":set(), "OPCODE":set(), "MEM_WATCH":{}, "REG_WATCH":{}}
    mem = Memory(0x10000)
    debug_level = 0
    mem.load_rom(args.rom)
    cpu = Cpu(mem)
    mem.cpu = cpu
    timer = Timers(mem)
    
    dbg_screen_thread = None
    screen = Lcd(mem)
    mem.screen = screen
    stop_event = threading.Event()
    ctrl_c_event = threading.Event()
    reset_event = threading.Event()
    #screen_thread = threading.Thread(target=screen_render, args=(screen,stop_event), daemon=True)
    dbg_screen_thread = threading.Thread(target=dbg_screen_render, args=(screen,stop_event), daemon=True)
    #screen_thread.start()
    dbg_screen_thread.start()
    cpu_thread = threading.Thread(target=main_loop, args=(args,breakpoints,cpu,mem,debug_level,timer,screen,stop_event,ctrl_c_event,reset_event), daemon=True)
    cpu_thread.start()
    ui_loop(args,screen,dbg_screen_thread,cpu_thread,stop_event, ctrl_c_event,reset_event)
def ui_loop(args,screen:Lcd,dbg_screen_thread:threading.Thread,cpu_thread:threading.Thread,stop_event:threading.Event,ctrl_c_event:threading.Event, reset_event:threading.Event):
    def quit(wait_for_cpu=False):
        stop_event.set()
        if wait_for_cpu:cpu_thread.join()
        dbg_screen_thread.join()
        pygame.display.quit()
    clock = pygame.time.Clock()
    while not stop_event.is_set() and not reset_event.is_set():
        try:
            #frame_start = time.perf_counter()
            screen.update()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit()
            clock.tick(59.7)
            #frame_end = time.perf_counter()
            #print("Screen: "+str(frame_end-frame_start))
        except KeyboardInterrupt as e:
            ctrl_c_event.set()
    if reset_event.is_set():
        reset_event.clear()
        quit(True)
        init(args)
def main_loop(args,breakpoints,cpu:Cpu,mem:Memory,debug_level,timer:Timers,screen:Lcd,stop_event:threading.Event,ctrl_c_event:threading.Event, reset_event:threading.Event):
    try:
        #global cpu, mem, debug_level, breakpoints, ctrl_c_counter, timer, screen, stop_event, screen_thread, dbg_screen_thread
        start_time = cpu_start_time = timer_start_time = debug_screen_start_time = breakpoint_start_time = custom_timer_start =0
        cpu_end_time = timer_end_time = debug_screen_end_time = breakpoint_end_time = custom_timer_end = 0
        breakpoints_enabled = False
        is_custom_timer_set = False
        while cpu.state != "QUIT" and not stop_event.is_set():
            if cpu.IME and cpu.state != "STOPPED":
                cpu.check_interrupts(debug_level)
                if cpu.break_on_interrupt and cpu.in_interrupt:
                    debug_level=0
                    end_int = time.perf_counter()
                    print("The interrupt took ",end_int-start_int)
                cpu.in_interrupt = False
            #breakpoint_start_time = time.perf_counter()
            if breakpoints_enabled:
                if cpu.pc in breakpoints["PC"]:
                    debug_level=0
                    print("Breakpoint hit at PC: "+hex(cpu.pc))
                if mem.read_unprotected(cpu.pc) in breakpoints["OPCODE"]:
                    debug_level=0
                    print("Breakpoint hit at opcode: "+hex(mem.read_unprotected(cpu.pc)))
                for address in breakpoints["MEM_WATCH"]:
                    if eval(str(mem.read_unprotected(int(address,16)))+breakpoints["MEM_WATCH"][address][0]+breakpoints["MEM_WATCH"][address][1 if breakpoints["MEM_WATCH"][address][1]!="x" else 2]):
                        debug_level=0
                        print("Memwatch triggered at memory address: "+address,", now the value is: "+hex(mem.read_unprotected(int(address,16))))
                        if breakpoints["MEM_WATCH"][address][1]=="x":
                            breakpoints["MEM_WATCH"][address] = (breakpoints["MEM_WATCH"][address][0], "x", hex(mem.read_unprotected(int(address,16))))
                for reg in breakpoints["REG_WATCH"]:
                    if eval((str(cpu.registers[reg]) if reg!="SP" else str(cpu.sp))+breakpoints["REG_WATCH"][reg][0]+breakpoints["REG_WATCH"][reg][1 if breakpoints["REG_WATCH"][reg][1]!="x" else 2]):
                        debug_level=0
                        print("Regwatch triggered at register: "+reg,", now the value is: "+hex(cpu.registers[reg] if reg!="SP" else cpu.sp))
                        if breakpoints["REG_WATCH"][reg][1]=="x":
                            breakpoints["REG_WATCH"][reg] = (breakpoints["REG_WATCH"][reg][0], "x", hex(cpu.registers[reg] if reg!="SP" else cpu.sp))
            #breakpoint_end_time = time.perf_counter()
            if debug_level<=1:
                end_time = time.perf_counter()
                if is_custom_timer_set:
                    custom_timer_end = time.perf_counter()
                    print(f"Time elapsed since last continue: {custom_timer_end-custom_timer_start}")
                    is_custom_timer_set = False
                    
                #print("Times")
                print("Total: "+str(end_time-start_time))
                #print("CPU: "+str(cpu_end_time-cpu_start_time))
                #print("Timer: "+str(timer_end_time-timer_start_time))
                #print("Debug screen: "+str(debug_screen_end_time-debug_screen_start_time))
                #print("Breakpoints: "+str(breakpoint_end_time-breakpoint_start_time))
                #print("All functions: "+str(breakpoint_start_time - start_time))
                print(timer)
                print(screen.ppu_str())
                print(mem.str_info(),end="")
                print(cpu)
                
                #print("Debug menu")
                if debug_level<1:
                    exit=False
                    while not exit:
                        ctrl_c_counter=0
                        answer = input("Enter command (h for help): ")
                        if len(answer)<1:
                            exit=True
                            continue
                        match answer[0]:
                            case 'h':
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
                                #print("g: Toggle tile debug screen")
                                print("t: See timers")
                            case 'q':
                                exit=True
                                cpu.state="QUIT"
                                print("Quitting...")
                            case 'c':
                                exit=True
                                debug_level=2
                                if cpu.break_on_interrupt:
                                    start_int = time.perf_counter()
                                if is_custom_timer_set:
                                    custom_timer_start = time.perf_counter()
                            case 'r':
                                exit=True
                                print("Resetting...")
                                reset_event.set()
                                cpu.state="QUIT"
                            case 's':
                                exit=True
                            case 'i':
                                pass #Add breakpoint here
                            case 'm':
                                mem.show_memory()
                            case 'p':
                                print(cpu)
                            case 'b':
                                br_help="Usage: b ([i]nstruction|[o]pcode|[m]em watch | [r]eg watch) (address for mem/reg watch if m/r ) (condition for mem/reg watch if m/r) (address|opcode|value|value)"
                                answer=answer.split(" ")
                                answer.pop(0)
                                if len(answer)<1: 
                                    print(br_help)
                                    continue
                                elif len(answer)==1: answer.insert(0,"i")
                                match answer[0]:
                                    case "i":
                                        try:
                                            if int(answer[1],16) not in range(0,0x10000):
                                                raise ValueError
                                            breakpoints["PC"].add(int(answer[1],16))
                                            breakpoints_enabled = True
                                        except ValueError:
                                            print("Invalid address")
                                            print(br_help)
                                    case "o":
                                        try:
                                            if int(answer[1],16) not in range(0,0x100): raise ValueError
                                            breakpoints["OPCODE"].add(int(answer[1],16))
                                            breakpoints_enabled = True
                                        except ValueError:
                                            print("Invalid opcode")
                                            print(br_help)
                                    case "m":
                                        try:
                                            if int(answer[1],16) not in range(0,0x10000): raise ValueError
                                            if answer[2] not in ["<",">","==","<=",">=","!="]: raise ValueError
                                            if answer[3].lower() == "x":
                                                breakpoints["MEM_WATCH"][answer[1]] = (answer[2], answer[3].lower(), hex(mem.read_unprotected(int(answer[1],16)))) 
                                            else:
                                                if int(answer[3],16) not in range(0,256): raise ValueError
                                                breakpoints["MEM_WATCH"][answer[1]] = (answer[2], "0x"+answer[3],  None)
                                            breakpoints_enabled = True
                                        except ValueError:
                                            print("Invalid mem watch")
                                            print(br_help)
                                    case "r":
                                        try:
                                            answer[1]=answer[1].upper()
                                            if answer[1] not in {"A","B","C","D","E","F","H","L","AF","BC","DE","HL","SP"}: raise ValueError
                                            if answer[2] not in ["<",">","==","<=",">=","!="]: raise ValueError
                                            if answer[3].lower() == "x":
                                                breakpoints["REG_WATCH"][answer[1]] = (answer[2], answer[3].lower(), hex(cpu.registers[answer[1]] if answer[1]!="SP" else cpu.sp)) 
                                            else:
                                                if int(answer[3],16) not in (range(0,0x10000) if answer[1] in {"AF","BC","DE","HL", "SP"} else range(0,0x100)): raise ValueError
                                                breakpoints["REG_WATCH"][answer[1]] = (answer[2], "0x"+answer[3], None)
                                            breakpoints_enabled = True
                                        except ValueError:
                                            print("Invalid reg watch")
                                            print(br_help)
                                    case _: print(br_help)
                            case 'd':
                                dbr_help="Usage: d ([i]nstruction|[o]pcode|[m]em watch|[r]eg watch) (address|opcode|address|register)"
                                answer=answer.split(" ")
                                answer.pop(0)
                                if len(answer)<1:
                                    print(dbr_help)
                                    continue
                                elif len(answer)==1: answer.insert(0,"i")
                                match answer[0]:
                                    case "i":
                                        try:
                                            if int(answer[1],16) not in range(0,0x10000): raise ValueError
                                            breakpoints["PC"].remove(int(answer[1],16))
                                            if len(breakpoints["PC"])==0 and len(breakpoints["OPCODE"])==0 and len(breakpoints["MEM_WATCH"])==0 and len(breakpoints["REG_WATCH"])==0:
                                                breakpoints_enabled = False
                                        except (ValueError, KeyError):
                                            print("Invalid address")
                                            print(dbr_help)
                                    case "o":
                                        try:
                                            if int(answer[1],16) not in range(0,0x100): raise ValueError
                                            breakpoints["OPCODE"].remove(int(answer[1],16))
                                            if len(breakpoints["PC"])==0 and len(breakpoints["OPCODE"])==0 and len(breakpoints["MEM_WATCH"])==0 and len(breakpoints["REG_WATCH"])==0:
                                                breakpoints_enabled = False
                                        except (ValueError, KeyError):
                                            print("Invalid opcode")
                                            print(dbr_help)
                                    case "m":
                                        try:
                                            if int(answer[1],16) not in range(0,0x10000): raise ValueError
                                            del(breakpoints["MEM_WATCH"][answer[1]])
                                            if len(breakpoints["PC"])==0 and len(breakpoints["OPCODE"])==0 and len(breakpoints["MEM_WATCH"])==0 and len(breakpoints["REG_WATCH"])==0:
                                                breakpoints_enabled = False
                                        except (ValueError, KeyError):
                                            print("Invalid mem watch")
                                            print(dbr_help)
                                    case "r":
                                        try:
                                            answer[1]=answer[1].upper()
                                            if answer[1] not in {"A","B","C","D","E","F","H","L","AF","BC","DE","HL", "SP"}: raise ValueError
                                            del(breakpoints["REG_WATCH"][answer[1]])
                                            if len(breakpoints["PC"])==0 and len(breakpoints["OPCODE"])==0 and len(breakpoints["MEM_WATCH"])==0 and len(breakpoints["REG_WATCH"])==0:
                                                breakpoints_enabled = False
                                        except (ValueError, KeyError):
                                            print("Invalid reg watch")
                                            print(dbr_help)
                                    case _: print(dbr_help)
                            case 'w':
                                print("Breakpoints: {",end = " ")
                                print("PC:", [hex(i) for i in breakpoints["PC"]], end = ", ")
                                print("OPCODE:", [hex(i) for i in breakpoints["OPCODE"]], end = ", ")
                                print("MEM_WATCH:", [f"{i} {breakpoints['MEM_WATCH'][i][0]} {breakpoints['MEM_WATCH'][i][1]}"+(f" ({breakpoints['MEM_WATCH'][i][2]})" if breakpoints['MEM_WATCH'][i][2] is not None else "") for i in breakpoints["MEM_WATCH"]], end = ", ")
                                print("REG_WATCH:", [f"{i} {breakpoints['REG_WATCH'][i][0]} {breakpoints['REG_WATCH'][i][1]}"+(f" ({breakpoints['REG_WATCH'][i][2]})" if breakpoints['REG_WATCH'][i][2] is not None else "") for i in breakpoints["REG_WATCH"]], end = " ")
                                print("}")
                            case 'x':
                                print("Clearing all breakpoints")
                                breakpoints={"PC":set(), "OPCODE":set(), "MEM_WATCH":{}, "REG_WATCH":{}}
                                breakpoints_enabled = False
                            case 't':
                                print("A timer will be set at continue")
                                is_custom_timer_set = True
                            case 'k':
                                cpu.break_on_interrupt = not cpu.break_on_interrupt
                                print("Break on interrupt: "+str(cpu.break_on_interrupt))
                            case 'g':
                                mem.load_state()
            start_time = time.perf_counter()
            if cpu.state == "RUNNING":
                #cpu_start_time = time.perf_counter()
                cpu.tick()
                #cpu_end_time = time.perf_counter()
                #print(cpu_end_time-cpu_start_time)
            timer.tick(4*cpu.cycles)
            for i in range(cpu.cycles):
                screen.tick()
            if mem.dma_active:
                mem.dma_tick(cpu.cycles)
            if ctrl_c_event.is_set():
                ctrl_c_event.clear()
                print("Ctrl+C detected")
                debug_level=0
                ctrl_c_counter+=1
                if ctrl_c_counter>1:
                    print_exc()
                    print("Exiting...")
                    cpu.state = "QUIT"
    except Exception as e:
        print_exc()
    stop_event.set()
def dbg_screen_render(screen: Lcd, stop_event):
    while not stop_event.is_set():
        frame_start = time.perf_counter()
        screen.dbg_update()
        frame_end = time.perf_counter()
        #print("Debug screen: "+str(frame_end-frame_start))
        time.sleep(max(0, 1/5 - (frame_end - frame_start)))
# def quit():
#     global screen_thread, stop_event, screen, dbg_screen_thread, debug_level
#     stop_event.set()
#     screen_thread.join()
#     dbg_screen_thread.join()
#     screen = None
#     dbg_screen_thread = None
#     screen_thread = None
#     cpu.state = "QUIT"
#     pygame.display.quit()