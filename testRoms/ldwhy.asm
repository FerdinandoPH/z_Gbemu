INCLUDE "hardware.inc"

SECTION "Header", ROM0[$100]
    nop
    jp EntryPoint

    ds $150 - @, 0 ; Make room for the header

EntryPoint:
    ld a, $0
    bit 6, a
    ld a, $40
    bit 6, a
    jr nz, EntryPoint