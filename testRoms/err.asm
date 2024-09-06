INCLUDE "hardware.inc"

SECTION "Header", ROM0[$100]
    nop
    jp EntryPoint

    ds $150 - @, 0 ; Make room for the header

EntryPoint:
    ld h, $FF
    ld l, $E1
    ld [hl], $F0
    ld a, $10
    add a, [hl]
    jr c, EntryPoint