INCLUDE "hardware.inc"
SECTION "38", ROM0[$38]
    add sp, $2
    jp EntryPoint
SECTION "Header", ROM0[$100]
    nop
    jp EntryPoint

    ds $150 - @, 0 ; Make room for the header

EntryPoint:
    rst $38