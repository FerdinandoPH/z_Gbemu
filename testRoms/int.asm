INCLUDE "hardware.inc"
SECTION "ROM Bank $050", ROM0[$50]
    call RestartEverything
    inc a
    jp EntryPoint

SECTION "Header", ROM0[$100]
    nop
    jp EntryPoint

    ds $150 - @, 0 ; Make room for the header

EntryPoint:
    ld l, $FF
    ld h, $FF
    set 2, [hl]
    ld l, $07
    set 0, [hl]
    set 2, [hl]
    ei
    nop
    halt
RestartEverything:
    res 2, [hl]
    res 0, [hl]
    ld l, $FF
    res 2, [hl]
    ret