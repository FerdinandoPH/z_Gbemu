INCLUDE "hardware.inc"

SECTION "Header", ROM0[$100]
    nop
    jp EntryPoint

    ds $150 - @, 0 ; Make room for the header

EntryPoint:
    ld h, $FF
    ld l, $FF
    set 2, [hl]
    ld l, $6
    ld [hl], $0
    ld l, $7
    res 0, [hl]
    res 1, [hl]
    set 2, [hl]
    ei
    halt
    jp EntryPoint
