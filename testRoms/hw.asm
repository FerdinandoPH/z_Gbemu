INCLUDE "hardware.inc"

SECTION "Header", ROM0[$100]
    nop
    jp EntryPoint

    ds $150 - @, 0 ; Make room for the header

EntryPoint:
    ; ld c, $3
    ; ld h, $5
    ; ld l, $6
    ; ld a, b
    ; ld l, $50
    ; ld h, $01
    ; ld a, [HLI]
    ; ld a, [BC]
    ; ld b, [HL]
    ; ld a, [$0100]
    ; ld [c], a
    ; ld a, [DE]
    ; ld a, [c]
    ; ld H, $FF
    ; ld a, $AB
    ; ld [HLD], a
    ; ld [HL], $FE
    ; use ldh
    inicio:
    ld h, $01
    ld c,h
    ld l, $3
    call miniFunc
    jr inicio
miniFunc:
    ld a, [hld]
    ld a, l
    cp a, $0
    jp nz, miniFunc
    ret