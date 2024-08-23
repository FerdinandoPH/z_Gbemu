import sdl2, sdl2.ext, time
from copy import deepcopy
class Ui:
    def __init__(self, memory, scale = 4):
        sdl2.ext.init()
        self.scale = scale
        self.mem = memory
        self.gb_colors = [0xFF9BBC0F, 0xFF8BAC0F, 0xFF306230, 0xFF0F380F]
        self.debug_tiles = {}
    def init_debug_screen(self):
        self.tile_debug_window = sdl2.ext.Window("Tile Debug", size=(16*8*self.scale, 32*8*self.scale), flags=sdl2.SDL_WINDOW_SHOWN)
        self.tile_debug_renderer = sdl2.ext.Renderer(self.tile_debug_window)
        self.tile_debug_screen = sdl2.SDL_CreateRGBSurface(0, (16 * 8 * self.scale) + (16 * self.scale), (32 * 8 * self.scale) + (64 * self.scale), 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
        self.tile_debug_texture = sdl2.SDL_CreateTexture(self.tile_debug_renderer.sdlrenderer, sdl2.SDL_PIXELFORMAT_ARGB8888, sdl2.SDL_TEXTUREACCESS_STREAMING, (16 * 8 * self.scale) + (16 * self.scale), (32 * 8 * self.scale) + (64 * self.scale))
    def display_tile(self, surface, addr, tileNum, x, y):
        #start_display = time.perf_counter()
        base = addr + (tileNum * 16)
        mem = self.mem
        scale = self.scale
        colors = self.gb_colors
        for tileY in range(0, 16, 2):
            byte1 = mem[base + tileY]
            byte2 = mem[base + tileY + 1]
            for bit in range(7, -1, -1):
                hi = int(bool(byte1 & (1 << bit))) << 1
                lo = int(bool(byte2 & (1 << bit)))
                color = (hi | lo)
                rc = sdl2.SDL_Rect(x + ((7 - bit) * scale), y + (tileY // 2 * scale), scale, scale)
                sdl2.SDL_FillRect(surface, rc, colors[color])
        #end_display = time.perf_counter()
        #print(f"Display time: {end_display - start_display}")

    def update_dbg_window(self):
        #render_start_time = time.perf_counter()
        xDraw, yDraw, tileNum = 0, 0, 0
        rect = sdl2.SDL_Rect(0, 0, self.tile_debug_screen.contents.w, self.tile_debug_screen.contents.h)
        sdl2.SDL_FillRect(self.tile_debug_screen, rect, 0xFFFFFFFF)
        addr = 0x8000
        for y in range(24):
            for x in range(16):
                self.display_tile(self.tile_debug_screen, addr, tileNum, xDraw + (x*self.scale), yDraw + (y*self.scale))
                xDraw += 8*self.scale
                tileNum += 1
            yDraw += 8*self.scale
            xDraw = 0
        #functions_start = time.perf_counter()
        sdl2.SDL_UpdateTexture(self.tile_debug_texture, None, self.tile_debug_screen.contents.pixels, self.tile_debug_screen.contents.pitch)
        sdl2.SDL_RenderClear(self.tile_debug_renderer.sdlrenderer)
        sdl2.SDL_RenderCopy(self.tile_debug_renderer.sdlrenderer, self.tile_debug_texture, None, None)
        sdl2.SDL_RenderPresent(self.tile_debug_renderer.sdlrenderer)
        #functions_end = time.perf_counter()
        #print(f"Functions time: {functions_end - functions_start}")
        #render_end_time = time.perf_counter()
        #print(f"Render time: {render_end_time - render_start_time}")
        #event_start_time = time.perf_counter()
        events = sdl2.ext.get_events()
        thing = False
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                break
        else:
            thing = True
        #event_end_time = time.perf_counter()
        #print(f"Event time: {event_end_time - event_start_time}")
        return thing
