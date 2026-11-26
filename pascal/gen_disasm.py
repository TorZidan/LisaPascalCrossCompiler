"""MC68000 disassembler mixin for the Lisa Pascal Code Generator."""

from __future__ import annotations

from lisalib import i8, i16, i32, pdelete, u32

_HEX_CH = '0123456789ABCDEF'
_COND_CC = 'T F HILSCCCSNEEQVCVSPLMIGELTGTLE'


class DisasmMixin:
    """Motorola 68000 CPU disassembler."""

    def Disassembler(
        self,
        FudgeDest: int,
        Binary: bytes | bytearray | memoryview,
        start_offset: int = 0,
        use_lookup: bool = False,
    ) -> tuple[int, str, str]:
        """Decode one MC68000 instruction from Binary[start_offset:] into (byte_len, opcode, operand).

        Substitutes external symbol names via self.LkUp when use_lookup is True and
        appends resolved branch/PC-relative target comments adjusted by FudgeDest.
        Invalid opcodes consume 2 bytes and return ('$$$$', '').
        """
        Start: int = start_offset
        Pc: int = 0
        W: int = 0
        B6: int = 0
        B5: int = 0
        B4: int = 0
        B3: int = 0
        Bad: bool = False
        HaveDest: bool = False
        DestAddr: int = 0
        Opcode: str = ''
        Operand: str = ''
        bin_len: int = len(Binary)

        def Addr32(a: int) -> int:
            return i32(a)

        def NxtWord() -> int:
            """Fetch the next big-endian 16-bit word from Binary and advance Pc by 2."""
            nonlocal Pc
            idx = Start + Pc
            hi = Binary[idx] & 0xFF if 0 <= idx < bin_len else 0
            lo = Binary[idx + 1] & 0xFF if 0 <= idx + 1 < bin_len else 0
            Pc += 2
            return (hi << 8) | lo

        def SExt16(v: int) -> int:
            return i16(v)

        def SExt8(v: int) -> int:
            return i8(v)

        def Illegal() -> None:
            nonlocal Bad
            Bad = True

        def AppCh(c: str) -> None:
            nonlocal Operand
            Operand += c

        def App(s: str) -> None:
            nonlocal Operand
            Operand += s

        def Opc(s: str) -> None:
            nonlocal Opcode
            Opcode += s

        def Comma() -> None:
            AppCh(',')

        def Hex1(v: int) -> None:
            AppCh(_HEX_CH[v & 15])

        def Hex2(v: int) -> None:
            u = u32(v)
            Hex1(u >> 4)
            Hex1(u)

        def Hex4(v: int) -> None:
            u = u32(v)
            Hex2(u >> 8)
            Hex2(u)

        def DataReg(r: int) -> None:
            AppCh('D')
            AppCh(chr(ord('0') + (r & 7)))

        def AddrReg(r: int) -> None:
            AppCh('A')
            AppCh(chr(ord('0') + (r & 7)))

        def MakeReg(r: int) -> None:
            if (r & 8) != 0:
                AddrReg(r)
            else:
                DataReg(r)

        def AppSize(sz: int) -> None:
            s = sz & 3
            if s == 0:
                Opc('.B')
            elif s == 2:
                Opc('.L')
            else:
                Opc('.W')

        def MakeImm(sz: int) -> None:
            AppCh('#')
            AppCh('$')
            if (sz & 3) == 2:
                Hex4(NxtWord())
            Hex4(NxtWord())

        def ShortIm(v: int) -> None:
            AppCh('#')
            AppCh('$')
            Hex1(v)

        def AppDotL(Ext: int) -> None:
            if (Ext & 0x800) != 0:
                App('.L')
            else:
                App('.W')

        def RegList(Mask: int) -> None:
            """Format a 16-bit MOVEM register mask as slash-separated registers and ranges (reversing for -(An))."""
            nonlocal Operand
            m = Mask & 0xFFFF
            if B5 == 4:
                rev = 0
                for i in range(16):
                    if (m & (1 << i)) != 0:
                        rev |= 1 << (15 - i)
                m = rev
            kmin = 1
            for k in range(16):
                if k == 8:
                    kmin = 9
                if k == 0:
                    Pair = 0
                elif k == 1:
                    Pair = 1
                else:
                    Pair = 3 << (k - 2)
                if (m & (1 << k)) != 0:
                    if k > kmin and (m & Pair) == Pair:
                        Operand = pdelete(Operand, len(Operand) - 3, 4)
                        AppCh('-')
                    if k < 8:
                        DataReg(k)
                    else:
                        AddrReg(k)
                    AppCh('/')
            if len(Operand) > 0:
                Operand = pdelete(Operand, len(Operand), 1)

        def LkUp1(Lc: int, Dest: int) -> None:
            """Record a PC-relative destination address and optionally resolve external symbol names via LkUp."""
            nonlocal DestAddr, HaveDest, Operand
            DestAddr = Addr32(Dest)
            HaveDest = True
            if use_lookup:
                Operand = self.LkUp(Addr32(Lc), Addr32(Dest), Operand)

        def PcRelTV(v: int, D2: int) -> None:
            """Append a PC-relative displacement (*+$xxxx or *-$xxxx) relative to the start of the instruction."""
            x = SExt16(v + (Pc - 2))
            if x < 0:
                App('*-$')
                x = -x - D2
            else:
                App('*+$')
                x = x + D2
            Hex4(x)

        def PcRelWd() -> int:
            """Read a signed 16-bit PC-relative displacement word and append its formatted offset."""
            v = SExt16(NxtWord())
            PcRelTV(v, 0)
            return v

        def EffAddr(Mode: int, Reg: int, Long: bool) -> None:
            """Decode and append an MC68000 effective-address operand from 3-bit Mode and Reg fields."""
            def LpAnRp() -> None:
                AppCh('(')
                MakeReg(Reg + 8)
                AppCh(')')

            if Mode == 0:
                DataReg(Reg)
            elif Mode == 1:
                AddrReg(Reg)
            elif Mode == 2:
                LpAnRp()
            elif Mode == 3:
                LpAnRp()
                AppCh('+')
            elif Mode == 4:
                AppCh('-')
                LpAnRp()
            elif Mode == 5:
                AppCh('$')
                Hex4(NxtWord())
                LpAnRp()
            elif Mode == 6:
                AppCh('$')
                Ext = NxtWord()
                Hex2(Ext & 0xFF)
                AppCh('(')
                MakeReg(Reg + 8)
                Comma()
                MakeReg(Ext >> 12)
                AppDotL(Ext)
                AppCh(')')
            elif Mode == 7:
                if Reg == 0:
                    AppCh('$')
                    Hex4(NxtWord())
                elif Reg == 1:
                    AppCh('$')
                    Hex4(NxtWord())
                    Hex4(NxtWord())
                elif Reg == 2:
                    v = PcRelWd()
                    LkUp1(Start + (Pc - 2), Start + (Pc - 2 + v))
                elif Reg == 3:
                    Ext = NxtWord()
                    v = SExt8(Ext)
                    PcRelTV(v, 0)
                    LkUp1(Start + (Pc - 2), Start + (Pc - 2 + v))
                    AppCh('(')
                    MakeReg(Ext >> 12)
                    AppDotL(Ext)
                    AppCh(')')
                elif Reg == 4:
                    if Long:
                        MakeImm(2)
                    else:
                        MakeImm(1)
                else:
                    Illegal()

        def LongSz() -> bool:
            return (B4 & 3) == 2

        def Ea56F() -> None:
            EffAddr(B5, B6, False)

        def EaLong() -> None:
            EffAddr(B5, B6, LongSz())

        def CommaEf() -> None:
            Comma()
            Ea56F()

        def CommaLn() -> None:
            Comma()
            EaLong()

        def CommaD3() -> None:
            Comma()
            DataReg(B3)

        def CommaD6() -> None:
            Comma()
            DataReg(B6)

        def Ea2D3() -> None:
            Ea56F()
            CommaD3()

        def D4EaLng() -> None:
            AppSize(B4)
            EaLong()

        def DataEa() -> None:
            DataReg(B3)
            CommaLn()

        def DeAnEaD() -> None:
            AppSize(B4)
            if (W & 0x100) != 0:
                DataEa()
            else:
                EaLong()
                CommaD3()

        def AOrSBcd() -> None:
            if B5 == 1:
                EffAddr(4, B6, LongSz())
                Comma()
                EffAddr(4, B3, LongSz())
            else:
                DataReg(B6)
                CommaD3()

        def EaAddr() -> None:
            if B4 == 7:
                EffAddr(B5, B6, True)
            else:
                Ea56F()
            Comma()
            AddrReg(B3)

        def BitOpc() -> None:
            b = B4 & 3
            if b == 0:
                Opc('BTST')
            elif b == 1:
                Opc('BCHG')
            elif b == 2:
                Opc('BCLR')
            elif b == 3:
                Opc('BSET')

        def CondName(Prefix: str) -> None:
            """Append Prefix ('B', 'DB', or 'S') followed by the 4-bit MC68000 condition mnemonic."""
            c = (W >> 8) & 15
            s = _COND_CC[c * 2 : c * 2 + 2]
            if s[1] == ' ':
                s = s[0]
            if Prefix == 'B':
                if c == 0:
                    s = 'RA'
                elif c == 1:
                    s = 'SR'
            Opc(Prefix + s)

        def ShiftName(n: int) -> None:
            """Append the shift or rotate mnemonic (ASR/ASL/LSR/LSL/ROXR/ROXL/ROR/ROL) for code n."""
            s = n & 7
            if s == 0:
                Opc('ASR')
            elif s == 1:
                Opc('ASL')
            elif s == 2:
                Opc('LSR')
            elif s == 3:
                Opc('LSL')
            elif s == 4:
                Opc('ROXR')
            elif s == 5:
                Opc('ROXL')
            elif s == 6:
                Opc('ROR')
            elif s == 7:
                Opc('ROL')

        def Case0() -> None:
            """Decode line-0 instructions: bit manipulation (BTST/BCHG/BCLR/BSET), MOVEP, and immediate ALU ops."""
            if (W & 0x100) != 0:
                if B5 == 1:
                    Opc('MOVEP')
                    AppSize((B4 & 1) + 1)
                    if (W & 0x80) != 0:
                        DataReg(B3)
                        Comma()
                        EffAddr(5, B6, False)
                    else:
                        EffAddr(5, B6, False)
                        CommaD3()
                else:
                    BitOpc()
                    DataReg(B3)
                    CommaEf()
            else:
                if B3 in (0, 1, 5):
                    if B3 == 0:
                        Opc('ORI')
                    elif B3 == 1:
                        Opc('ANDI')
                    elif B3 == 5:
                        Opc('EORI')
                    AppSize(B4)
                    MakeImm(B4)
                    Comma()
                    if B5 == 7 and B6 == 4:
                        if (B4 & 3) != 0:
                            App('SR')
                        else:
                            App('CCR')
                    else:
                        EaLong()
                elif B3 in (2, 3, 6):
                    if B3 == 2:
                        Opc('SUBI')
                    elif B3 == 3:
                        Opc('ADDI')
                    elif B3 == 6:
                        Opc('CMPI')
                    AppSize(B4)
                    MakeImm(B4)
                    CommaLn()
                elif B3 == 4:
                    BitOpc()
                    EffAddr(7, 4, False)
                    CommaEf()
                elif B3 == 7:
                    Illegal()

        def Case4() -> None:
            """Decode line-4 miscellaneous instructions (LEA, PEA, CHK, MOVEM, LINK/UNLK, JSR/JMP, RTS, unary ALU)."""
            if B4 == 6:
                Opc('CHK')
                Ea2D3()
            elif B4 == 7:
                Opc('LEA')
                EffAddr(B5, B6, True)
                Comma()
                AddrReg(B3)
            else:
                b4_3 = B4 & 3
                if B3 == 0:
                    if b4_3 == 3:
                        Opc('MOVE')
                        App('SR')
                        CommaEf()
                    else:
                        Opc('NEGX')
                        D4EaLng()
                elif B3 == 1:
                    if b4_3 == 3:
                        Illegal()
                    else:
                        Opc('CLR')
                        D4EaLng()
                elif B3 == 2:
                    if b4_3 == 3:
                        Opc('MOVE')
                        Ea56F()
                        Comma()
                        App('CCR')
                    else:
                        Opc('NEG')
                        D4EaLng()
                elif B3 == 3:
                    if b4_3 == 3:
                        Opc('MOVE')
                        Ea56F()
                        Comma()
                        App('SR')
                    else:
                        Opc('NOT')
                        D4EaLng()
                elif B3 == 4:
                    if b4_3 == 0:
                        Opc('NBCD')
                        Ea56F()
                    elif b4_3 == 1:
                        if B5 == 0:
                            Opc('SWAP')
                            DataReg(B6)
                        else:
                            Opc('PEA')
                            Ea56F()
                    elif b4_3 in (2, 3):
                        if B5 == 0:
                            if b4_3 == 2:
                                Opc('EXT.W')
                            else:
                                Opc('EXT.L')
                            DataReg(B6)
                        else:
                            if b4_3 == 2:
                                Opc('MOVEM.W')
                            else:
                                Opc('MOVEM.L')
                            RegList(NxtWord())
                            CommaEf()
                elif B3 == 5:
                    if b4_3 == 3:
                        Opc('TAS')
                        Ea56F()
                    else:
                        Opc('TST')
                        D4EaLng()
                elif B3 == 6:
                    Opc('MOVEM')
                    AppSize((B4 & 1) + 1)
                    Mask = NxtWord()
                    Ea56F()
                    Comma()
                    RegList(Mask)
                elif B3 == 7:
                    if b4_3 == 0:
                        Illegal()
                    elif b4_3 == 1:
                        if (B5 & 6) == 0:
                            Opc('TRAP')
                            ShortIm(W)
                        else:
                            if B5 == 2:
                                Opc('LINK')
                                AddrReg(B6)
                                Comma()
                                EffAddr(7, 4, False)
                            elif B5 == 3:
                                Opc('UNLK')
                                AddrReg(B6)
                            elif B5 == 4:
                                Opc('MOVE')
                                AddrReg(B6)
                                Comma()
                                App('USP')
                            elif B5 == 5:
                                Opc('MOVE')
                                App('USP')
                                Comma()
                                AddrReg(B6)
                            elif B5 == 6:
                                if B6 == 0:
                                    Opc('RESET')
                                elif B6 == 1:
                                    Opc('NOP')
                                elif B6 == 2:
                                    Opc('STOP')
                                    EffAddr(7, 4, False)
                                elif B6 == 3:
                                    Opc('RTE')
                                elif B6 == 4:
                                    Illegal()
                                elif B6 == 5:
                                    Opc('RTS')
                                elif B6 == 6:
                                    Opc('TRAPV')
                                elif B6 == 7:
                                    Opc('RTR')
                            else:
                                Illegal()
                    elif b4_3 == 2:
                        Opc('JSR')
                        Ea56F()
                    elif b4_3 == 3:
                        Opc('JMP')
                        Ea56F()

        def Case5() -> None:
            """Decode line-5 ADDQ, SUBQ, Scc, and DBcc instructions."""
            if (B4 & 3) == 3:
                if B5 == 1:
                    CondName('DB')
                    DataReg(B6)
                    Comma()
                    EffAddr(7, 2, False)
                else:
                    CondName('S')
                    Ea56F()
            else:
                if (W & 0x100) != 0:
                    Opc('SUBQ')
                else:
                    Opc('ADDQ')
                AppSize(B4)
                n = B3 if B3 != 0 else 8
                ShortIm(n)
                CommaLn()

        def Case6() -> None:
            """Decode line-6 short and word-displacement BRA, BSR, and Bcc branch instructions."""
            CondName('B')
            if (W & 0xFF) != 0:
                Opc('.S')
                v = SExt8(W)
                PcRelTV(v, 2)
                LkUp1(Start + Pc, Start + (Pc + v))
            else:
                v = PcRelWd()
                LkUp1(Start + (Pc - 2), Start + (Pc - 2 + v))

        def Case7() -> None:
            """Decode line-7 MOVEQ #imm8,Dn instructions."""
            if (W & 0x100) != 0:
                Illegal()
            else:
                Opc('MOVEQ')
                if (W & 0x80) != 0:
                    App('#-$')
                else:
                    App('#$')
                Hex2(W & 0x7F)
                CommaD3()

        def Case8() -> None:
            """Decode line-8 OR, DIVU, DIVS, and SBCD instructions."""
            if (W & 0x1F0) == 0x100:
                Opc('SBCD')
                AOrSBcd()
            elif B4 == 7:
                Opc('DIVS')
                Ea2D3()
            elif B4 == 3:
                Opc('DIVU')
                Ea2D3()
            else:
                Opc('OR')
                DeAnEaD()

        def IsAddSubX() -> bool:
            return ((W & 0x100) != 0) and ((W & 0x30) == 0) and ((W & 0xC0) != 0xC0)

        def Case9() -> None:
            """Decode line-9 SUB, SUBA, and SUBX instructions."""
            if IsAddSubX():
                Opc('SUBX')
                AppSize(B4)
                AOrSBcd()
            elif B4 == 3:
                Opc('SUBA.W')
                EaAddr()
            elif B4 == 7:
                Opc('SUBA.L')
                EaAddr()
            else:
                Opc('SUB')
                DeAnEaD()

        def CaseA() -> None:
            """Decode line-A ($Axxx) Lisa intrinsic-unit jump-table instructions (IUJSR/IUJMP/IULEA/IUPEA)."""
            k = (B3 // 2) & 3
            if k == 0:
                Opc('IUJSR')
            elif k == 1:
                Opc('IUJMP')
            elif k == 2:
                Opc('IULEA')
            elif k == 3:
                Opc('IUPEA')
            AppCh('$')
            if k == 2:
                l_val = (((W & 0x7F) * 65536) + NxtWord()) * 2
                Hex4(u32(l_val) >> 16)
                Hex4(l_val)
                Comma()
                AddrReg((W >> 7) & 7)
            else:
                Hex4(W & 0xFF)
                Hex4(NxtWord())

        def CaseB() -> None:
            """Decode line-B CMP, CMPA, CMPM, and EOR instructions."""
            if ((W & 0x100) != 0) and (B5 == 1) and ((W & 0xC0) != 0xC0):
                Opc('CMPM')
                AppSize(B4)
                EffAddr(3, B6, False)
                Comma()
                EffAddr(3, B3, False)
            elif ((W & 0x100) != 0) and ((W & 0xC0) != 0xC0):
                Opc('EOR')
                AppSize(B4)
                DataEa()
            elif B4 == 3:
                Opc('CMPA.W')
                EaAddr()
            elif B4 == 7:
                Opc('CMPA.L')
                EaAddr()
            else:
                Opc('CMP')
                AppSize(B4)
                EaLong()
                CommaD3()

        def CaseC() -> None:
            """Decode line-C AND, MULU, MULS, ABCD, and EXG instructions."""
            if B4 == 5 and B5 == 0:
                Opc('EXG')
                DataReg(B3)
                CommaD6()
            elif B4 == 5 and B5 == 1:
                Opc('EXG')
                AddrReg(B3)
                Comma()
                AddrReg(B6)
            elif B4 == 6 and B5 == 1:
                Opc('EXG')
                DataReg(B3)
                Comma()
                AddrReg(B6)
            elif (W & 0x1F0) == 0x100:
                Opc('ABCD')
                AOrSBcd()
            elif B4 == 7:
                Opc('MULS')
                Ea2D3()
            elif B4 == 3:
                Opc('MULU')
                Ea2D3()
            else:
                Opc('AND')
                DeAnEaD()

        def CaseD() -> None:
            """Decode line-D ADD, ADDA, and ADDX instructions."""
            if IsAddSubX():
                Opc('ADDX')
                AppSize(B4)
                AOrSBcd()
            elif B4 == 3:
                Opc('ADDA.W')
                EaAddr()
            elif B4 == 7:
                Opc('ADDA.L')
                EaAddr()
            else:
                Opc('ADD')
                DeAnEaD()

        def CaseE() -> None:
            """Decode line-E register and memory shift/rotate instructions."""
            if (B4 & 3) == 3:
                ShiftName((W >> 8) & 7)
                AppSize(1)
                Ea56F()
            else:
                n = (B5 & 3) * 2
                if (W & 0x100) != 0:
                    n += 1
                ShiftName(n)
                AppSize(B4)
                if (W & 0x20) != 0:
                    DataReg(B3)
                else:
                    cnt = B3 if B3 != 0 else 8
                    ShortIm(cnt)
                CommaD6()

        def Try2Dis() -> None:
            """Read the primary opcode word and dispatch on its top 4 bits (lines $0..$F)."""
            nonlocal Opcode, Operand, Bad, W, B6, B5, B4, B3
            Opcode = ''
            Operand = ''
            Bad = False
            W = NxtWord()
            B6 = W & 7
            B5 = (W >> 3) & 7
            B4 = (W >> 6) & 7
            B3 = (W >> 9) & 7
            top = W >> 12
            if top == 0:
                Case0()
            elif top == 1:
                Opc('MOVE.B')
                Ea56F()
                Comma()
                EffAddr(B4, B3, False)
            elif top == 2:
                Opc('MOVE.L')
                EffAddr(B5, B6, True)
                Comma()
                EffAddr(B4, B3, True)
            elif top == 3:
                Opc('MOVE.W')
                Ea56F()
                Comma()
                EffAddr(B4, B3, False)
            elif top == 4:
                Case4()
            elif top == 5:
                Case5()
            elif top == 6:
                Case6()
            elif top == 7:
                Case7()
            elif top == 8:
                Case8()
            elif top == 9:
                Case9()
            elif top == 10:
                CaseA()
            elif top == 11:
                CaseB()
            elif top == 12:
                CaseC()
            elif top == 13:
                CaseD()
            elif top == 14:
                CaseE()
            elif top == 15:
                Illegal()

        Try2Dis()
        if Bad:
            Pc = 2
            Opcode = '$$$$'
            Operand = ''
        elif HaveDest:
            while True:
                AppCh(' ')
                if len(Operand) >= 16:
                    break
            AppCh(';')
            AppCh(' ')
            DestAddr = i32(u32(DestAddr) + u32(FudgeDest))
            Hex4(u32(DestAddr) >> 16)
            Hex4(DestAddr)

        return Pc, Opcode, Operand
