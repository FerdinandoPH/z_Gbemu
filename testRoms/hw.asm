INCLUDE "hardware.inc"

SECTION "Header", ROM0[$100]

    jp EntryPoint

    ds $150 - @, 0 ; Make room for the header

EntryPoint:
    ld a, $FF
    ld b, $1
    ld c, $2
    ld d, $3
    ld e, $4
    ld h, $5
    ld l, $6
    ld a, $0
    ld a, b
    ld l, $50
    ld h, $01
    ld a, [HLI]
    ld a, [BC]
    ld b, [HL]
    ld a, [$0100]
    jp EntryPoint