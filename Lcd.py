import pygame, time
import numpy as np
from enum import Enum

class Mode(Enum):
    HBLANK = 0
    VBLANK = 1
    OAM = 2
    TRANSFER = 3
class Lcd:
    def __init__(self, mem, scale = 3):
        pygame.init()
        self.enabled = False
        self.window_map_src = 0x9800
        self.window_enabled = False
        self.tile_src = 0x8000
        self.bg_map_src = 0x9800
        self.sprite_height = 8
        self.sprite_enabled = False
        self.bg_window_enabled = True
        self.mem = mem
        self.mode = Mode.VBLANK
        self.ly = 0
        # self.lyc = 0
        # self.stat = 0
        # self.scx = 0
        # self.scy = 0
        # self.wx = 0
        # self.wy = 0
        self.scale = scale
        self.mem.screen = self
        self.line_ticks = 0
        self.tiles = {}
        self.gb_colors = [(0x9B, 0xBC, 0x0F),(0x8B, 0xAC, 0x0F),(0x30, 0x62, 0x30),(0x0F, 0x38, 0x0F)]
        self.main_screen = pygame.display.set_mode(((172+144)*scale, (218)*scale))
        pygame.display.set_caption("zGBEmu")
        self.game_screen = pygame.Surface((160*scale, 144*scale))
        self.debug_screen = pygame.Surface((16*8, 216))
        self.main_screen.fill((255,255,255))
        self.game_screen.fill((0,0,0))
        self.debug_screen.fill((0,0,0))
        self.main_screen.blit(self.game_screen, (0,(216*scale/2)-(144*scale/2)))
        self.writing = False
        self.clock = pygame.time.Clock()
        print("Screen size:", self.main_screen.get_size())
        #time.sleep(3)
    @property
    def stat(self):
        return self.mem[0xFF41]
    @property
    def ly(self):
        return self.mem[0xFF44]
    @ly.setter
    def ly(self, value):
        self.mem.write_unprotected(0xFF44, value & 0xFF)
    @property
    def lyc(self):
        return self.mem[0xFF45]
    @property
    def scx(self):
        return self.mem[0xFF43]
    @property
    def scy(self):
        return self.mem[0xFF42]
    @property
    def wx(self):
        return self.mem[0xFF4B]
    @property
    def wy(self):
        return self.mem[0xFF4A]
    def tick(self):
        pass
    def generate_bg_palette(self):
        palette_table = {0: (0x9B, 0xBC, 0x0F), 1: (0x8B, 0xAC, 0x0F), 2: (0x30, 0x62, 0x30), 3: (0x0F, 0x38, 0x0F)}
        bgp = self.mem[0xFF47]
        bg_palette = [palette_table[(bgp & (0b11 << i*2)) >> i*2] for i in range(4)]
        return bg_palette
    def generate_obj_palette(self, number):
        if number not in range(0,2): number = 0
        palette_table = {0: (0, 0, 0, 0), 1: (0x8B, 0xAC, 0x0F), 2: (0x30, 0x62, 0x30), 3: (0x0F, 0x38, 0x0F)}
        obp = self.mem[0xFF48+number]
        obj_palette = [palette_table[(obp & (0b11 << i*2)) >> i*2] for i in range(4)]
        return obj_palette
    def generate_tiles(self, src = 0x8000, dest = 0x9800):
        tile_arrays = {}
        
        for addr in range(src, dest, 16):
            tile = np.arange(64)
            for y in range(8):
                addr_y = addr + y*2
                lo_byte = self.mem[addr_y]
                hi_byte = self.mem[addr_y+1]
                for x in range(7,-1,-1):
                    mask = 1 << x
                    lo =int(bool(lo_byte & mask))
                    hi =int(bool(hi_byte & mask)) << 1
                    color = hi | lo
                    tile[y*8+(7-x)] = color
            tile_arrays[addr] = tile
        # else:
        #         dbg_tiles=[]
        #         dbg_palette=[(0x9B, 0xBC, 0x0F),(0x8B, 0xAC, 0x0F),(0x30, 0x62, 0x30),(0x0F, 0x38, 0x0F)]
        #         draw_x = 0
        #         draw_y = 0
        #         mini_dbg_screen = pygame.Surface((144, 216))
        #         #y = 0
        #         for addr in range(src, dest, 16):
        #             tile = np.arange(64)
        #             dbg_tile = pygame.Surface((8,8), pygame.SRCALPHA)
        #             #dbg_tile_pxs = pygame.PixelArray(dbg_tile)
        #             for y in range(8):
        #                 addr_y = addr + y*2
        #                 lo_byte = self.mem[addr_y]
        #                 hi_byte = self.mem[addr_y+1]
        #                 for x in range(7,-1,-1):
        #                     mask = 1 << x
        #                     lo =int(bool(lo_byte & mask))
        #                     hi =int(bool(hi_byte & mask)) << 1
        #                     color = hi | lo
        #                     tile[y*8+(7-x)] = color
        #                     dbg_tile.set_at((7-x,y),dbg_palette[color])
        #             # draw_x = 9*(((addr-src)//16)%16)
        #             # draw_y = 9*(((addr-src)//16)//16)
        #             # dbg_tiles.append((dbg_tile, (draw_x,draw_y)))
        #             #dbg_tiles.append((dbg_tile, (9*draw_x, 9*(draw_y//16))))
        #             mini_dbg_screen.blit(dbg_tile, (9*draw_x, 9*(draw_y//16)))
        #             draw_x = (draw_x+1)%16
        #             draw_y +=1
        #             tile_arrays[addr] = tile
        #         self.dbg_tiles = dbg_tiles
        #         self.main_screen.blit(pygame.transform.scale(mini_dbg_screen, (144*self.scale, 216*self.scale)), (171*self.scale, self.scale))
        return tile_arrays
    def generate_colored_tile(self, tile, palette = [(0x9B, 0xBC, 0x0F),(0x8B, 0xAC, 0x0F),(0x30, 0x62, 0x30),(0x0F, 0x38, 0x0F)]):
        tile_surface = pygame.Surface((8,8), pygame.SRCALPHA)
        for y in range(8):
            for x in range(8):
                tile_surface.set_at((x,y),palette[tile[y*8+x]])
        return tile_surface
    def generate_colored_tiles(self,tile_array, src = 0x8000, dest = 0x9800,palette=[(0x9B, 0xBC, 0x0F),(0x8B, 0xAC, 0x0F),(0x30, 0x62, 0x30),(0x0F, 0x38, 0x0F)]):
        tiles = {}
        for addr in range(src, dest, 16):
            tiles[addr] = self.generate_colored_tile(tile_array[addr], palette)
        return tiles
    def update(self):
        self.main_screen.fill((255,255,255))
        #self.tiles = self.generate_tiles()
        self.main_screen.blit(self.debug_screen, (171*self.scale, 0))
        pygame.display.flip()
    def dbg_update(self):
        
        copy_dbg_screen = pygame.Surface((144, 216))
        dbg_palette=[(0x9B, 0xBC, 0x0F),(0x8B, 0xAC, 0x0F),(0x30, 0x62, 0x30),(0x0F, 0x38, 0x0F)]
        draw_x = 0
        draw_y = 0
        for addr in range (0x8000, 0x9800, 16):
            dbg_tile = pygame.Surface((8,8), pygame.SRCALPHA)
            for y in range(8):
                addr_y = addr + y*2
                lo_byte = self.mem[addr_y]
                hi_byte = self.mem[addr_y+1]
                for x in range(7,-1,-1):
                    mask = 1 << x
                    lo =int(bool(lo_byte & mask))
                    hi =int(bool(hi_byte & mask)) << 1
                    color = hi | lo
                    dbg_tile.set_at((7-x,y),dbg_palette[color])
            copy_dbg_screen.blit(dbg_tile, (draw_x*9, (draw_y//16)*9))
            draw_x = (draw_x+1)%16
            draw_y +=1
        self.debug_screen = pygame.transform.scale(copy_dbg_screen.copy(), (144*self.scale, 216*self.scale))

if __name__ == "__main__":
    ui = Lcd(None)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
        pygame.display.flip()
        time.sleep(1/60)