INCLUDE "hardware.inc"

SECTION "Header", ROM0[$100]
    nop
    jp EntryPoint

    ds $150 - @, 0 ; Make room for the header

EntryPoint:
    di
    call pruebaReti
    jp EntryPoint
pruebaReti:
    reti