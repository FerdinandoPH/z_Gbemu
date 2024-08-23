INCLUDE "hardware.inc"

SECTION "Header", ROM0[$100]
    nop
    jp EntryPoint

    ds $150 - @, 0 ; Make room for the header

EntryPoint:
    ld a, $4
    rra
    ld h,$01
    ld l, $50
    jp hl