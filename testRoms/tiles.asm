INCLUDE "hardware.inc"
SECTION "ROM Bank $050", ROM0[$50]
    add sp, $2
    jp TimerInt
SECTION "Header", ROM0[$100]
    nop
    jp EntryPoint

    ds $150 - @, 0 ; Make room for the header
EntryPoint:

    ld a, $00
    Init:
    ld h, $80
    ld l, $00
    ClearRam:
    ld [hli], a
    push af
    ld a, h
    cp $90
    jr z, Change
    pop af
    jr ClearRam
    Change:
    ld a, $00
    IntStart:
    ld h, $FF
    ld l, $FF
    set 2, [hl]
    ld l, $07
    set 2, [hl]
    ei
    nop
    halt
    SetNext:
    pop af
    cp a, $00
    jr z, setFF
    ld a, $00
    jp Init
    setFF:
    ld a, $FF
    jp Init
    TimerInt:
    ld l, $07
    res 2, [hl]
    ld l, $05
    ld [hl], $00
    inc a
    cp a, $A
    jr z, StartSetNext
    jp IntStart
    StartSetNext:
    ld l, $07
    res 2, [hl]
    ld l, $05
    ld [hl], $00
    jp SetNext
