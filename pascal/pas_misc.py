"""Source I/O, scanner, diagnostics, constants, symbol table, I-code output, and pass-1 driver."""

from __future__ import annotations

import struct
import sys
from typing import Optional

from frontend_base import (
    AccessKind,
    ALFALEN,
    AllBegSys,
    Attr,
    BlockBegSy,
    BuffBlockSize,
    BuffByteSize,
    CondState,
    ConstBegSys,
    DecBegSys,
    DeclKind,
    FacBegSys,
    IdDecBegSys,
    InbufBLockSize,
    InbufByteSize,
    InlineCode,
    InputFileTypes,
    MaxCondDepth,
    MaxErrs,
    MAXFILES,
    N,
    NameClass,
    NodeKind,
    PFkind,
    SetValRec,
    Stmt,
    StmtTypes,
    StrValRec,
    Symbol,
    T,
    TypeForms,
    UnitKind,
    Valu,
    Where,
)
from lisalib import (
    AbortCompilation,
    IOCloseKind,
    IODevType,
    IOModes,
    IONewline,
    LisaCloseOpt,
    SUBell,
    SUCr,
    SUEsc,
    SUMaxStrLeng,
    alfa8,
    f32,
    i16,
    i32,
    odd,
    p_f32,
    pcopy,
    pdelete,
    pdiv,
    pget_ch,
    pmod,
    ppos,
    pround,
    pset_ch,
    ptrunc,
    u16,
    u8,
)

MaxFpString = 80
MemAvailWords = 32767

_MULT_OPS = frozenset({
    Symbol.DIVSY,
    Symbol.STARSY,
    Symbol.MODSY,
    Symbol.ANDSY,
    Symbol.SLASHSY,
})
_ADD_OPS = frozenset({
    Symbol.PLUSSY,
    Symbol.MINUSSY,
    Symbol.ORSY,
})
_REL_OPS = frozenset({
    Symbol.LTSY,
    Symbol.GTSY,
    Symbol.LESY,
    Symbol.GESY,
    Symbol.EQSY,
    Symbol.NESY,
    Symbol.INSY,
})
_CONST_STD_KEYS = frozenset({1, 3, 9, 10, 12, 14, 17, 26, 32})


def _lower_alfa(name: str) -> str:
    """Convert `name` to an 8-character blank-padded `Alfa` string with uppercase letters folded to lowercase."""
    return ''.join(chr(ord(c) + 32) if 'A' <= c <= 'Z' else c for c in alfa8(name))


class MiscMixin:
    """Front-end scanner, file stack, error/listing reporter, constant evaluator,
    symbol table, buffered I-code output, and unit/program compilation driver."""

    # ========================================================================
    # 1. Source file stack, listing/error reporting, lexer, directives, and type helpers
    # ========================================================================

    def _p_abort_flag(self) -> bool:
        """Return True if the runtime abort flag (`pAbortFlag`) has been set."""
        return bool(getattr(self.rt, 'pAbortFlag', False))

    def OpenNewFile(self, Filename: str, FileType: InputFileTypes) -> bool:
        """Save the current input file state and push a new `.TEXT` or `USES` `.OBJ` file onto `OpenFileStack`.
        Initializes buffered reading after the 1024-byte header page (block 2) and returns True on success."""
        # Remember all relevant information about current sourcefile
        if self.TopOfOpenFileStack != 0:
            cur = self.OpenFileStack[self.TopOfOpenFileStack]
            cur.NextChToRead = self.InbufP
            cur.LastValidByte = self.InbufLastValidByte
            cur.NumValidBlocks = self.InbufNumValidBlocks
            cur.SrcEolSource = self.EolSource
            # Save the contents of the input buffer. If previously stacked file
            # has saved buffer then invalidate it (there is only one save buffer)
            if self.TopOfOpenFileStack > 1:
                self.OpenFileStack[self.TopOfOpenFileStack - 1].BufSaved = False
            cur.BufSaved = True
            self.SaveInbufP[:] = self.Inbuf
            cur.pCurL = self.pCurLine
            self.CurLine = self.CurLine[:max(0, self.pCurLine)]
            cur.CurL = self.CurLine
            cur.PrevL = self.PrevLine
            cur.LineNbr = self.LineNumber
            cur.PrevLnbr = self.PrevLn
            cur.LPrinted = self.LinePrinted
            cur.ErrIdx = self.ErrIndex
            i = 1
            while i <= self.ErrIndex:
                cur.ErrLst[i] = self.ErrList[i].copy()
                i += 1
            self.ErrIndex = 0

        # Push file on OpenFileStack
        if self.TopOfOpenFileStack == MAXFILES:
            self.Error(304)
            return False

        self.TopOfOpenFileStack += 1

        # Source and Include files must be .TEXT files.
        # 'Uses' files may end in .OBJ.
        # File-open error fatal except in 'Uses' case.
        if FileType == InputFileTypes.INCLUDED or FileType == InputFileTypes.SOURCE:
            Filename, _ = self.rt.SUAddExtension(Filename, '.TEXT', SUMaxStrLeng)

        top_entry = self.OpenFileStack[self.TopOfOpenFileStack]
        self.rt.reset_untyped(top_entry.SrcFile, Filename)

        if self.rt.io_result > 0:
            if FileType == InputFileTypes.INCLUDED or FileType == InputFileTypes.SOURCE:
                # exit with IORESULT > 0!!
                self.TopOfOpenFileStack -= 1
                return False
            else:
                # filetype = used
                Filename = Filename + '.OBJ'

            self.rt.reset_untyped(top_entry.SrcFile, Filename)
            if self.rt.io_result > 0:
                # filetype = used; exit with IORESULT > 0!!
                self.TopOfOpenFileStack -= 1
                return False

        top_entry.LastRelBlkRead = 2 - InbufBLockSize  # next read will start at block 2
        top_entry.NextChToRead = 0
        top_entry.FName = Filename
        self.EolSource = True
        top_entry.BufSaved = False
        self.InbufLastValidByte = InbufByteSize - 1
        self.InbufP = InbufByteSize
        self.LinePrinted = True
        self.LineNumber = 0
        return True

    def PreviousFile(self) -> None:
        """Close the current input file, pop `OpenFileStack`, and restore the previous file's line, error, and buffer state.
        Re-reads the saved block group from disk if the single save buffer was invalidated by deeper nesting."""
        if self.TopOfOpenFileStack > 1:
            self.rt.close_untyped(self.OpenFileStack[self.TopOfOpenFileStack].SrcFile)
            self.TopOfOpenFileStack -= 1
            entry = self.OpenFileStack[self.TopOfOpenFileStack]
            # during this pop, merge current errors with pushed errors
            if (entry.ErrIdx + self.ErrIndex) > MaxErrs:
                # cut back the current error list
                self.ErrIndex = MaxErrs - entry.ErrIdx
                self.ErrList[self.ErrIndex].Nbr = 352  # too many errors
                self.ErrList[self.ErrIndex].Name = '        '
            j = self.ErrIndex
            self.ErrIndex = entry.ErrIdx + self.ErrIndex
            i = self.ErrIndex
            while j > 0:
                self.ErrList[i] = self.ErrList[j].copy()
                i -= 1
                j -= 1
            i = 1
            while i <= entry.ErrIdx:
                self.ErrList[i] = entry.ErrLst[i].copy()
                i += 1
            self.LinePrinted = entry.LPrinted
            self.LineNumber = entry.LineNbr
            self.PrevLn = entry.PrevLnbr
            self.pCurLine = entry.pCurL
            self.CurLine = entry.CurL
            self.PrevLine = entry.PrevL
            self.InbufP = entry.NextChToRead
            self.InbufLastValidByte = entry.LastValidByte
            self.InbufNumValidBlocks = entry.NumValidBlocks
            self.EolSource = entry.SrcEolSource
            if entry.BufSaved:
                self.Inbuf[:] = self.SaveInbufP
            elif (
                self.rt.block_read(
                    entry.SrcFile,
                    self.Inbuf,
                    self.InbufNumValidBlocks,
                    entry.LastRelBlkRead,
                )
                != self.InbufNumValidBlocks
            ):
                # Fatal error in rereading previously read block-group
                self.Error(406)
                raise AbortCompilation()

    def FilePos(self) -> tuple[int, int]:
        """Return the current `(block, byte)` position within the active source or `.OBJ` unit interface file."""
        block = self.OpenFileStack[self.TopOfOpenFileStack].LastRelBlkRead + pdiv(self.InbufP, 512)
        byte = pmod(self.InbufP, 512)
        return block, byte

    def FileSeek(self, Block: int) -> None:
        """Position the active input file so the next `FillInbuf` reads starting at 512-byte `Block` (e.g. for `.OBJ` `InterfLoc`)."""
        self.OpenFileStack[self.TopOfOpenFileStack].LastRelBlkRead = Block - InbufBLockSize
        self.InbufLastValidByte = InbufByteSize
        self.InbufP = InbufByteSize

    def NextPg(self) -> None:
        """Advance `InbufP` to the next 1024-byte UCSD/Lisa text page boundary, refilling `Inbuf` if needed."""
        if self._p_abort_flag():
            self.KillExec()
            self.Aborted = True
            raise AbortCompilation()
        self.InbufP = pdiv(self.InbufP, 1024) * 1024 + 1024  # advance to next UCSD textpage
        if self.InbufP > self.InbufLastValidByte:
            self.FillInbuf()

    def FillInbuf(self) -> None:
        """Read the next group of 512-byte blocks into `Inbuf`, popping `OpenFileStack` on nested EOF or placing ETX (`0x03`) at root EOF."""
        while True:  # LABEL 1
            if self.InbufLastValidByte < InbufByteSize - 1:
                self.InbufLastValidByte = 0  # previous read got all the blocks
            else:
                top_entry = self.OpenFileStack[self.TopOfOpenFileStack]
                self.InbufNumValidBlocks = self.rt.block_read(
                    top_entry.SrcFile,
                    self.Inbuf,
                    InbufBLockSize,
                    top_entry.LastRelBlkRead + InbufBLockSize,
                )
                self.InbufLastValidByte = 512 * self.InbufNumValidBlocks - 1
                io_err = self.rt.io_result
                if io_err > 0:
                    self.rt.IOError(io_err, '*** FATAL I/O ERROR ***')
                    self.Error(406)
                    raise AbortCompilation()

            if self.InbufLastValidByte <= 0:
                # Top of stack read failed
                if self.TopOfOpenFileStack == 1:
                    # EOF
                    self.InbufP = 0
                    self.Inbuf[0] = 3
                    if self.EofLn < 0:
                        # capture last line in case of errors
                        self.EofLn = self.TotalLines
                        self.EofLine = self.PrevLine
                    return
                else:
                    self.PreviousFile()
                    # Block just reread might have just hit last <CR> before it was pushed
                    if self.InbufP > self.InbufLastValidByte:
                        continue  # GOTO 1
                    if self.Inbuf[self.InbufP] == 0:
                        self.NextPg()
                    return
            else:
                # Top of stack read succeeded
                self.OpenFileStack[self.TopOfOpenFileStack].LastRelBlkRead += InbufBLockSize
                self.InbufP = 0
                return

    def ListLine(self, TotalLines: int) -> int:
        """Format and write the current source line (with line numbers, include depth, and nesting markers) to the listing file."""
        if self.CondStack[self.CondTos] >= CondState.MATCHELSE:
            # line is being conditionally skipped
            self.Left = ' '
            self.Right = ' '
            self.ProcLev = ' '

        self.CurLine = self.CurLine[:max(0, self.pCurLine)]
        t_str = self.rt.PutIntP(TotalLines, 5)
        line_image = (t_str + self.rt.PutIntP(self.LineNumber, 8) + '      ' + self.CurLine)[:SUMaxStrLeng]
        if self.TopOfOpenFileStack > 1:
            line_image = pset_ch(line_image, 8, chr(ord('0') + (self.TopOfOpenFileStack - 1)))
        line_image = pset_ch(line_image, 15, self.Left)
        line_image = pset_ch(line_image, 16, self.Right)
        line_image = pset_ch(line_image, 18, self.ProcLev)

        if self.ListingFCBP is not None:
            self.rt.PutLineS(self.ListingFCBP, line_image)

        TotalLines = TotalLines + 1
        self.TotalLines = TotalLines
        self.LinePrinted = True

        if self._p_abort_flag():
            self.KillExec()
            self.Aborted = True
            raise AbortCompilation()

        return TotalLines

    def _get_err_text(self, msg_nbr: int) -> str:
        """Look up `msg_nbr` in the big-endian `PASERRS.ERR` directory and return the formatted diagnostic string."""
        err_msg = f'*** Error {self.rt.PutIntP(msg_nbr, 3)} ***'

        if not self.MsgFileOpen:
            io_status = self.rt.SUSysReset(self.MsgFile, 'PASERRS.ERR')
            if io_status > 0:
                temp_str = ' Error message file "PasErrs.Err" not available.'
                return (err_msg + temp_str)[:SUMaxStrLeng]
            self.MsgFileOpen = True

        raw_blk = bytearray(512)

        def get_block(n: int) -> Optional[int]:
            """Read 512-byte block `n` from `PASERRS.ERR` into `raw_blk`, returning `n` or `None` on I/O failure."""
            nonlocal err_msg
            k = self.rt.block_read(self.MsgFile, raw_blk, 1, n)
            if self.rt.io_result > 0 or k != 1:
                temp_str = ' Bad block read on error message file "PasErrs.Err".'
                err_msg = (err_msg + temp_str)[:SUMaxStrLeng]
                return None
            return n

        def get_msg_idx() -> Optional[int]:
            """Search the `(msg_nbr, byte_offset)` index at the start of `PASERRS.ERR` for `msg_nbr`."""
            blk_n = get_block(0)
            if blk_n is None:
                return None
            num_errs = struct.unpack_from('>h', raw_blk, 0)[0]
            cur_idx = 2
            j = 1
            while j <= num_errs:
                if cur_idx > 255:
                    blk_n = get_block(blk_n + 1)
                    if blk_n is None:
                        return None
                    cur_idx = 0
                entry_nbr = struct.unpack_from('>h', raw_blk, 2 * cur_idx)[0]
                if entry_nbr == msg_nbr:
                    return struct.unpack_from('>h', raw_blk, 2 * (cur_idx + 1))[0]
                cur_idx += 2
                j += 1
            return None

        msg_idx = get_msg_idx()
        if msg_idx is None:
            return err_msg

        err_msg, _ = self.rt.SUAddCh(err_msg, ' ', SUMaxStrLeng)
        block_n = get_block(pdiv(msg_idx, 512))
        if block_n is None:
            return err_msg
        cur_pos = pmod(msg_idx, 512)

        end_msg = False
        while not end_msg:
            if cur_pos > 511:
                block_n = get_block(block_n + 1)
                if block_n is None:
                    return err_msg
                cur_pos = 0
            b_val = raw_blk[cur_pos]
            if b_val == 0:
                end_msg = True
            else:
                err_msg, overflow = self.rt.SUAddCh(err_msg, chr(b_val), SUMaxStrLeng)
                if overflow:
                    end_msg = True
                cur_pos += 1

        return err_msg

    def ListErrors(self) -> None:
        """Output queued source-line diagnostics and `?` column pointers to active outputs, with optional `ProgComm` handoff to the Editor."""
        first_msg = ''
        first_pos = 0
        last_pos = 0
        next_msg = ''

        def setup_for_editor() -> None:
            """Write the first error message, file name, and token coordinates to `For Editor` via `ProgComm` and schedule the Editor."""
            nonlocal first_msg
            self.rt.PCReWrite(self.rt.PCText, 'For Editor')
            idx = ppos(' *** ', first_msg)
            if idx > 4:
                first_msg = pdelete(first_msg, 1, idx + 4)
            if len(first_msg) < 95:
                first_msg = first_msg + ' ' * (95 - len(first_msg))
            ok = self.rt.PCPutLine(first_msg)
            if ok:
                ok = self.rt.PCPutLine(self.OpenFileStack[self.TopOfOpenFileStack].FName)
                if ok:
                    idx = first_pos
                    while idx > 0:
                        c = pget_ch(self.CurLine, idx)
                        if ('A' <= c <= 'Z') or ('a' <= c <= 'z') or ('0' <= c <= '9') or c in ('_', '%'):
                            idx -= 1
                        else:
                            break
                    line_str = self.rt.PutIntP(self.LineNumber, 1)
                    col_str = self.rt.PutIntP(first_pos + 1, 1)
                    ok = self.rt.PCPutLine(
                        f'{line_str} {self.rt.PutIntP(idx + 1, 1)} {line_str} {col_str}'
                    )
            if not self.rt.PCClose(False, 'For Editor'):
                ok = False
            if ok:
                self.rt.PCSetRunCmd(self.Ecmd)
            else:
                sys.stdout.write(f'{SUBell}Unable to set up communication to the Editor.\n')
            self.Aborted = True

        def show(m: str) -> None:
            """Write formatted error message `m` to the error file, listing file, and console."""
            if self.ErrFileOpen:
                self.ErrFile.writeln(m)
            if self.Listing and self.ListingFCBP is not None:
                self.rt.PutLineS(self.ListingFCBP, m)
            if not self.ConsListing:
                sys.stdout.write(m + '\n')

        def point(pos: int) -> None:
            """Write a `?` caret line aligned to column `pos` across active diagnostic outputs."""
            nonlocal last_pos
            q_line = '?'.rjust(max(1, 5 + pos))
            if self.ErrFileOpen:
                self.ErrFile.writeln(q_line)
            if self.Listing and self.ListingFCBP is not None:
                self.rt.PutStrS(self.ListingFCBP, '?', 19 + pos)
                self.rt.PutcF(self.ListingFCBP, IONewline)
            if not self.ConsListing:
                sys.stdout.write(q_line + '\n')
            last_pos = pos

        if self.TotalLines == self.EofLn:
            self.CurLine = self.EofLine

        if not self.ConsListing:
            if self.PrevLn != 0:
                sys.stdout.write(f'{self.PrevLn:4d} {self.PrevLine}\n')
            if self.TotalLines != self.LastErrLn:
                sys.stdout.write(f'{self.LineNumber:4d} {self.CurLine}\n')

        if self.ErrFileOpen:
            if self.PrevLn != 0:
                self.ErrFile.writeln(f'{self.PrevLn:4d} {self.PrevLine}')
            if self.TotalLines != self.LastErrLn:
                self.ErrFile.writeln(f'{self.LineNumber:4d} {self.CurLine}')

        self.LastErrLn = self.TotalLines

        err_idx = self.ErrIndex
        self.ErrIndex = 0  # in case we go to 999, and for next line

        for i in range(1, err_idx + 1):
            err = self.ErrList[i]
            if self._p_abort_flag():
                self.Aborted = True
                raise AbortCompilation()

            msg = self._get_err_text(err.Nbr)

            if err.Name != '        ':
                msg, _ = self.rt.SUAddCh(msg, ' ', SUMaxStrLeng)
                for j in range(1, ALFALEN + 1):
                    msg, _ = self.rt.SUAddCh(msg, pget_ch(err.Name, j), SUMaxStrLeng)
                msg = self.rt.SUTrimBlanks(msg)

            msg, _ = self.rt.SUAddCh(msg, '.', SUMaxStrLeng)

            if i == 1:
                point(err.Pos)
                next_msg = msg
                first_msg = msg
                first_pos = err.Pos
            elif msg == next_msg and err.Pos != last_pos:
                point(err.Pos)
            elif msg != next_msg and err.Pos == last_pos:
                show(next_msg)
                next_msg = msg
            elif msg != next_msg and err.Pos != last_pos:
                show(next_msg)
                next_msg = msg
                point(err.Pos)

        show(next_msg)

        file_msg = f'*** File {self.OpenFileStack[self.TopOfOpenFileStack].FName} ***'
        if self.Listing and self.ListingFCBP is not None:
            self.rt.PutLineS(self.ListingFCBP, file_msg)
        if not self.ConsListing:
            sys.stdout.write(file_msg + '\n')
        if self.ErrFileOpen:
            self.ErrFile.writeln(file_msg)

        if not (self.Listing or self.ErrFileOpen):
            if self.CallEditor:
                setup_for_editor()
                raise AbortCompilation()
            else:
                sys.stdout.write('Type SPACE to continue, CLEAR to exit, E to call Editor.')
                sys.stdout.flush()
                while True:
                    ch = self.rt.SUGetCh()
                    got_response = ch in (' ', SUCr, SUEsc, 'e', 'E')
                    if not got_response:
                        sys.stdout.write(SUBell)
                        sys.stdout.flush()
                    else:
                        sys.stdout.write('\n')
                        if ch == SUEsc:
                            self.Aborted = True
                            raise AbortCompilation()
                        if ch in ('e', 'E'):
                            setup_for_editor()
                            raise AbortCompilation()
                        break

    def NextCh(self) -> None:
        """Read the next source character into `Ch`, flushing completed listing/error lines on `EolSource`.
        Skips NUL page padding via `NextPg` and expands DLE (`0x10`) run-length leading spaces into `CurLine`."""
        if self.EolSource:
            self.EolSource = False
            self.CurLine = self.CurLine[:max(0, self.pCurLine)]
            if not self.LinePrinted:
                if self.Listing:
                    self.TotalLines = self.ListLine(self.TotalLines)
                else:
                    self.TotalLines += 1
            if self.ErrIndex != 0:
                self.ListErrors()
            self.PrevLn = self.LineNumber
            self.PrevLine = self.CurLine
            self.LineNumber += 1
            self.Left = '-'
            self.Right = '-'
            self.ProcLev = ' '
            if self.InbufP > self.InbufLastValidByte:
                self.FillInbuf()
            if self.Inbuf[self.InbufP] == 0:  # NULL
                self.NextPg()
            self.pCurLine = 0
            self.CurLine = ''
            if self.Inbuf[self.InbufP] == 16:  # DLE
                self.pCurLine = self.Inbuf[self.InbufP + 1] - 32
                if self.pCurLine > 150:
                    self.pCurLine = 150
                if self.pCurLine > 0:
                    self.CurLine = ' ' * self.pCurLine
                self.InbufP += 2  # Need to skip blanks at beginning of line
            self.LinePrinted = False

        # Pick up the next character in Inbuf
        ch_byte = self.Inbuf[self.InbufP]
        self.Ch = chr(ch_byte)
        self.InbufP += 1

        # If this character is the <CR>, it gets special treatment
        if ch_byte == 13:
            self.Ch = ' '
            self.EolSource = True
        elif self.pCurLine < 150:
            self.pCurLine += 1
            self.CurLine = pset_ch(self.CurLine, self.pCurLine, self.Ch)

    def Scan(self) -> None:
        """Scan the next lexical token into `Token` (and `Ident`, `IntVal`, `RealVal`, or `StrVal`).
        Processes comments, `$` compiler options, include files, and `$IFC`/`$ELSEC`/`$ENDC`/`$SETC` conditional compilation."""

        def hex_constant() -> None:
            """Scan a `$`-prefixed hex constant into `IntVal` (sign-extending 1-4 digit `$8000..$FFFF` words) or emit `DOLLARSY`."""
            self.IntVal = 0
            n_digits = 0
            self.NextCh()
            l_ch = self.Ch if self.Ch < 'a' else chr(ord(self.Ch) - 32)
            while ('0' <= l_ch <= '9') or ('A' <= l_ch <= 'F'):
                if 0 <= self.IntVal <= 268435455:
                    k_val = ord(l_ch) - ord('0')
                    if l_ch >= 'A':
                        k_val -= 7
                    self.IntVal = i32(self.IntVal * 16 + k_val)
                else:
                    self.Error(12)
                    self.IntVal = 0
                n_digits += 1
                self.NextCh()
                l_ch = self.Ch if self.Ch < 'a' else chr(ord(self.Ch) - 32)
            if n_digits > 0:
                self.Token = Symbol.ICONSTSY
                if n_digits <= 4:
                    # <= 4 digits, make two's complement word
                    if 32768 <= self.IntVal <= 65535:
                        self.IntVal -= 65536
            else:
                self.Token = Symbol.DOLLARSY

        def unsigned_number() -> None:
            """Scan an unsigned decimal integer (`ICONSTSY`) or real literal (`RCONSTSY`), handling `..` and `.)` lookahead."""
            digits = ['\x00'] * (MaxFpString + 1)
            error10 = False
            self.Token = Symbol.ICONSTSY
            k = 0
            while self.Ch == '0':
                self.NextCh()  # ignore leading zeros
            digital = self.ChClass[ord(self.Ch)] == Symbol.DIGITCL

            def concat_ch() -> None:
                """Append `Ch` to the numeric `digits` buffer and advance to the next character."""
                nonlocal k, digital, error10
                if k < MaxFpString:
                    k += 1
                    digits[k] = self.Ch
                elif not error10:
                    error10 = True
                    self.Error(10)  # not enough room in buffer
                self.NextCh()
                digital = self.ChClass[ord(self.Ch)] == Symbol.DIGITCL

            while digital:
                concat_ch()
            if self.Ch == '.':
                concat_ch()
                if self.Ch == '.':
                    # woops - meant :
                    self.Ch = ':'
                    self.DotFlag = True
                    k -= 1
                elif self.Ch == ')':
                    self.Ch = ']'
                    k -= 1
                else:
                    # decimal point detected
                    self.Token = Symbol.RCONSTSY
                    if not digital:
                        self.Error(11)
                    while digital:
                        concat_ch()
            if self.Ch == 'E' or self.Ch == 'e':
                concat_ch()
                self.Token = Symbol.RCONSTSY
                if self.Ch == '+' or self.Ch == '-':
                    concat_ch()
                if not digital:
                    self.Error(13)
                while digital:
                    concat_ch()
            if self.Token == Symbol.ICONSTSY:
                self.IntVal = 0
                if k > 0:
                    if k > 10:
                        self.Error(12)
                    else:
                        max_k = 9 if k > 9 else k
                        self.IntVal = ord(digits[1]) - 48
                        for idx in range(2, max_k + 1):
                            self.IntVal = 10 * self.IntVal + ord(digits[idx]) - 48
                        if k == 10:
                            if self.IntVal >= 214748365 or (
                                self.IntVal == 214748364 and digits[10] > '8'
                            ):
                                self.Error(12)
                                self.IntVal = 0
                            else:
                                self.IntVal = i32(self.IntVal * 10 + ord(digits[10]) - 48)
            else:
                digits_str = ''.join(digits[1:k + 1])
                self.RealVal = p_f32(digits_str)

        def get_string() -> None:
            """Scan a single-quoted character (`CCONSTSY`) or string literal (`SCONSTSY`), unescaping doubled quotes."""
            l_str_val: Optional[StrValRec] = None
            str_len_mod = 0
            l_int_val = 0
            self.IntVal = 0
            done = False

            def concat_str() -> None:
                """Append `Ch` to the single-character value or chained 8-byte `StrValRec` segments."""
                nonlocal l_str_val, str_len_mod, l_int_val
                if self.IntVal == 0:
                    l_int_val = ord(self.Ch)
                else:
                    if self.IntVal == 1:
                        self.StrVal = StrValRec(pset_ch('        ', 1, chr(l_int_val)), None)
                        l_str_val = self.StrVal
                        str_len_mod = 1
                    assert l_str_val is not None
                    if str_len_mod == ALFALEN:
                        nxt = StrValRec('        ', None)
                        l_str_val.Next = nxt
                        l_str_val = nxt
                        str_len_mod = 0
                    str_len_mod += 1
                    l_str_val.StrPart = pset_ch(l_str_val.StrPart, str_len_mod, self.Ch)
                self.IntVal += 1

            while not done:
                if self.EolSource:
                    self.Error(14)
                else:
                    self.NextCh()
                while self.Ch != "'":
                    concat_str()
                    if self.EolSource:
                        self.Error(14)
                        self.Ch = "'"
                    else:
                        self.NextCh()
                self.NextCh()  # Found first ', is there another
                if self.Ch == "'":
                    concat_str()  # Double '
                else:
                    done = True

            if self.IntVal == 1:
                self.IntVal = l_int_val
                self.Token = Symbol.CCONSTSY
            else:
                self.Token = Symbol.SCONSTSY

        def comment(term_ch: str) -> bool:
            """Scan a `{...}` or `(*...*)` comment and process `$` compiler options and `$IFC`/`$ELSEC`/`$ENDC`/`$SETC` directives.
            Returns True when conditional skipping already consumed and scanned the next active token."""
            end_of_options = False
            option_ch = ' '
            filename = ''
            incl_opt_flag = False
            already_skipping = self.CondStack[self.CondTos] >= CondState.MATCHELSE

            def get_file_name(blanks_ok: bool) -> None:
                """Scan the remainder of a directive up to the comment delimiter into `filename`."""
                nonlocal filename, end_of_options
                j = len(filename)

                def next_file_ch() -> None:
                    """Append `Ch` to `filename` (ignoring spaces unless `blanks_ok`) and advance `Ch`."""
                    nonlocal filename, j
                    if j < SUMaxStrLeng:
                        if blanks_ok or self.Ch != ' ':
                            j += 1
                            filename = filename + self.Ch
                    else:
                        self.Error(351)  # File name too long
                    self.NextCh()

                if term_ch == '*':
                    next_file_ch()
                    while self.Ch != '*' and self.Ch != '\x03':
                        next_file_ch()
                else:
                    while self.Ch != '}' and self.Ch != '\x03':
                        next_file_ch()
                filename = self.rt.SUTrimBlanks(filename)
                end_of_options = True

            def push(s: CondState) -> None:
                """Push conditional compilation state `s` onto `CondStack`."""
                self.CondTos += 1
                self.CondStack[self.CondTos] = s

            def pop() -> None:
                """Pop the top conditional compilation state from `CondStack`."""
                self.CondTos -= 1

            def set_val(a: str, b: int) -> None:
                """Insert or update `$SETC` symbol `a` with 16-bit value `b` in the `CondRoot` binary tree."""
                a_norm = alfa8(a)
                b_val = i16(b)

                def level_check() -> bool:
                    """Ensure `$SETC` appears at program or unit scope, reporting error 260 otherwise."""
                    if self.Level == 1 or (-self.NumUnits <= self.Level <= -1):
                        return True
                    self.Error(260)
                    return False

                def enter() -> Optional[N]:
                    """Create a new `IDENTNODE` entry for `CondRoot` if `level_check` succeeds."""
                    if level_check():
                        fn = N(NodeKind.IDENTNODE)
                        fn.Name = a_norm
                        fn.Llink = None
                        fn.Rlink = None
                        fn.ValueOf.Ivalu = b_val
                        return fn
                    return None

                lpn = self.CondRoot
                if lpn is None:
                    self.CondRoot = enter()
                else:
                    while lpn is not None:
                        if a_norm == lpn.Name:
                            lpn.ValueOf.Ivalu = b_val
                            lpn = None
                        elif a_norm < lpn.Name:
                            if lpn.Llink is None:
                                lpn.Llink = enter()
                                lpn = None
                            else:
                                lpn = lpn.Llink
                        else:
                            if lpn.Rlink is None:
                                lpn.Rlink = enter()
                                lpn = None
                            else:
                                lpn = lpn.Rlink

            def get_val(a: str) -> int:
                """Look up `$SETC` symbol `a` in `CondRoot`, reporting error 261 and defining it as 0 if missing."""
                a_norm = alfa8(a)
                lpn = self.CondRoot
                while lpn is not None:
                    if a_norm == lpn.Name:
                        return i16(lpn.ValueOf.Ivalu)
                    elif a_norm < lpn.Name:
                        lpn = lpn.Llink
                    else:
                        lpn = lpn.Rlink
                self.Error(261)
                set_val(a_norm, 0)
                return 0

            def op_factor() -> int:
                """Parse and evaluate a primary factor in a `$IFC` or `$SETC` expression."""
                while self.Token not in (
                    Symbol.IDENTSY,
                    Symbol.ICONSTSY,
                    Symbol.NOTSY,
                    Symbol.LPARENSY,
                    Symbol.STRINGSY,
                    Symbol.CCONSTSY,
                ):
                    self.Error(262)
                    self.Scan()
                tok = self.Token
                if tok == Symbol.IDENTSY:
                    res = get_val(self.Ident)
                    self.Scan()
                    return res
                elif tok in (Symbol.ICONSTSY, Symbol.CCONSTSY):
                    res = i16(self.IntVal)
                    self.Scan()
                    return res
                elif tok == Symbol.STRINGSY:
                    self.Error(262)
                    self.Scan()
                    return 0
                elif tok == Symbol.NOTSY:
                    self.Scan()
                    return int(not odd(op_factor()))
                else:  # Symbol.LPARENSY
                    self.Scan()
                    res = op_expr()
                    if self.Token != Symbol.RPARENSY:
                        self.Error(262)
                    self.Scan()
                    return res

            def op_term() -> int:
                """Parse and evaluate multiplicative and `AND` operators in a conditional directive expression."""
                left_val = op_factor()
                while self.Token in (
                    Symbol.STARSY,
                    Symbol.SLASHSY,
                    Symbol.DIVSY,
                    Symbol.MODSY,
                    Symbol.ANDSY,
                ):
                    old_sy = self.Token
                    self.Scan()
                    if old_sy == Symbol.STARSY:
                        left_val = i16(left_val * op_factor())
                    elif old_sy in (Symbol.SLASHSY, Symbol.DIVSY):
                        right_val = op_factor()
                        left_val = i16(pdiv(left_val, right_val))
                    elif old_sy == Symbol.MODSY:
                        right_val = op_factor()
                        left_val = i16(pmod(left_val, right_val))
                    elif old_sy == Symbol.ANDSY:
                        # always evaluate RightVal (as Lisa Pascal does), so its tokens are consumed
                        right_val = op_factor()
                        left_val = int(odd(left_val) and odd(right_val))
                return left_val

            def op_simp_expr() -> int:
                """Parse and evaluate unary signs, additive operators, and `OR` in a conditional directive expression."""
                negate = False
                if self.Token in (Symbol.PLUSSY, Symbol.MINUSSY, Symbol.ORSY):
                    negate = self.Token == Symbol.MINUSSY
                    if self.Token == Symbol.ORSY:
                        self.Error(262)
                    self.Scan()
                left_val = op_term()
                if negate:
                    left_val = i16(-left_val)
                while self.Token in (Symbol.PLUSSY, Symbol.MINUSSY, Symbol.ORSY):
                    old_sy = self.Token
                    self.Scan()
                    if old_sy == Symbol.PLUSSY:
                        left_val = i16(left_val + op_term())
                    elif old_sy == Symbol.MINUSSY:
                        left_val = i16(left_val - op_term())
                    elif old_sy == Symbol.ORSY:
                        # always evaluate RightVal (as Lisa Pascal does), so its tokens are consumed
                        right_val = op_term()
                        left_val = int(odd(left_val) or odd(right_val))
                return left_val

            def op_expr() -> int:
                """Parse and evaluate relational operators in a `$IFC` or `$SETC` expression."""
                left_val = op_simp_expr()
                if self.Token in (
                    Symbol.LTSY,
                    Symbol.LESY,
                    Symbol.GESY,
                    Symbol.GTSY,
                    Symbol.NESY,
                    Symbol.EQSY,
                    Symbol.INSY,
                ):
                    old_sy = self.Token
                    self.Scan()
                    if old_sy == Symbol.LTSY:
                        left_val = int(left_val < op_simp_expr())
                    elif old_sy == Symbol.LESY:
                        left_val = int(left_val <= op_simp_expr())
                    elif old_sy == Symbol.GESY:
                        left_val = int(left_val >= op_simp_expr())
                    elif old_sy == Symbol.GTSY:
                        left_val = int(left_val > op_simp_expr())
                    elif old_sy == Symbol.NESY:
                        left_val = int(left_val != op_simp_expr())
                    elif old_sy == Symbol.EQSY:
                        left_val = int(left_val == op_simp_expr())
                    elif old_sy == Symbol.INSY:
                        self.Error(262)
                return left_val

            def eval_expr() -> int:
                """Scan and evaluate a `$IFC` or `$SETC` expression with `ParsingOption` enabled."""
                self.ParsingOption = True
                self.Scan()
                res = op_expr()
                self.ParsingOption = False
                return res

            def scan_for_cond() -> None:
                """Recognize multi-letter `$` directives (`$IFC`, `$ELSEC`, `$ENDC`, `$SETC`, `$OV`, `$OPT`, `$ASM`) and set `option_ch`."""
                nonlocal option_ch, filename, end_of_options

                def setup_op(o_ch: str) -> None:
                    """Assign internal directive code `o_ch` and clear any residual `RBRACKSY` token before `scan_2_end`."""
                    nonlocal option_ch
                    option_ch = o_ch
                    if self.Token == Symbol.RBRACKSY:
                        self.Token = Symbol.LBRACECL

                a_chars = [' '] * ALFALEN
                a_chars[0] = option_ch
                idx = 1
                j = len(filename)
                chk_sign = option_ch in ('A', 'O')  # asm, ov, opt
                while (
                    self.Ch != term_ch
                    and self.Ch != ' '
                    and not (chk_sign and self.Ch in ('-', '+'))
                ):
                    if j < SUMaxStrLeng:
                        j += 1
                        filename = filename + self.Ch
                    if idx < ALFALEN:
                        if 'a' <= self.Ch <= 'z':
                            a_chars[idx] = chr(ord(self.Ch) - 32)
                        else:
                            a_chars[idx] = self.Ch
                        idx += 1
                    self.NextCh()
                a_str = ''.join(a_chars)
                if a_str == 'IFC     ':
                    setup_op('1')
                elif a_str == 'ELSEC   ':
                    setup_op('2')
                elif a_str == 'ENDC    ':
                    setup_op('3')
                elif a_str == 'SETC    ':
                    setup_op('4')
                elif a_str == 'OV      ':
                    setup_op('5')
                elif a_str == 'OPT     ':
                    setup_op('6')
                elif a_str == 'ASM     ':
                    setup_op('7')
                if self.Ch == term_ch:
                    end_of_options = True

            def scan_2_end() -> None:
                """Consume tokens until the matching closing delimiter (`}` or `*)`) ends a `$IFC` or `$SETC` directive."""
                done = False
                while not done:
                    while self.Token != Symbol.RBRACKSY:
                        self.Scan()
                    if term_ch == self.RBrackChar:
                        done = True
                    else:
                        self.Scan()
                self.ParsingOption = False

            goto_1 = False
            self.NextCh()
            if self.Ch == '$':
                end_of_options = False
                while not end_of_options:
                    self.NextCh()
                    if 'a' <= self.Ch <= 'z':
                        self.Ch = chr(ord(self.Ch) - 32)
                    if self.Ch in (
                        '%', 'A', 'C', 'D', 'E', 'F', 'H', 'I',
                        'L', 'M', 'O', 'P', 'R', 'S', 'U', 'X',
                    ):
                        option_ch = self.Ch
                        self.NextCh()

                        filename = ''
                        if option_ch in ('A', 'E', 'I', 'O', 'S') and self.Ch not in (
                            ' ', '+', '-'
                        ):
                            scan_for_cond()

                        # if skipping text then invalidate all but IFC, ELSEC, ENDC metacomments
                        if self.CondStack[self.CondTos] >= CondState.MATCHELSE:
                            if option_ch not in ('1', '2', '3'):
                                option_ch = ' '

                        if option_ch == '%':
                            if self.Ch == '+':
                                self.ChClass[ord('%')] = Symbol.LETCL
                            elif self.Ch == '-':
                                self.ChClass[ord('%')] = Symbol.ERRSY
                            else:
                                end_of_options = True
                        elif option_ch == 'A':
                            if self.Ch in ('+', '-'):
                                self.SaveA2D3 = self.Ch == '+'
                            else:
                                end_of_options = True
                        elif option_ch == 'C':
                            if self.Ch in ('+', '-'):
                                self.CodeFlag = self.Ch == '+'
                            else:
                                end_of_options = True
                        elif option_ch == 'D':
                            if self.Ch in ('+', '-'):
                                self.DbugFlag = self.Ch == '+'
                            else:
                                end_of_options = True
                        elif option_ch == 'E':
                            if self.Ch in ('+', '-'):
                                self.CallEditor = self.Ch == '+'
                            else:
                                if self.ErrFileOpen:
                                    self.rt.close_text(self.ErrFile, LisaCloseOpt.LOCK)
                                if self.Ch != term_ch:
                                    get_file_name(True)
                                filename, _ = self.rt.SUAddExtension(
                                    filename, '.TEXT', SUMaxStrLeng
                                )
                                self.rt.rewrite_text(self.ErrFile, filename)
                                if self.rt.io_result <= 0:
                                    self.ErrFileOpen = True
                                    self.ErrFName = filename
                                else:
                                    self.ErrFileOpen = False
                                    self.Error(411)
                        elif option_ch == 'F':
                            if self.Ch in ('+', '-'):
                                self.ForwChkFlag = self.Ch == '+'
                                self.NextCh()
                                if self.Ch in ('+', '-'):
                                    self.RodFlag = self.Ch == '+'
                                else:
                                    end_of_options = True
                        elif option_ch == 'H':
                            if self.Ch in ('+', '-'):
                                self.HandleCheck = self.Ch == '+'
                            else:
                                end_of_options = True
                        elif option_ch == 'I':
                            if self.Ch in ('+', '-'):
                                self.IOFlag = self.Ch == '+'
                            else:
                                if self.InterFlag:
                                    self.Error(305)
                                if self.Ch != term_ch:
                                    get_file_name(True)
                                incl_opt_flag = True
                        elif option_ch == 'L':
                            if not self.ListingOk:
                                end_of_options = True
                            elif self.Ch in ('+', '-'):
                                self.Listing = (self.Ch == '+') and self.ListOpen
                            else:
                                get_file_name(True)
                                same_name = False
                                if self.ListOpen and self.ListingFCBP is not None:
                                    str1 = self.rt.SUTrimBlanks(self.rt.SUUpStr(filename))
                                    str1, _ = self.rt.SUAddExtension(
                                        str1, '.TEXT', SUMaxStrLeng
                                    )
                                    str2 = self.rt.SUUpStr(self.ListingFCBP.Filename)
                                    if str1 == str2:
                                        same_name = True
                                    else:
                                        self.rt.CloseF(self.ListingFCBP, IOCloseKind.IOLock)
                                        self.Listing = False
                                if not same_name:
                                    r_open, self.ListingFCBP = self.rt.OpenF(
                                        filename,
                                        self.ListingFCBP,
                                        IOModes.IOWrite,
                                        self.ListingBufrP,
                                    )
                                    self.Listing = r_open <= 0
                                if self.Listing and self.ListingFCBP is not None:
                                    self.ConsListing = (
                                        self.ListingFCBP.DevType == IODevType.IOConsDev
                                    )
                                    self.NewListFile = (
                                        self.ListingFCBP.DevType == IODevType.IOBlkDev
                                        and self.AsmListOk
                                        and not same_name
                                    )
                                    self.LastLine = 0
                                else:
                                    self.Error(410)
                                self.ListOpen = self.Listing
                                self.Pass2Listing = (
                                    self.Listing and self.NewListFile and self.AsmListOk
                                )
                        elif option_ch == 'M':
                            if self.Ch in ('+', '-'):
                                self.MacFlag = self.Ch == '+'
                            else:
                                end_of_options = True
                        elif option_ch == 'P':
                            if self.Listing and not self.ConsListing and self.ListingFCBP is not None:
                                self.rt.PutcF(self.ListingFCBP, '\x0c')
                            end_of_options = True
                        elif option_ch == 'R':
                            if self.Ch in ('+', '-'):
                                self.RangeFlag = self.Ch == '+'
                            else:
                                end_of_options = True
                        elif option_ch == 'S':
                            if self.Ch in ('+', '-'):
                                self.SwapFlag = self.Ch == '+'
                            else:
                                if self.Ch != term_ch:
                                    get_file_name(False)
                                self.SegName = alfa8(filename)
                        elif option_ch == 'U':
                            if self.Ch in ('+', '-'):
                                self.SearchLibrary = self.Ch == '+'
                            else:
                                get_file_name(True)
                                if not self.Using:
                                    self.UFname = filename
                        elif option_ch == 'X':
                            if self.Ch in ('+', '-'):
                                self.StkXFlag = self.Ch == '+'
                            else:
                                end_of_options = True
                        elif option_ch == '1':  # IFC
                            if self.CondTos < MaxCondDepth - 1:
                                if self.CondStack[self.CondTos] >= CondState.MATCHELSE:
                                    self.ParsingOption = True
                                    push(CondState.MATCHEND)
                                    push(CondState.MATCHELSE)
                                else:
                                    if odd(eval_expr()):
                                        push(CondState.MATCHEND)
                                        push(CondState.LOOKELSE)
                                    else:
                                        push(CondState.LOOKEND)
                                        push(CondState.MATCHELSE)
                            else:
                                self.Error(263)
                                _ = eval_expr()
                            scan_2_end()
                            goto_1 = True
                            break
                        elif option_ch == '2':  # ELSEC
                            if self.CondStack[self.CondTos] not in (
                                CondState.LOOKELSE,
                                CondState.MATCHELSE,
                            ):
                                self.Error(264)
                            else:
                                pop()
                        elif option_ch == '3':  # ENDC
                            if self.CondStack[self.CondTos] not in (
                                CondState.LOOKELSE,
                                CondState.MATCHELSE,
                                CondState.LOOKEND,
                                CondState.MATCHEND,
                            ):
                                self.Error(265)
                            else:
                                if self.CondStack[self.CondTos] in (
                                    CondState.LOOKELSE,
                                    CondState.MATCHELSE,
                                ):
                                    pop()
                                pop()
                        elif option_ch == '4':  # SETC
                            while True:
                                self.ParsingOption = True
                                self.Scan()
                                if self.Token != Symbol.IDENTSY:
                                    self.Error(266)
                                temp_id = self.Ident
                                self.Scan()
                                if self.Token != Symbol.ASSIGNSY and self.Token != Symbol.EQSY:
                                    self.Error(266)
                                else:
                                    set_val(temp_id, eval_expr())
                                if self.Token != Symbol.COMMASY:
                                    break
                            scan_2_end()
                            goto_1 = True
                            break
                        elif option_ch == '5':  # OV
                            if self.Ch in ('+', '-'):
                                self.OflowFlag = self.Ch == '+'
                            else:
                                end_of_options = True
                        elif option_ch == '6':  # OPT
                            if self.Ch in ('+', '-'):
                                self.OptFlag = self.Ch == '+'
                                self.OptLimFlag = True
                                self.NextCh()
                                if self.Ch in ('+', '-'):
                                    self.OptLimFlag = self.Ch == '-'
                                else:
                                    end_of_options = True
                            else:
                                end_of_options = True
                        elif option_ch == '7':  # ASM
                            if self.Ch in ('+', '-'):
                                self.ShowAsmCode = self.Ch == '+'
                                self.NewAsmStatus = True
                            else:
                                end_of_options = True

                        if not end_of_options:
                            self.NextCh()
                            end_of_options = self.Ch != ','
                    else:
                        end_of_options = True

            if not goto_1:
                if term_ch == '*':
                    while True:
                        while self.Ch != '*' and self.Ch != '\x03':
                            self.NextCh()
                        if self.Ch != '\x03':
                            self.NextCh()
                        if self.Ch == ')' or self.Ch == '\x03':
                            break
                else:
                    while self.Ch != '}' and self.Ch != '\x03':
                        self.NextCh()

                if self.Ch == '\x03':
                    self.LineNumber -= 1
                    self.PrevLn = 0
                    self.Error(18)
                    raise AbortCompilation()

                if incl_opt_flag:
                    # Attempt to flush out current line
                    if self.InbufP < len(self.Inbuf) and self.Inbuf[self.InbufP] == 13:
                        self.NextCh()
                        if self.Listing:
                            self.TotalLines = self.ListLine(self.TotalLines)
                        else:
                            self.TotalLines += 1
                        self.LinePrinted = True
                        self.LineNumber += 1
                        self.EolSource = False

                    if self.OpenNewFile(filename, InputFileTypes.INCLUDED):
                        self.FillInbuf()  # Get a buffer full of include file
                        self.NextCh()
                        prev_entry = self.OpenFileStack[self.TopOfOpenFileStack - 1]
                        self.PrevLn = prev_entry.PrevLnbr
                        self.PrevLine = prev_entry.PrevL
                    else:
                        if self.rt.io_result > 0:
                            self.LineNumber -= 1
                            self.Error(405)
                            raise AbortCompilation()
                        self.NextCh()
                else:
                    self.NextCh()

            # LABEL 1:
            if not already_skipping:
                if self.CondStack[self.CondTos] >= CondState.MATCHELSE:
                    while self.CondStack[self.CondTos] >= CondState.MATCHELSE:
                        self.Scan()
                    return True  # Exit(Scan)
            return False

        # Body of Scan (LABEL 1 loop)
        while True:
            while self.ChClass[ord(self.Ch)] == Symbol.BLANKCL:
                self.NextCh()
            cc = self.ChClass[ord(self.Ch)]

            if cc == Symbol.DIGITCL:
                unsigned_number()
                return

            if cc == Symbol.DOLLARSY:
                hex_constant()
                return

            if cc == Symbol.LETCL:
                k = 0
                ident_chars = [' '] * ALFALEN
                while True:
                    if k < ALFALEN:
                        if self.Ch >= 'a':
                            self.Ch = chr(ord(self.Ch) - 32)
                        ident_chars[k] = self.Ch
                        k += 1
                    self.NextCh()
                    if self.ChClass[ord(self.Ch)] < Symbol.LETCL:
                        break
                self.Ident = ''.join(ident_chars)
                self.Token = Symbol.IDENTSY
                for i in range(self.LRWnames[k - 1] + 1, self.LRWnames[k] + 1):
                    if self.RWnames[i] == self.Ident:
                        self.Token = self.RWsymbol[i]
                return

            if cc in (
                Symbol.RPARENSY,
                Symbol.COMMASY,
                Symbol.SEMISY,
                Symbol.UPARROWSY,
                Symbol.LBRACKSY,
                Symbol.RBRACKSY,
                Symbol.PLUSSY,
                Symbol.MINUSSY,
                Symbol.SLASHSY,
                Symbol.EQSY,
                Symbol.ATSIGNSY,
            ):
                self.Token = cc
                self.NextCh()
                return

            if cc == Symbol.STARSY:
                self.NextCh()
                if self.ParsingOption and self.Ch == ')':
                    self.NextCh()
                    self.Token = Symbol.RBRACKSY
                    self.RBrackChar = '*'
                else:
                    self.Token = Symbol.STARSY
                return

            if cc == Symbol.LPARENSY:
                self.NextCh()
                if self.Ch == '*':
                    if comment('*'):
                        return
                    continue  # GOTO 1
                elif self.Ch == '.':
                    self.NextCh()
                    self.Token = Symbol.LBRACKSY
                    return
                else:
                    self.Token = Symbol.LPARENSY
                    return

            if cc == Symbol.LBRACECL:
                if comment('}'):
                    return
                continue  # GOTO 1

            if cc == Symbol.LTSY:
                self.NextCh()
                if self.Ch == '=':
                    self.NextCh()
                    self.Token = Symbol.LESY
                elif self.Ch == '>':
                    self.NextCh()
                    self.Token = Symbol.NESY
                else:
                    self.Token = Symbol.LTSY
                return

            if cc == Symbol.GTSY:
                self.NextCh()
                if self.Ch == '=':
                    self.NextCh()
                    self.Token = Symbol.GESY
                else:
                    self.Token = Symbol.GTSY
                return

            if cc == Symbol.PERIODSY:
                self.NextCh()
                if self.Ch == '.':
                    self.NextCh()
                    self.Token = Symbol.COLONSY
                    self.DotDot = True
                elif self.Ch == ')':
                    self.NextCh()
                    self.Token = Symbol.RBRACKSY
                else:
                    self.Token = Symbol.PERIODSY
                return

            if cc == Symbol.COLONSY:
                self.NextCh()
                if self.Ch == '=':
                    self.NextCh()
                    self.Token = Symbol.ASSIGNSY
                else:
                    self.Token = Symbol.COLONSY
                    self.DotDot = self.DotFlag
                    self.DotFlag = False
                return

            if cc == Symbol.SCONSTSY:
                get_string()
                return

            if cc == Symbol.EOFSY:
                self.EolSource = True
                self.LinePrinted = True
                self.PrevLn = 0
                if self.Token == Symbol.EOFSY:
                    # Two times is an error
                    if self.CondStack[self.CondTos] == CondState.NULL:
                        self.Error(16)
                    else:
                        self.Error(267)
                    self.NextCh()  # force out error message
                    raise AbortCompilation()
                else:
                    self.Token = Symbol.EOFSY
                    self.LineNumber -= 1
                return

            # ERRSY
            if self.ParsingOption and self.Ch == '}':
                self.NextCh()
                self.Token = Symbol.RBRACKSY
                self.RBrackChar = '}'
                return
            else:
                self.pCurLine += 1  # fake out error position
                self.Error(15)  # Illegal character input
                self.pCurLine -= 1
                self.NextCh()
                continue  # GOTO 1

    def ShowProcName(self, Class: str, Name: str, Level: int) -> str:
        """Format a routine progress line showing available words, lexical indentation, class, and name (`{...}` if errors exist)."""
        name_str = alfa8(Name)
        cls_str = Class[:9]
        mem_str = self.rt.PutIntP(MemAvailWords, 6)
        indent = pcopy(self.Blanks, 1, (Level - 1) * 3 + 1)
        if self.Errors == 0:
            self.ShowPStr = f'[{mem_str} words]{indent}{cls_str}{name_str}'[:SUMaxStrLeng]
        else:
            self.ShowPStr = f'{{{mem_str} words}}{indent}{cls_str}{name_str}'[:SUMaxStrLeng]
        return self.ShowPStr

    def LeftCheck(self) -> None:
        """Increment statement nesting level `NestLev` and record its low digit in `Left` if unset on this line."""
        self.NestLev += 1
        if self.Left == '-':
            self.Left = chr(ord('0') + pmod(self.NestLev, 10))

    def RightCheck(self) -> None:
        """Record the current statement nesting level's low digit in `Right` and decrement `NestLev`."""
        self.Right = chr(ord('0') + pmod(self.NestLev, 10))
        self.NestLev -= 1

    def KillExec(self) -> None:
        """Stop any active Lisa OS exec file via `SUStopExec` upon compiler error or abort."""
        err = self.rt.SUStopExec()
        if err > 0:
            sys.stdout.write(f'Error number {err} killing OS exec.\n')
            strg = self.rt.SUErrText('OSErrs.Err', err)
            sys.stdout.write(f'{strg}\n')
            self.rt.SUWaitSp()

    def RecordError(self, Nbr: int, Pos: int, Name: str) -> None:
        """Stop any OS exec script, increment `Errors`, and record `(Nbr, Pos, Name)` in `ErrList` (or error 352 on overflow)."""
        self.KillExec()
        self.Errors += 1
        name_alfa = alfa8(Name)
        if self.ErrIndex >= MaxErrs:
            self.ErrList[MaxErrs].Nbr = 352  # too many errors on line
            self.ErrList[MaxErrs].Name = '        '
        else:
            self.ErrIndex += 1
            self.ErrList[self.ErrIndex].Nbr = Nbr
            self.ErrList[self.ErrIndex].Name = name_alfa
        self.ErrList[self.ErrIndex].Pos = Pos

    def Error(self, ErrNum: int) -> None:
        """Record error `ErrNum` at the current source column if not already queued at that position."""
        p = self.pCurLine - (0 if self.EolSource else 1)
        if p <= 0:
            p = 1

        dup_err = False
        i = 1
        while not dup_err and i <= self.ErrIndex:
            err = self.ErrList[i]
            if p == err.Pos and ErrNum == err.Nbr:
                dup_err = True
            else:
                i += 1

        if not dup_err:
            self.RecordError(ErrNum, p, '        ')

    def NError(self, ErrNum: int, ErrName: str) -> None:
        """Record identifier-qualified error `ErrNum` with `ErrName` at the current source column."""
        p = self.pCurLine - (0 if self.EolSource else 1)
        if p <= 0:
            p = 1
        self.RecordError(ErrNum, p, alfa8(ErrName))

    def FatalOutputError(self) -> None:
        """Handle an I-code output error, recording error 407 on disk-full (`848`) or aborting with error 408 after flushing the line."""
        io_rslt = self.rt.io_result
        if io_rslt <= 0:
            self.Error(407)
        elif io_rslt == 848:
            self.Error(407)
        else:
            self.rt.IOError(io_rslt, '*** FATAL OUTPUT ERROR WRITING I-CODE FILE ***')
            self.Error(408)
            while not self.EolSource:
                self.NextCh()
            self.CurLine = self.CurLine[:max(0, self.pCurLine)]
            if not self.LinePrinted:
                if self.Listing:
                    self.TotalLines = self.ListLine(self.TotalLines)
                else:
                    self.TotalLines += 1
            raise AbortCompilation()

    def FullBytes(self, FpT: Optional[T]) -> int:
        """Return the unpacked storage/stack byte size of `FpT`, rounding bit-packed sizes up and promoting unsigned 1-byte scalars to 2 bytes."""
        if FpT is not None:
            if FpT.Bits != 0:
                return FpT.Bytes + 1
            elif FpT.Bytes == 1 and FpT.Form <= TypeForms.SUBRANGE:
                l_min, _ = self.GetBounds(FpT)
                if l_min >= 0:
                    return 2
                else:
                    return 1
            else:
                return FpT.Bytes
        else:
            return 2

    def CompTypes(self, FpT1: Optional[T], FpT2: Optional[T]) -> bool:
        """Return True if `FpT1` and `FpT2` are compatible (unwrapping subranges, matching strings/`NIL`, and checking `FpT2` subclass-of `FpT1`)."""
        if FpT1 is not None and FpT2 is not None:
            if FpT1 is not FpT2:
                if FpT1.Form != FpT2.Form:
                    if FpT1.Form == TypeForms.SUBRANGE:
                        return self.CompTypes(FpT1.RangeOf, FpT2)
                    elif FpT2.Form == TypeForms.SUBRANGE:
                        return self.CompTypes(FpT2.RangeOf, FpT1)
                    elif (
                        FpT1.Form == TypeForms.STRINGS and FpT2.Form == TypeForms.SCONST
                    ) or (
                        FpT1.Form == TypeForms.SCONST and FpT2.Form == TypeForms.STRINGS
                    ):
                        return True
                    elif (FpT1.Form == TypeForms.CLASSES and FpT2 is self.NilPtr) or (
                        FpT2.Form == TypeForms.CLASSES and FpT1 is self.NilPtr
                    ):
                        return True
                    else:
                        return False
                else:
                    form = FpT1.Form
                    if form in (
                        TypeForms.SCALAR,
                        TypeForms.ARRAYS,
                        TypeForms.RECORDS,
                        TypeForms.TAGFIELD,
                        TypeForms.VARIANT,
                        TypeForms.FILES,
                    ):
                        return False
                    elif form == TypeForms.SUBRANGE:
                        return self.CompTypes(FpT1.RangeOf, FpT2.RangeOf)
                    elif form == TypeForms.POINTERS:
                        return (FpT1 is self.NilPtr) or (FpT2 is self.NilPtr)
                    elif form == TypeForms.SETS:
                        return self.CompTypes(FpT1.SetOf, FpT2.SetOf)
                    elif form in (TypeForms.SCONST, TypeForms.STRINGS):
                        return True
                    elif form == TypeForms.CLASSES:
                        t_pt: Optional[T] = FpT2
                        while t_pt is not None:
                            if t_pt is FpT1:
                                return True
                            t_pt = t_pt.SuperClass
                        return False
        return True

    def EqTypes(self, FpT1: Optional[T], FpT2: Optional[T]) -> bool:
        """Return True if `FpT1` and `FpT2` are identical types, or if `FpT1` is a subclass of `FpT2` for class types."""
        if (FpT1 is not None and FpT1.Form == TypeForms.CLASSES) or (
            FpT2 is not None and FpT2.Form == TypeForms.CLASSES
        ):
            return self.CompTypes(FpT2, FpT1)
        return FpT1 is FpT2

    def CompFormals(
        self, FormArg1: Optional[N], FormArg2: Optional[N], Exact: bool
    ) -> bool:
        """Return True if formal parameter lists `FormArg1` and `FormArg2` match in names, kinds, nested signatures, and types.
        When `Exact` is False, class parameters and function results in `FormArg2` may be subclasses of those in `FormArg1`."""

        def equal_types(arg1: N, arg2: N) -> bool:
            """Return True if `arg1` and `arg2` have identical types, or compatible class types when `Exact` is False."""
            if Exact:
                return arg1.IdType is arg2.IdType
            if arg1.IdType is not None and arg2.IdType is not None:
                if arg1.IdType.Form == arg2.IdType.Form:
                    if arg1.IdType.Form == TypeForms.CLASSES:
                        return self.CompTypes(arg1.IdType, arg2.IdType)
                    else:
                        return arg1.IdType is arg2.IdType
            return False

        ok = True
        while FormArg1 is not None and FormArg2 is not None and ok:
            ok = False
            if FormArg1.Name == FormArg2.Name:
                if FormArg1.Class == FormArg2.Class:
                    if FormArg1.Class == NameClass.VARS:
                        if FormArg1.Vkind == FormArg2.Vkind:
                            ok = equal_types(FormArg1, FormArg2)
                    elif FormArg1.PFdeclKind == FormArg2.PFdeclKind:
                        if self.CompFormals(
                            FormArg1.PFargList, FormArg2.PFargList, Exact
                        ):
                            if FormArg1.Class == NameClass.PROC:
                                ok = True
                            else:
                                ok = equal_types(FormArg1, FormArg2)

            FormArg1 = FormArg1.Next
            FormArg2 = FormArg2.Next

        if ok:
            ok = (FormArg1 is None) and (FormArg2 is None)
        return ok

    def GetBounds(self, FpT: Optional[T]) -> tuple[int, int]:
        """Return the 16-bit `(min, max)` bounds of scalar, subrange, or string type `FpT` (not valid for 32-bit `LONGINT`)."""
        f_min = 0
        f_max = 0
        if FpT is not None:
            if FpT.Form == TypeForms.SCALAR:
                if FpT.ScalKind == DeclKind.DECLARED:
                    if FpT.MaxConst is not None:
                        f_max = i16(FpT.MaxConst.ValueOf.Ivalu)
                elif FpT is self.CharPtr:
                    f_max = 255
                elif FpT is self.IntPtr:
                    f_min = -32767 - 1
                    f_max = 32767
            elif FpT.Form == TypeForms.SUBRANGE:
                f_min = i16(FpT.Min)
                f_max = i16(FpT.Max)
            elif FpT.Form in (TypeForms.STRINGS, TypeForms.SCONST):
                f_min = 0  # 0 to allow access to string length
                f_max = i16(FpT.StringLen)
        return f_min, f_max

    def StringType(self, FpT: Optional[T]) -> bool:
        """Return True if `FpT` is a Pascal `STRING`, string literal (`SCONST`), or `PACKED ARRAY OF CHAR`."""
        if FpT is not None:
            if FpT.Form == TypeForms.STRINGS or FpT.Form == TypeForms.SCONST:
                return True
            elif FpT.Form == TypeForms.ARRAYS:
                return (FpT.ArrayOf is self.CharPtr) and FpT.PckdArr
        return False

    def ChToString(self, FAttr: Attr) -> None:
        """Convert character constant attribute `FAttr` in place into a 1-character `Str1Ptr` string constant."""
        assert FAttr.TreePtr is not None
        ch = chr(u8(FAttr.TreePtr.CstValu.Ivalu))
        l_str_val = StrValRec(pset_ch('        ', 1, ch), None)
        FAttr.TreePtr.CstType = self.Str1Ptr
        FAttr.TreePtr.CstValu.Svalu = l_str_val
        FAttr.TreePtr.CstValu.SvaluLen = 1
        FAttr.Typtr = self.Str1Ptr
        FAttr.ASize = 2

    def UpdateSetConst(
        self, fLb: int, fUb: int, fSetCstPart: Optional[N]
    ) -> Optional[N]:
        """Insert ordinal elements `fLb..fUb` (`0..4087`) into chained 32-bit `SetValRec` nodes on `fSetCstPart`, creating it if `None`."""
        if fLb < 0 or fUb < 0 or fLb > 4087 or fUb > 4087:
            self.Error(308)
        else:
            lb = int(fLb)
            ub = int(fUb)
            if lb <= ub:
                if fSetCstPart is None:
                    fSetCstPart = N(NodeKind.CSTNODE)
                    fSetCstPart.CstType = None
                    fSetCstPart.CstValu.MaxSetEl = 0
                    fSetCstPart.CstValu.SetValu = SetValRec(None, set())
                cst_val = fSetCstPart.CstValu
                if cst_val.MaxSetEl < ub:
                    cst_val.MaxSetEl = ub
                l_set_val = cst_val.SetValu
                assert l_set_val is not None
                for _ in range(1, pdiv(ub, 32) + 1):
                    if l_set_val.NextSet is None:
                        l_set_val.NextSet = SetValRec(None, set())
                    l_set_val = l_set_val.NextSet
                for i in range(lb, ub + 1):
                    l_set_val = cst_val.SetValu
                    assert l_set_val is not None
                    for _ in range(1, pdiv(i, 32) + 1):
                        assert l_set_val.NextSet is not None
                        l_set_val = l_set_val.NextSet
                    l_set_val.SetVal.add(pmod(i, 32))
        return fSetCstPart

    # ========================================================================
    # 2. Constant evaluator, symbol table, I-code buffered output, and unit/program driver
    # ========================================================================

    def Constant(self, FSys: set[Symbol] | frozenset[Symbol]) -> tuple[Valu, Optional[T]]:
        """Parse and evaluate a compile-time constant expression, synchronizing on `FSys`.

        Returns `(Valu, T)` for the folded constant, defaulting to integer `0` on error.
        """
        NonStd: bool = False
        fValu = Valu()
        FpT: Optional[T] = None

        def ConstExpression(Fsys: set[Symbol] | frozenset[Symbol]) -> None:
            """Evaluate a constant expression including optional relational and `IN` operators."""
            nonlocal NonStd

            def Err(Nbr: int) -> None:
                """Report compiler error `Nbr` and clear `gAttr` type and tree pointers."""
                self.Error(Nbr)
                self.gAttr.Typtr = None
                self.gAttr.TreePtr = None

            def Float(fAttr: Attr) -> None:
                """Promote integer constant attribute `fAttr` in place to a 32-bit real constant."""
                assert fAttr.TreePtr is not None
                fAttr.Typtr = self.RealPtr
                fAttr.TreePtr.CstType = self.RealPtr
                fAttr.TreePtr.CstValu.Rvalu = f32(fAttr.TreePtr.CstValu.Ivalu)

            def SimpleConstExpression(Fsys: set[Symbol] | frozenset[Symbol]) -> None:
                """Evaluate a signed or unsigned simple constant expression (`+`, `-`, `OR`, set union/difference)."""
                nonlocal NonStd
                lToken: Symbol = Symbol.ERRSY
                lAttr: Attr = Attr()

                def CompactSet(Result: N) -> None:
                    """Trim trailing empty chunks from constant set `Result` and compute `MaxSetEl` and byte size."""
                    assert self.gAttr.Typtr is not None
                    lpT = T(TypeForms.SETS)
                    lpT.FType = False
                    lpT.Form = TypeForms.SETS
                    lpT.SetOf = self.gAttr.Typtr.SetOf
                    lpT.Bits = 0

                    self.gAttr.Typtr = lpT
                    self.gAttr.TreePtr = Result
                    Result.Node = NodeKind.CSTNODE
                    Result.CstType = lpT

                    cv = Result.CstValu
                    LastSetVal: Optional[SetValRec] = None
                    MaxEl: int = 0

                    if cv.SetValu is not None:
                        lSetVal: Optional[SetValRec] = cv.SetValu
                        CurrMaxEl = -1
                        while lSetVal is not None:
                            CurrMaxEl += 32
                            if len(lSetVal.SetVal) > 0:
                                LastSetVal = lSetVal
                                MaxEl = CurrMaxEl
                            lSetVal = lSetVal.NextSet

                    if LastSetVal is None:
                        lpT.Bytes = 0
                        cv.SetValu = None
                        cv.MaxSetEl = -1
                    else:
                        LastSetVal.NextSet = None
                        CurrMaxEl = 31
                        while CurrMaxEl not in LastSetVal.SetVal:
                            CurrMaxEl -= 1
                        cv.MaxSetEl = MaxEl - (31 - CurrMaxEl)
                        lpT.Bytes = pdiv(cv.MaxSetEl, 8) + 1
                        if lpT.Bytes > 1 and odd(lpT.Bytes):
                            lpT.Bytes += 1

                def LinkSetVal(
                    Result: N, PrevSetVal: Optional[SetValRec]
                ) -> tuple[SetValRec, SetValRec]:
                    """Allocate and append a new 32-bit `SetValRec` chunk to `Result`'s constant set chain."""
                    CurrSetVal = SetValRec()
                    if PrevSetVal is None:
                        Result.CstValu.SetValu = CurrSetVal
                    else:
                        PrevSetVal.NextSet = CurrSetVal
                    PrevSetVal = CurrSetVal
                    CurrSetVal.NextSet = None
                    return PrevSetVal, CurrSetVal

                def SetUnion() -> None:
                    """Compute the compile-time union (`+`) of the constant sets in `lAttr` and `gAttr`."""
                    assert lAttr.TreePtr is not None and self.gAttr.TreePtr is not None
                    Result = N(NodeKind.CSTNODE)
                    Result.CstValu.SetValu = None
                    Left = lAttr.TreePtr.CstValu.SetValu
                    Right = self.gAttr.TreePtr.CstValu.SetValu
                    PrevSetVal: Optional[SetValRec] = None

                    while Left is not None or Right is not None:
                        PrevSetVal, CurrSetVal = LinkSetVal(Result, PrevSetVal)
                        if Left is not None and Right is not None:
                            CurrSetVal.SetVal = set(Left.SetVal) | set(Right.SetVal)
                            Left = Left.NextSet
                            Right = Right.NextSet
                        elif Left is None:
                            assert Right is not None
                            CurrSetVal.SetVal = set(Right.SetVal)
                            Right = Right.NextSet
                        else:
                            CurrSetVal.SetVal = set(Left.SetVal)
                            Left = Left.NextSet

                    CompactSet(Result)

                def SetDifference() -> None:
                    """Compute the compile-time difference (`-`) of the constant sets in `lAttr` and `gAttr`."""
                    assert lAttr.TreePtr is not None and self.gAttr.TreePtr is not None
                    Result = N(NodeKind.CSTNODE)
                    Result.CstValu.SetValu = None
                    Left = lAttr.TreePtr.CstValu.SetValu
                    Right = self.gAttr.TreePtr.CstValu.SetValu
                    PrevSetVal: Optional[SetValRec] = None

                    while Left is not None:
                        PrevSetVal, CurrSetVal = LinkSetVal(Result, PrevSetVal)
                        if Right is not None:
                            CurrSetVal.SetVal = set(Left.SetVal) - set(Right.SetVal)
                            Right = Right.NextSet
                        else:
                            CurrSetVal.SetVal = set(Left.SetVal)
                        Left = Left.NextSet

                    CompactSet(Result)

                def ConstTerm(Fsys: set[Symbol] | frozenset[Symbol]) -> None:
                    """Evaluate a constant term across `*`, `/`, `DIV`, `MOD`, `AND`, and set intersection."""
                    nonlocal NonStd
                    lToken: Symbol = Symbol.ERRSY
                    lAttr: Attr = Attr()

                    def SetIntersection() -> None:
                        """Compute the compile-time intersection (`*`) of the constant sets in `lAttr` and `gAttr`."""
                        assert lAttr.TreePtr is not None and self.gAttr.TreePtr is not None
                        Result = N(NodeKind.CSTNODE)
                        Result.CstValu.SetValu = None
                        PrevSetVal: Optional[SetValRec] = None
                        Left = lAttr.TreePtr.CstValu.SetValu
                        Right = self.gAttr.TreePtr.CstValu.SetValu

                        while Left is not None and Right is not None:
                            PrevSetVal, CurrSetVal = LinkSetVal(Result, PrevSetVal)
                            CurrSetVal.SetVal = set(Left.SetVal) & set(Right.SetVal)
                            Left = Left.NextSet
                            Right = Right.NextSet

                        CompactSet(Result)

                    def ConstFactor(Fsys: set[Symbol] | frozenset[Symbol]) -> None:
                        """Parse and evaluate a constant factor (literal, constant name, intrinsic call, `NOT`, or set)."""
                        nonlocal NonStd

                        def ConstCall(Fsys: set[Symbol] | frozenset[Symbol], FpN: N) -> None:
                            """Evaluate a compile-time call to a permitted standard function (`ABS`, `CHR`, `ODD`, `ORD`, `ORD4`, `ROUND`, `SQR`, `TRUNC`, `SIZEOF`)."""
                            nonlocal NonStd
                            NonStd = True
                            if self.Token == Symbol.LPARENSY:
                                self.Scan()
                            else:
                                self.Error(31)

                            if FpN.PFdeclKind != DeclKind.STANDARD:
                                Err(183)
                            elif FpN.Key not in _CONST_STD_KEYS:
                                Err(183)
                            elif FpN.Key == 26:
                                # SizeOf
                                self.gAttr.Typtr = self.IntPtr
                                if self.Token == Symbol.IDENTSY:
                                    lpN = self.SearchAll({NameClass.VARS, NameClass.TYPES})
                                    lpT = lpN.IdType if lpN is not None else None
                                    self.Scan()
                                    cst = N(NodeKind.CSTNODE)
                                    cst.Node = NodeKind.CSTNODE
                                    cst.CstType = self.IntPtr
                                    if lpT is None:
                                        cst.CstValu.Ivalu = 0
                                    elif lpT.Form == TypeForms.CLASSES:
                                        cst.CstValu.Ivalu = i32(lpT.SizeInstance)
                                    else:
                                        cst.CstValu.Ivalu = i32(self.FullBytes(lpT))
                                    self.gAttr.TreePtr = cst
                                    self.gAttr.Typtr = self.IntPtr
                                else:
                                    Err(29)
                            else:
                                ConstExpression(Fsys | frozenset({Symbol.RPARENSY}))
                                if self.gAttr.Typtr is not None:
                                    assert self.gAttr.TreePtr is not None
                                    key = FpN.Key
                                    if self.CompTypes(self.gAttr.Typtr, self.IntPtr):
                                        if key == 1:
                                            # ABS
                                            self.gAttr.TreePtr.CstValu.Ivalu = i32(
                                                abs(self.gAttr.TreePtr.CstValu.Ivalu)
                                            )
                                        elif key == 3:
                                            # CHR
                                            self.gAttr.Typtr = self.CharPtr
                                            self.gAttr.TreePtr.CstType = self.CharPtr
                                        elif key == 9:
                                            # ODD
                                            self.gAttr.TreePtr.CstValu.Ivalu = (
                                                1 if odd(self.gAttr.TreePtr.CstValu.Ivalu) else 0
                                            )
                                            self.gAttr.Typtr = self.BoolPtr
                                            self.gAttr.TreePtr.CstType = self.BoolPtr
                                        elif key in (10, 32):
                                            # ORD, ORD4
                                            pass
                                        elif key == 14:
                                            # SQR
                                            v = self.gAttr.TreePtr.CstValu.Ivalu
                                            self.gAttr.TreePtr.CstValu.Ivalu = i32(v * v)
                                        elif key in (12, 17):
                                            # TRUNC, ROUND
                                            Err(122)
                                    elif self.CompTypes(self.gAttr.Typtr, self.RealPtr):
                                        if key == 1:
                                            # ABS
                                            self.gAttr.TreePtr.CstValu.Rvalu = f32(
                                                abs(self.gAttr.TreePtr.CstValu.Rvalu)
                                            )
                                        elif key == 12:
                                            # ROUND
                                            self.gAttr.TreePtr.CstValu.Ivalu = i32(
                                                pround(self.gAttr.TreePtr.CstValu.Rvalu)
                                            )
                                            self.gAttr.Typtr = self.IntPtr
                                            self.gAttr.TreePtr.CstType = self.IntPtr
                                        elif key == 14:
                                            # SQR
                                            rv = self.gAttr.TreePtr.CstValu.Rvalu
                                            self.gAttr.TreePtr.CstValu.Rvalu = f32(rv * rv)
                                        elif key == 17:
                                            # TRUNC
                                            self.gAttr.TreePtr.CstValu.Ivalu = i32(
                                                ptrunc(self.gAttr.TreePtr.CstValu.Rvalu)
                                            )
                                            self.gAttr.Typtr = self.IntPtr
                                            self.gAttr.TreePtr.CstType = self.IntPtr
                                        elif key in (3, 9, 10, 32):
                                            # CHR, ODD, ORD, ORD4
                                            Err(122)
                                    elif key == 10 or (
                                        key == 32 and self.gAttr.Typtr.Form <= TypeForms.POINTERS
                                    ):
                                        # ORD, ORD4
                                        self.gAttr.Typtr = self.IntPtr
                                        self.gAttr.TreePtr.CstType = self.IntPtr
                                    else:
                                        Err(122)

                            if self.Token == Symbol.RPARENSY:
                                self.Scan()
                            else:
                                self.Error(32)

                        def BuildSet() -> None:
                            """Parse a `[...]` constant set constructor of elements and `:` subranges into `gAttr`."""
                            nonlocal NonStd
                            NonStd = True
                            self.Scan()
                            SetType: Optional[T] = None
                            SetCstPart: Optional[N] = None

                            if self.Token != Symbol.RBRACKSY:
                                ExitFlag = False
                                while not ExitFlag:
                                    ConstExpression(
                                        Fsys | frozenset({Symbol.COMMASY, Symbol.COLONSY, Symbol.RBRACKSY})
                                    )
                                    if SetType is None:
                                        SetType = self.gAttr.Typtr
                                    elif not self.CompTypes(SetType, self.gAttr.Typtr):
                                        self.Error(134)

                                    if self.Token == Symbol.COLONSY:
                                        # Double set element
                                        self.Scan()
                                        lpN = self.gAttr.TreePtr
                                        ConstExpression(
                                            Fsys | frozenset({Symbol.COMMASY, Symbol.RBRACKSY})
                                        )
                                        if SetType is None:
                                            SetType = self.gAttr.Typtr
                                        elif not self.CompTypes(SetType, self.gAttr.Typtr):
                                            self.Error(134)
                                        if lpN is not None and self.gAttr.TreePtr is not None:
                                            SetCstPart = self.UpdateSetConst(
                                                lpN.CstValu.Ivalu,
                                                self.gAttr.TreePtr.CstValu.Ivalu,
                                                SetCstPart,
                                            )
                                    elif self.gAttr.TreePtr is not None:
                                        SetCstPart = self.UpdateSetConst(
                                            self.gAttr.TreePtr.CstValu.Ivalu,
                                            self.gAttr.TreePtr.CstValu.Ivalu,
                                            SetCstPart,
                                        )

                                    if self.Token == Symbol.COMMASY:
                                        self.Scan()
                                    else:
                                        ExitFlag = True

                                if SetType is not None:
                                    if SetType.Form > TypeForms.SUBRANGE:
                                        self.Error(133)
                                    elif self.CompTypes(SetType, self.RealPtr):
                                        self.Error(164)

                            lpT = T(TypeForms.SETS)
                            lpT.FType = False
                            lpT.Form = TypeForms.SETS
                            lpT.SetOf = SetType
                            lpT.Bits = 0
                            self.gAttr.Typtr = lpT

                            if SetCstPart is None:
                                SetCstPart = N(NodeKind.CSTNODE)
                                SetCstPart.CstValu.SetValu = None
                                SetCstPart.CstValu.MaxSetEl = -1
                                lpT.Bytes = 0
                            else:
                                lpT.Bytes = pdiv(SetCstPart.CstValu.MaxSetEl, 8) + 1
                                if lpT.Bytes > 1 and odd(lpT.Bytes):
                                    lpT.Bytes += 1

                            SetCstPart.CstType = lpT
                            self.gAttr.TreePtr = SetCstPart

                            if self.Token == Symbol.RBRACKSY:
                                self.Scan()
                            else:
                                self.Error(34)

                        self.gAttr.TreePtr = None
                        self.gAttr.Typtr = None
                        if self.Token not in FacBegSys:
                            self.Skip(27, Fsys | FacBegSys)

                        while True:
                            if self.Token in FacBegSys:
                                tok = self.Token
                                if tok == Symbol.IDENTSY:
                                    lpN = self.SearchAll({NameClass.CONSTS, NameClass.FUNC})
                                    self.Scan()
                                    assert lpN is not None
                                    if lpN.Class == NameClass.CONSTS:
                                        self.gAttr.Typtr = lpN.IdType
                                        tp = N(NodeKind.CSTNODE)
                                        tp.Node = NodeKind.CSTNODE
                                        tp.CstValu = lpN.ValueOf.copy()
                                        tp.CstType = lpN.IdType
                                        self.gAttr.TreePtr = tp
                                    else:
                                        ConstCall(Fsys, lpN)

                                elif tok == Symbol.ICONSTSY:
                                    self.gAttr.Typtr = self.IntPtr
                                    tp = N(NodeKind.CSTNODE)
                                    tp.Node = NodeKind.CSTNODE
                                    tp.CstType = self.gAttr.Typtr
                                    tp.CstValu.Ivalu = i32(self.IntVal)
                                    self.gAttr.TreePtr = tp
                                    self.Scan()

                                elif tok == Symbol.RCONSTSY:
                                    self.gAttr.Typtr = self.RealPtr
                                    tp = N(NodeKind.CSTNODE)
                                    tp.Node = NodeKind.CSTNODE
                                    tp.CstType = self.RealPtr
                                    tp.CstValu.Rvalu = f32(self.RealVal)
                                    self.gAttr.TreePtr = tp
                                    self.Scan()

                                elif tok == Symbol.CCONSTSY:
                                    self.gAttr.Typtr = self.CharPtr
                                    tp = N(NodeKind.CSTNODE)
                                    tp.Node = NodeKind.CSTNODE
                                    tp.CstType = self.CharPtr
                                    tp.CstValu.Ivalu = i32(self.IntVal)
                                    self.gAttr.TreePtr = tp
                                    self.Scan()

                                elif tok == Symbol.SCONSTSY:
                                    if self.IntVal > 0:
                                        lpT = T(TypeForms.SCONST)
                                        lpT.FType = False
                                        lpT.Form = TypeForms.SCONST
                                        lpT.StringLen = self.IntVal
                                        lpT.Bits = 0
                                        lpT.Bytes = self.IntVal
                                        if lpT.Bytes != 1 and odd(lpT.Bytes):
                                            lpT.Bytes += 1
                                    else:
                                        lpT = self.Str0Ptr
                                    self.gAttr.Typtr = lpT
                                    tp = N(NodeKind.CSTNODE)
                                    tp.Node = NodeKind.CSTNODE
                                    tp.CstType = lpT
                                    tp.CstValu.Svalu = self.StrVal
                                    tp.CstValu.SvaluLen = self.IntVal
                                    self.gAttr.TreePtr = tp
                                    self.Scan()

                                elif tok == Symbol.LPARENSY:
                                    NonStd = True
                                    self.Scan()
                                    ConstExpression(Fsys | frozenset({Symbol.RPARENSY}))
                                    if self.Token == Symbol.RPARENSY:
                                        self.Scan()
                                    else:
                                        self.Error(32)

                                elif tok == Symbol.NOTSY:
                                    NonStd = True
                                    self.Scan()
                                    ConstFactor(Fsys)
                                    if not self.CompTypes(self.gAttr.Typtr, self.BoolPtr):
                                        Err(132)
                                    elif self.gAttr.Typtr is not None:
                                        assert self.gAttr.TreePtr is not None
                                        self.gAttr.TreePtr.CstValu.Ivalu = i32(
                                            1 - self.gAttr.TreePtr.CstValu.Ivalu
                                        )

                                elif tok == Symbol.NILSY:
                                    Err(181)

                                elif tok == Symbol.LBRACKSY:
                                    BuildSet()

                                elif tok == Symbol.ATSIGNSY:
                                    Err(182)
                                    self.Scan()
                                    if self.Token == Symbol.IDENTSY:
                                        self.Scan()

                                if self.Token not in Fsys:
                                    self.Skip(20, Fsys | FacBegSys)

                            if self.Token in Fsys:
                                break

                    ConstFactor(Fsys | _MULT_OPS)

                    while self.Token in _MULT_OPS:
                        NonStd = True
                        lAttr = self.gAttr.copy()
                        lToken = self.Token

                        self.Scan()
                        ConstFactor(Fsys | _MULT_OPS)

                        if lAttr.Typtr is not None and self.gAttr.Typtr is not None:
                            assert lAttr.TreePtr is not None and self.gAttr.TreePtr is not None
                            if lToken == Symbol.ANDSY:
                                if self.CompTypes(lAttr.Typtr, self.BoolPtr) and self.CompTypes(
                                    self.gAttr.Typtr, self.BoolPtr
                                ):
                                    self.gAttr.TreePtr.CstValu.Ivalu = i32(
                                        lAttr.TreePtr.CstValu.Ivalu
                                        * self.gAttr.TreePtr.CstValu.Ivalu
                                    )
                                else:
                                    Err(132)

                            elif lToken in (Symbol.DIVSY, Symbol.MODSY):
                                if self.CompTypes(lAttr.Typtr, self.IntPtr) and self.CompTypes(
                                    self.gAttr.Typtr, self.IntPtr
                                ):
                                    if self.gAttr.TreePtr.CstValu.Ivalu != 0:
                                        if lToken == Symbol.DIVSY:
                                            self.gAttr.TreePtr.CstValu.Ivalu = i32(
                                                pdiv(
                                                    lAttr.TreePtr.CstValu.Ivalu,
                                                    self.gAttr.TreePtr.CstValu.Ivalu,
                                                )
                                            )
                                        else:
                                            self.gAttr.TreePtr.CstValu.Ivalu = i32(
                                                pmod(
                                                    lAttr.TreePtr.CstValu.Ivalu,
                                                    self.gAttr.TreePtr.CstValu.Ivalu,
                                                )
                                            )
                                    else:
                                        Err(180)
                                else:
                                    Err(131)

                            elif lToken == Symbol.SLASHSY:
                                if self.CompTypes(lAttr.Typtr, self.IntPtr):
                                    Float(lAttr)
                                if self.CompTypes(self.gAttr.Typtr, self.IntPtr):
                                    Float(self.gAttr)
                                if self.CompTypes(
                                    self.gAttr.Typtr, self.RealPtr
                                ) and self.CompTypes(lAttr.Typtr, self.RealPtr):
                                    if self.gAttr.TreePtr.CstValu.Rvalu != 0.0:
                                        self.gAttr.TreePtr.CstValu.Rvalu = f32(
                                            lAttr.TreePtr.CstValu.Rvalu
                                            / self.gAttr.TreePtr.CstValu.Rvalu
                                        )
                                    else:
                                        Err(180)
                                else:
                                    Err(131)

                            elif lToken == Symbol.STARSY:
                                if self.CompTypes(lAttr.Typtr, self.IntPtr) and self.CompTypes(
                                    self.gAttr.Typtr, self.IntPtr
                                ):
                                    self.gAttr.TreePtr.CstValu.Ivalu = i32(
                                        lAttr.TreePtr.CstValu.Ivalu
                                        * self.gAttr.TreePtr.CstValu.Ivalu
                                    )
                                else:
                                    if self.CompTypes(lAttr.Typtr, self.IntPtr):
                                        Float(lAttr)
                                    if self.CompTypes(self.gAttr.Typtr, self.IntPtr):
                                        Float(self.gAttr)
                                    if self.CompTypes(
                                        lAttr.Typtr, self.RealPtr
                                    ) and self.CompTypes(self.gAttr.Typtr, self.RealPtr):
                                        self.gAttr.TreePtr.CstValu.Rvalu = f32(
                                            lAttr.TreePtr.CstValu.Rvalu
                                            * self.gAttr.TreePtr.CstValu.Rvalu
                                        )
                                    elif (
                                        self.CompTypes(self.gAttr.Typtr, lAttr.Typtr)
                                        and self.gAttr.Typtr is not None
                                        and self.gAttr.Typtr.Form == TypeForms.SETS
                                    ):
                                        SetIntersection()
                                    else:
                                        Err(131)

                Negative = self.Token == Symbol.MINUSSY
                Signed = (self.Token == Symbol.PLUSSY) or Negative
                if Signed:
                    self.Scan()

                ConstTerm(Fsys | _ADD_OPS)

                if self.gAttr.Typtr is not None:
                    if Signed:
                        assert self.gAttr.TreePtr is not None
                        if self.CompTypes(self.gAttr.Typtr, self.IntPtr):
                            if Negative:
                                self.gAttr.TreePtr.CstValu.Ivalu = i32(
                                    -self.gAttr.TreePtr.CstValu.Ivalu
                                )
                        elif self.CompTypes(self.gAttr.Typtr, self.RealPtr):
                            if Negative:
                                self.gAttr.TreePtr.CstValu.Rvalu = f32(
                                    -self.gAttr.TreePtr.CstValu.Rvalu
                                )
                        else:
                            Err(140)

                while self.Token in _ADD_OPS:
                    NonStd = True
                    lToken = self.Token
                    lAttr = self.gAttr.copy()

                    self.Scan()
                    ConstTerm(Fsys | _ADD_OPS)

                    if lAttr.Typtr is not None and self.gAttr.Typtr is not None:
                        assert lAttr.TreePtr is not None and self.gAttr.TreePtr is not None
                        if lToken in (Symbol.MINUSSY, Symbol.PLUSSY):
                            if self.CompTypes(lAttr.Typtr, self.IntPtr) and self.CompTypes(
                                self.gAttr.Typtr, self.IntPtr
                            ):
                                if lToken == Symbol.PLUSSY:
                                    self.gAttr.TreePtr.CstValu.Ivalu = i32(
                                        lAttr.TreePtr.CstValu.Ivalu
                                        + self.gAttr.TreePtr.CstValu.Ivalu
                                    )
                                else:
                                    self.gAttr.TreePtr.CstValu.Ivalu = i32(
                                        lAttr.TreePtr.CstValu.Ivalu
                                        - self.gAttr.TreePtr.CstValu.Ivalu
                                    )
                            else:
                                if self.CompTypes(lAttr.Typtr, self.IntPtr):
                                    Float(lAttr)
                                if self.CompTypes(self.gAttr.Typtr, self.IntPtr):
                                    Float(self.gAttr)
                                if self.CompTypes(
                                    lAttr.Typtr, self.RealPtr
                                ) and self.CompTypes(self.gAttr.Typtr, self.RealPtr):
                                    if lToken == Symbol.PLUSSY:
                                        self.gAttr.TreePtr.CstValu.Rvalu = f32(
                                            lAttr.TreePtr.CstValu.Rvalu
                                            + self.gAttr.TreePtr.CstValu.Rvalu
                                        )
                                    else:
                                        self.gAttr.TreePtr.CstValu.Rvalu = f32(
                                            lAttr.TreePtr.CstValu.Rvalu
                                            - self.gAttr.TreePtr.CstValu.Rvalu
                                        )
                                elif (
                                    self.CompTypes(lAttr.Typtr, self.gAttr.Typtr)
                                    and lAttr.Typtr is not None
                                    and lAttr.Typtr.Form == TypeForms.SETS
                                ):
                                    if lToken == Symbol.PLUSSY:
                                        SetUnion()
                                    else:
                                        SetDifference()
                                else:
                                    Err(131)

                        elif lToken == Symbol.ORSY:
                            if self.CompTypes(lAttr.Typtr, self.BoolPtr) and self.CompTypes(
                                self.gAttr.Typtr, self.BoolPtr
                            ):
                                if (
                                    lAttr.TreePtr.CstValu.Ivalu + self.gAttr.TreePtr.CstValu.Ivalu
                                ) == 0:
                                    self.gAttr.TreePtr.CstValu.Ivalu = 0
                                else:
                                    self.gAttr.TreePtr.CstValu.Ivalu = 1
                            else:
                                Err(132)

            def CompInts(Left: Attr, Op: Symbol, Right: Attr) -> bool:
                """Compare two integer or scalar constant attributes `Left` and `Right` with relational operator `Op`."""
                assert Left.TreePtr is not None and Right.TreePtr is not None
                Lvalu = Left.TreePtr.CstValu.Ivalu
                Rvalu = Right.TreePtr.CstValu.Ivalu
                if Op == Symbol.LTSY:
                    return Lvalu < Rvalu
                if Op == Symbol.GTSY:
                    return Lvalu > Rvalu
                if Op == Symbol.LESY:
                    return Lvalu <= Rvalu
                if Op == Symbol.GESY:
                    return Lvalu >= Rvalu
                if Op == Symbol.EQSY:
                    return Lvalu == Rvalu
                if Op == Symbol.NESY:
                    return Lvalu != Rvalu
                return False

            def CompReals(Left: Attr, Op: Symbol, Right: Attr) -> bool:
                """Compare two 32-bit real constant attributes `Left` and `Right` with relational operator `Op`."""
                assert Left.TreePtr is not None and Right.TreePtr is not None
                Lvalu = Left.TreePtr.CstValu.Rvalu
                Rvalu = Right.TreePtr.CstValu.Rvalu
                if Op == Symbol.LTSY:
                    return Lvalu < Rvalu
                if Op == Symbol.GTSY:
                    return Lvalu > Rvalu
                if Op == Symbol.LESY:
                    return Lvalu <= Rvalu
                if Op == Symbol.GESY:
                    return Lvalu >= Rvalu
                if Op == Symbol.EQSY:
                    return Lvalu == Rvalu
                if Op == Symbol.NESY:
                    return Lvalu != Rvalu
                return False

            def CompSets(Left: Attr, Op: Symbol, Right: Attr) -> bool:
                """Compare two constant set attributes `Left` and `Right` for `<=`, `>=`, `=`, or `<>`."""
                assert Left.TreePtr is not None and Right.TreePtr is not None
                Lmax = Left.TreePtr.CstValu.MaxSetEl
                Rmax = Right.TreePtr.CstValu.MaxSetEl
                lBv = False

                if Op == Symbol.LESY:
                    if Lmax > Rmax:
                        lBv = False
                    else:
                        lSetVal = Left.TreePtr.CstValu.SetValu
                        rSetVal = Right.TreePtr.CstValu.SetValu
                        lBv = True
                        while lSetVal is not None and rSetVal is not None and lBv:
                            if lSetVal.SetVal <= rSetVal.SetVal:
                                lSetVal = lSetVal.NextSet
                                rSetVal = rSetVal.NextSet
                            else:
                                lBv = False

                elif Op == Symbol.GESY:
                    if Rmax > Lmax:
                        lBv = False
                    else:
                        lSetVal = Left.TreePtr.CstValu.SetValu
                        rSetVal = Right.TreePtr.CstValu.SetValu
                        lBv = True
                        while lSetVal is not None and rSetVal is not None and lBv:
                            if lSetVal.SetVal >= rSetVal.SetVal:
                                lSetVal = lSetVal.NextSet
                                rSetVal = rSetVal.NextSet
                            else:
                                lBv = False

                elif Op == Symbol.EQSY:
                    if Lmax != Rmax:
                        lBv = False
                    else:
                        lSetVal = Left.TreePtr.CstValu.SetValu
                        rSetVal = Right.TreePtr.CstValu.SetValu
                        lBv = True
                        while lSetVal is not None and rSetVal is not None and lBv:
                            if lSetVal.SetVal == rSetVal.SetVal:
                                lSetVal = lSetVal.NextSet
                                rSetVal = rSetVal.NextSet
                            else:
                                lBv = False

                elif Op == Symbol.NESY:
                    lBv = Lmax != Rmax

                return lBv

            def CompStrs(Left: Attr, Op: Symbol, Right: Attr) -> bool:
                """Compare two string constant attributes `Left` and `Right` lexicographically with `Op`."""
                def Concat(StrValu: Valu) -> str:
                    """Reassemble chained `ALFALEN`-chunked string value `StrValu` into a `str` (up to 255 chars)."""
                    buf = ['\x00'] * 255
                    sval = StrValu.Svalu
                    length = 0
                    while sval is not None:
                        if length < 249:
                            for idx in range(ALFALEN):
                                if length + idx < 255:
                                    buf[length + idx] = sval.StrPart[idx]
                            length += ALFALEN
                            sval = sval.Next
                        else:
                            for idx in range(255 - length):
                                buf[length + idx] = sval.StrPart[idx]
                            sval = None
                    target_len = StrValu.SvaluLen & 0xFF
                    return ''.join(buf[:target_len])

                assert Left.TreePtr is not None and Right.TreePtr is not None
                LeftStr = Concat(Left.TreePtr.CstValu)
                RightStr = Concat(Right.TreePtr.CstValu)

                if Op == Symbol.LTSY:
                    return LeftStr < RightStr
                if Op == Symbol.GTSY:
                    return LeftStr > RightStr
                if Op == Symbol.LESY:
                    return LeftStr <= RightStr
                if Op == Symbol.GESY:
                    return LeftStr >= RightStr
                if Op == Symbol.EQSY:
                    return LeftStr == RightStr
                if Op == Symbol.NESY:
                    return LeftStr != RightStr
                return False

            SimpleConstExpression(Fsys | _REL_OPS)

            if self.Token in _REL_OPS:
                NonStd = True
                lToken = self.Token
                lAttr = self.gAttr.copy()

                self.Scan()
                SimpleConstExpression(Fsys)

                Bv = False
                if lAttr.Typtr is not None and self.gAttr.Typtr is not None:
                    if lToken in (
                        Symbol.LTSY,
                        Symbol.GTSY,
                        Symbol.LESY,
                        Symbol.GESY,
                        Symbol.EQSY,
                        Symbol.NESY,
                    ):
                        if not self.CompTypes(lAttr.Typtr, self.gAttr.Typtr):
                            if self.CompTypes(lAttr.Typtr, self.IntPtr):
                                Float(lAttr)
                            elif self.CompTypes(self.gAttr.Typtr, self.IntPtr):
                                Float(self.gAttr)
                            elif (
                                lAttr.Typtr.Form == TypeForms.SCONST
                                and self.gAttr.Typtr == self.CharPtr
                            ):
                                self.ChToString(self.gAttr)
                            elif (
                                lAttr.Typtr.Form == TypeForms.SCONST
                                and self.gAttr.Typtr == self.CharPtr
                            ):
                                self.ChToString(lAttr)
                        if self.CompTypes(lAttr.Typtr, self.gAttr.Typtr):
                            assert self.gAttr.Typtr is not None
                            form = self.gAttr.Typtr.Form
                            if form in (TypeForms.SCALAR, TypeForms.SUBRANGE):
                                if self.CompTypes(self.gAttr.Typtr, self.RealPtr):
                                    Bv = CompReals(lAttr, lToken, self.gAttr)
                                else:
                                    Bv = CompInts(lAttr, lToken, self.gAttr)
                            elif form == TypeForms.SETS:
                                if lToken in (Symbol.LTSY, Symbol.GTSY):
                                    Err(129)
                                else:
                                    Bv = CompSets(lAttr, lToken, self.gAttr)
                            elif form == TypeForms.SCONST:
                                Bv = CompStrs(lAttr, lToken, self.gAttr)
                            elif form == TypeForms.RECORDS:
                                Err(131)
                            elif form == TypeForms.FILES:
                                Err(130)
                            elif form in (
                                TypeForms.STRINGS,
                                TypeForms.CLASSES,
                                TypeForms.POINTERS,
                                TypeForms.ARRAYS,
                            ):
                                Err(179)
                        else:
                            Err(144)
                    elif lToken == Symbol.INSY:
                        if self.gAttr.Typtr.Form == TypeForms.SETS:
                            if self.CompTypes(lAttr.Typtr, self.gAttr.Typtr.SetOf):
                                assert lAttr.TreePtr is not None and self.gAttr.TreePtr is not None
                                i_val = lAttr.TreePtr.CstValu.Ivalu
                                if 0 <= i_val <= self.gAttr.TreePtr.CstValu.MaxSetEl:
                                    lSetVal = self.gAttr.TreePtr.CstValu.SetValu
                                    for _ in range(i_val // 32):
                                        assert lSetVal is not None
                                        lSetVal = lSetVal.NextSet
                                    assert lSetVal is not None
                                    Bv = (i_val % 32) in lSetVal.SetVal
                                else:
                                    Bv = False
                            else:
                                Err(127)
                        else:
                            Err(131)
                else:
                    self.gAttr.Typtr = None

                if self.gAttr.Typtr is not None:
                    self.gAttr.Typtr = self.BoolPtr
                    tp = N(NodeKind.CSTNODE)
                    tp.Node = NodeKind.CSTNODE
                    tp.CstType = self.BoolPtr
                    tp.CstValu.Ivalu = 1 if Bv else 0
                    self.gAttr.TreePtr = tp

        if self.Token not in ConstBegSys:
            self.Skip(24, FSys | ConstBegSys)
        if self.Token in ConstBegSys:
            ConstExpression(FSys)
            if self.gAttr.Typtr is None:
                fValu.Ivalu = 0
                FpT = self.IntPtr
            else:
                assert self.gAttr.TreePtr is not None
                fValu = self.gAttr.TreePtr.CstValu.copy()
                FpT = self.gAttr.TreePtr.CstType
            if self.Token not in FSys:
                self.Skip(20, FSys)
        else:
            fValu.Ivalu = 0
            FpT = self.IntPtr

        return fValu, FpT

    def EnterId(self, fN: N) -> None:
        """Insert identifier node `fN` into the current `Display[Top]` name tree.

        Reports error 100 if `fN.Name` duplicates an identifier in `Display[Top]` or (at level 1) any used unit.
        """
        DuplId = False
        fN.Llink = None
        fN.Rlink = None

        if self.Top == 1 and self.UnitList is not None:
            # Search the used units for this identifier.
            lUnitP: Optional[N] = self.UnitList
            if lUnitP.Ulev == -1:
                lUnitP = lUnitP.Next
            while lUnitP is not None and not DuplId:
                lN: Optional[N] = lUnitP
                while lN is not None and not DuplId:
                    if lN.Name == fN.Name:
                        DuplId = True
                    elif lN.Name < fN.Name:
                        lN = lN.Llink
                    else:
                        lN = lN.Rlink
                lUnitP = lUnitP.Next

        lN = self.Display[self.Top].NameTree
        if lN is None:
            self.Display[self.Top].NameTree = fN
        else:
            while lN is not None:
                if lN.Name == fN.Name:
                    DuplId = True
                    lN = lN.Llink
                elif lN.Name < fN.Name:
                    if lN.Llink is None:
                        lN.Llink = fN
                        lN = None
                    else:
                        lN = lN.Llink
                elif lN.Rlink is None:
                    lN.Rlink = fN
                    lN = None
                else:
                    lN = lN.Rlink

        if DuplId:
            self.Error(100)

    def SearchLocal(self, FTree: Optional[N]) -> Optional[N]:
        """Look up `self.Ident` in binary search tree `FTree`, checking `UnitList` trees first at `Display[1]`."""
        lpN = FTree
        ExitFlag = False
        if (FTree is self.Display[1].NameTree) and (self.UnitList is not None):
            # Search the used units FIRST.
            lUnitP: Optional[N] = self.UnitList
            if lUnitP.Ulev == -1:
                lUnitP = lUnitP.Next
            while lUnitP is not None and not ExitFlag:
                lpN = lUnitP
                while lpN is not None and not ExitFlag:
                    if lpN.Name == self.Ident:
                        ExitFlag = True
                    elif lpN.Name < self.Ident:
                        lpN = lpN.Llink
                    else:
                        lpN = lpN.Rlink
                if not ExitFlag:
                    lUnitP = lUnitP.Next
            if not ExitFlag:
                lpN = FTree

        while lpN is not None and not ExitFlag:
            if lpN.Name == self.Ident:
                ExitFlag = True
            elif lpN.Name < self.Ident:
                lpN = lpN.Llink
            else:
                lpN = lpN.Rlink
        return lpN

    def SearchClasses(self, FpT: Optional[T], StartAtSuper: bool) -> tuple[Optional[N], bool]:
        """Search class `FpT` and its `SuperClass` chain for `self.Ident`, hiding inherited `CREATE` methods.

        Returns `(node, HigherLevel)` indicating the matching member node (or `None`) and whether a superclass was reached.
        """
        ExitFlag = False
        HigherLevel = StartAtSuper
        lpN: Optional[N] = None

        while FpT is not None and not ExitFlag:
            lpN = FpT.ClFields
            while lpN is not None and not ExitFlag:
                if lpN.Name == self.Ident:
                    ExitFlag = True
                    if HigherLevel:
                        if lpN.Class == NameClass.PROC or lpN.Class == NameClass.FUNC:
                            if lpN.Name == 'CREATE  ':
                                ExitFlag = False
                                lpN = None
                elif lpN.Name < self.Ident:
                    lpN = lpN.Llink
                else:
                    lpN = lpN.Rlink
            if not ExitFlag:
                FpT = FpT.SuperClass
                HigherLevel = True

        return lpN, HigherLevel

    def SearchAll(self, fClass: set[NameClass] | frozenset[NameClass]) -> Optional[N]:
        """Search open scopes from `Display[Top]` down to `0` (including `WITH` classes and used units) for `self.Ident` in `fClass`.

        Updates `self.Disx` on match; if unfound and `PrintErrors` is set, logs error 102 and returns a class-appropriate dummy node.
        """
        lpN: Optional[N] = None

        for lDisx in range(self.Top, -1, -1):
            if lDisx == 1 and self.UnitList is not None:
                # Search the used units first.
                lUnitP: Optional[N] = self.UnitList
                if lUnitP.Ulev == -1:
                    lUnitP = lUnitP.Next
                while lUnitP is not None:
                    lpN = lUnitP
                    while lpN is not None:
                        if lpN.Name == self.Ident:
                            if lpN.Class in fClass:
                                self.Disx = lDisx
                                return lpN
                            if self.PrintErrors:
                                self.Error(101)
                            lpN = lpN.Llink
                        elif lpN.Name < self.Ident:
                            lpN = lpN.Llink
                        else:
                            lpN = lpN.Rlink
                    lUnitP = lUnitP.Next

            disp = self.Display[lDisx]
            if disp.Occur == Where.KLASS and disp.KType is not None:
                # Process WITH'ed class record.
                lpN, _ = self.SearchClasses(disp.KType, False)
                if lpN is not None:
                    if lpN.Class in fClass:
                        self.Disx = lDisx
                        return lpN
                    if self.PrintErrors:
                        self.Error(101)
                # GOTO 2: advance to next display level without searching NameTree.
                continue

            lpN = disp.NameTree
            while lpN is not None:
                if lpN.Name == self.Ident:
                    if lpN.Class in fClass:
                        self.Disx = lDisx
                        return lpN
                    if self.PrintErrors:
                        self.Error(101)
                    lpN = lpN.Llink
                elif lpN.Name < self.Ident:
                    lpN = lpN.Llink
                else:
                    lpN = lpN.Rlink

        # No such identifier of the correct class. Return a dummy if PrintErrors.
        lpN = None
        self.Disx = 0
        if self.PrintErrors:
            self.Error(102)
            if NameClass.VARS in fClass:
                lpN = self.uVarPtr
            elif NameClass.TYPES in fClass:
                lpN = self.uTypPtr
            elif NameClass.CONSTS in fClass:
                lpN = self.uCstPtr
            elif NameClass.FIELD in fClass:
                lpN = self.uFldPtr
            elif NameClass.PROC in fClass:
                lpN = self.uPrcPtr
            else:
                lpN = self.uFctPtr

        return lpN

    def Skip(self, ErrorNo: int, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Report `ErrorNo` (when non-zero) and advance tokens until `self.Token` belongs to `FSys`."""
        if ErrorNo != 0:
            self.Error(ErrorNo)
        while self.Token not in FSys:
            self.Scan()

    def Out(self, a: int) -> None:
        """Append byte `a & 0xFF` to `.I` buffer `Buff`, flushing `BuffBlockSize` blocks to `ICodeFile` when full."""
        if self.ByteNo >= BuffByteSize:
            if (
                self.rt.block_write(self.ICodeFile, self.Buff, BuffBlockSize, self.BlockNo)
                != BuffBlockSize
            ):
                self.FatalOutputError()
            self.BlockNo += BuffBlockSize
            self.ByteNo = 0
        self.Buff[self.ByteNo] = a & 0xFF
        self.ByteNo += 1

    def Out2(self, a: int) -> None:
        """Emit 16-bit word `a` to the `.I` intermediate code buffer in big-endian byte order."""
        u = u16(a)
        self.Out((u >> 8) & 0xFF)
        self.Out(u & 0xFF)

    def ForwSearch(self, FpN: Optional[N]) -> None:
        """Traverse name tree `FpN` in order and report errors 176/177 for unresolved `FORWARD` routines."""
        if FpN is not None:
            self.ForwSearch(FpN.Llink)
            if FpN.Class == NameClass.PROC or FpN.Class == NameClass.FUNC:
                if FpN.PFdeclKind == DeclKind.DECLARED:
                    if FpN.PFdecl == PFkind.FORWDECL:
                        if FpN.Class == NameClass.PROC:
                            self.NError(176, FpN.Name)
                        else:
                            self.NError(177, FpN.Name)
            self.ForwSearch(FpN.Rlink)

    def HasBody(
        self, FSys: set[Symbol] | frozenset[Symbol], ProcpN: N, HeapMark: int
    ) -> tuple[bool, int]:
        """Parse `FORWARD`, `EXTERNAL`, `INLINE`, or `C` directives after routine header `ProcpN`.

        Returns `(True, HeapMark)` when a routine body follows, or `(False, HeapMark)` if handled by a directive.
        """
        has_body = True

        if self.Token == Symbol.IDENTSY:
            has_body = False

            if self.Ident == 'FORWARD ':
                if self.InterFlag or self.InUses:
                    self.Error(20)
                if ProcpN.PFdecl == PFkind.DECL:
                    ProcpN.PFdecl = PFkind.FORWDECL
                    self.Forwcount += 1
                else:
                    self.Error(175)
                self.Scan()

            elif self.Ident == 'EXTERNAL':
                if self.InterFlag or self.InUses:
                    self.Error(20)
                if ProcpN.PFdecl == PFkind.FORWDECL:
                    self.Forwcount -= 1
                ProcpN.PFdecl = PFkind.EXTDECL
                ProcpN.RtnNo = -1
                if self.DebugOpen:
                    disp = self.Display[self.Top]
                    self.DumpSyms(disp.ProcBase, disp.NameTree, None, ProcpN)
                self.Scan()

            elif self.Ident == 'INLINE  ':
                if ProcpN.PFdecl != PFkind.DECL:
                    self.Error(186)
                ProcpN.PFdecl = PFkind.INLINEDECL
                LastWord: Optional[InlineCode] = None
                while True:
                    self.Scan()
                    InlineWord, lpT = self.Constant(
                        FSys | frozenset({Symbol.COMMASY, Symbol.SEMISY})
                    )
                    if lpT is not None:
                        if lpT != self.IntPtr:
                            self.Error(185)
                            InlineWord.Ivalu = 0
                        elif InlineWord.Ivalu < -32768 or InlineWord.Ivalu > 65535:
                            self.Error(185)
                            InlineWord.Ivalu = 0
                        CodeWord = InlineCode(i16(InlineWord.Ivalu), None)
                        if LastWord is None:
                            ProcpN.InlineCode = CodeWord
                        else:
                            LastWord.NextInlineWord = CodeWord
                        LastWord = CodeWord
                    if self.Token != Symbol.COMMASY:
                        break

            elif self.Ident == 'C       ':
                if self.InterFlag or self.InUses:
                    self.Error(20)
                if ProcpN.PFdecl == PFkind.FORWDECL:
                    self.Forwcount -= 1
                    self.Error(187)
                ProcpN.PFdecl = PFkind.CDECL
                ProcpN.RtnNo = -1
                if self.DebugOpen:
                    disp = self.Display[self.Top]
                    self.DumpSyms(disp.ProcBase, disp.NameTree, None, ProcpN)
                self.Scan()

            else:
                self.Error(162)
                self.Scan()

            if self.InterFlag or self.InUses:
                if self.Token == Symbol.SEMISY:
                    self.Scan()
                else:
                    self.Error(36)

        return has_body, HeapMark

    def PFList(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile consecutive `PROCEDURE` and `FUNCTION` declarations, optimizing and dumping I-code for each body."""
        ExitFlag = False
        OldLevel = self.Level
        OldTop = self.Top
        OldProc = self.CurrentProc
        OldForwCount = self.Forwcount
        ProcpN: Optional[N] = None
        HeapMark: int = 0

        while not ExitFlag:
            if self.Token == Symbol.PROCSY or self.Token == Symbol.FUNCTSY:
                if self.Level > 0:
                    self.ProcLev = chr(ord('A') + self.Level - 1)
                else:
                    self.ProcLev = 'A'

                lToken = self.Token
                self.Scan()
                ProcpN, HeapMark = self.Declarations(
                    FSys | frozenset({Symbol.IDENTSY}), lToken, ProcpN, HeapMark, None
                )
                assert ProcpN is not None
                self.CurrentProc = ProcpN

                has_body, HeapMark = self.HasBody(FSys, ProcpN, HeapMark)
                if has_body:
                    if ProcpN.PFdecl == PFkind.FORWDECL:
                        ProcpN.PFdecl = PFkind.DECL
                        self.Forwcount -= 1

                    while True:
                        self.PFList(FSys)
                        if self.Token in IdDecBegSys:
                            ProcpN, HeapMark = self.Declarations(
                                FSys, self.Token, ProcpN, HeapMark, None
                            )
                            assert ProcpN is not None
                        if self.Token not in DecBegSys:
                            break

                    if self.Token == Symbol.BEGINSY:
                        self.LeftCheck()
                        if self.Level > 1:
                            self.ProcLev = chr(ord('A') + self.Level - 2)
                        self.Scan()
                    else:
                        self.Error(43)

                    while True:
                        self.ProcStmt = self.Body(FSys | frozenset({Symbol.CASESY}), ProcpN.Name)
                        if self.Token != Symbol.SEMISY:
                            self.Skip(20, FSys)
                        if self.Errors == 0 and self.CodeFlag:
                            self.RegMask.sMask = set()
                            if self.OptFlag:
                                if self.OptLimFlag:
                                    self.Optimize(self.ProcStmt, ProcpN)
                                    self.ProcStmt = self.BindRegisters(self.ProcStmt, ProcpN)
                                else:
                                    self.ProcStmt = self.GlobalOptimize(self.ProcStmt, ProcpN)
                            if self.DebugOpen or self.DebugDebug:
                                disp = self.Display[self.Top]
                                self.DumpSyms(disp.ProcBase, disp.NameTree, self.ProcStmt, ProcpN)
                            self.Dump(self.ProcStmt, ProcpN, False)
                        if self.Token == Symbol.SEMISY or self.Token in BlockBegSy:
                            break

                if self.Token == Symbol.SEMISY:
                    self.Scan()
                else:
                    self.Error(36)

                self.Level = OldLevel
                self.Top = OldTop
                self.CurrentProc = OldProc
            else:
                ExitFlag = True

        if self.Token not in (frozenset({Symbol.BEGINSY}) | IdDecBegSys):
            self.Skip(22, FSys)

        if self.Forwcount > OldForwCount:
            if self.ForwChkFlag:
                self.ForwSearch(self.Display[self.Top].NameTree)
                self.Forwcount = OldForwCount

    def BodyCount(self, ThisClass: Optional[T]) -> None:
        """Verify that every method declared on `ThisClass` received a body, reporting error 805 otherwise."""
        if ThisClass is None:
            return
        ThisMethod = ThisClass.ClFstMethod
        while ThisMethod is not None:
            if ThisMethod.PFdecl == PFkind.FORWMETHDECL:
                self.NError(805, ThisMethod.Name)
            ThisMethod = ThisMethod.Next

    def AddMethodInfo(
        self, ProcStmt: Optional[Stmt], ThisClass: T, ClassName: str
    ) -> Optional[Stmt]:
        """Prefix class creation body `ProcStmt` with `%_CLASS` runtime interpreter calls and method-slot descriptors.

        Builds the call sequence used at runtime to populate `ThisClass`'s method dispatch tables.
        """
        if ProcStmt is not None:
            LineNbr = ProcStmt.StmtNumb
        else:
            LineNbr = self.TotalLines

        LastStmt = Stmt(StmtTypes.CALLST)
        LastStmt.NextStmt = ProcStmt
        ProcStmt = LastStmt
        LastStmt.StmtOp = StmtTypes.CALLST
        LastStmt.StmtNumb = LineNbr
        LastStmt.ProcpN = self.KlassPtr

        # 1st arg - type Alfa (ClassName)
        arg1 = N(NodeKind.BINNODE)
        arg1.Node = NodeKind.BINNODE
        arg1.BinOp = 0
        arg1.BinSubOp = 0
        la1 = N(NodeKind.CSTNODE)
        la1.Node = NodeKind.CSTNODE
        la1.CstValu.SvaluLen = 8
        la1.CstValu.Svalu = StrValRec(alfa8(ClassName), None)
        ct1 = T(TypeForms.SCONST)
        ct1.FType = False
        ct1.Form = TypeForms.SCONST
        ct1.Bits = 0
        ct1.Bytes = 8
        ct1.StringLen = 8
        la1.CstType = ct1
        arg1.LeftArg = la1

        # 2nd arg - SuperClass name
        arg2 = N(NodeKind.BINNODE)
        arg2.Node = NodeKind.BINNODE
        arg2.BinOp = 0
        arg2.BinSubOp = 0
        la2 = N(NodeKind.CSTNODE)
        la2.Node = NodeKind.CSTNODE
        la2.CstValu.SvaluLen = 8
        if ThisClass.SuperClass is None:
            super_part = 'NIL     '
        elif ThisClass.SuperClass.ItsId is None:
            super_part = 'NIL     '
        else:
            super_part = ThisClass.SuperClass.ItsId.Name
        la2.CstValu.Svalu = StrValRec(alfa8(super_part), None)
        ct2 = T(TypeForms.SCONST)
        ct2.FType = False
        ct2.Form = TypeForms.SCONST
        ct2.Bits = 0
        ct2.Bytes = 8
        ct2.StringLen = 8
        la2.CstType = ct2
        arg2.LeftArg = la2
        arg1.RightArg = arg2

        # 3rd arg - MasterPtr
        arg3 = N(NodeKind.BINNODE)
        arg3.Node = NodeKind.BINNODE
        arg3.BinOp = 0
        arg3.BinSubOp = 0
        la3 = N(NodeKind.IDENTNODE)
        la3.IdType = self.LIntPtr
        la3.Node = NodeKind.IDENTNODE
        la3.Class = NameClass.VARS
        la3.Vkind = AccessKind.DRCT
        la3.IsSELF = False
        la3.InRegister = -1
        la3.Vlev = ThisClass.MethodLevel
        la3.Voff = ThisClass.MethodOff
        arg3.LeftArg = la3
        arg2.RightArg = arg3

        # 4th arg - LastEvenMethod
        arg4 = N(NodeKind.BINNODE)
        arg4.Node = NodeKind.BINNODE
        arg4.BinOp = 0
        arg4.BinSubOp = 0
        arg4.RightArg = None
        la4 = N(NodeKind.CSTNODE)
        la4.Node = NodeKind.CSTNODE
        la4.CstType = self.IntPtr
        la4.CstValu.Ivalu = ThisClass.LastEvenMethod
        arg4.LeftArg = la4
        arg3.RightArg = arg4

        # 5th arg - LastOddMethod
        arg5 = N(NodeKind.BINNODE)
        arg5.Node = NodeKind.BINNODE
        arg5.BinOp = 0
        arg5.BinSubOp = 0
        arg5.RightArg = None
        la5 = N(NodeKind.CSTNODE)
        la5.Node = NodeKind.CSTNODE
        la5.CstType = self.IntPtr
        la5.CstValu.Ivalu = ThisClass.LastOddMethod
        arg5.LeftArg = la5
        arg4.RightArg = arg5

        # 6th arg - SizeInstance
        arg6 = N(NodeKind.BINNODE)
        arg6.Node = NodeKind.BINNODE
        arg6.BinOp = 0
        arg6.BinSubOp = 0
        arg6.RightArg = None
        la6 = N(NodeKind.CSTNODE)
        la6.Node = NodeKind.CSTNODE
        la6.CstType = self.IntPtr
        la6.CstValu.Ivalu = ThisClass.SizeInstance
        arg6.LeftArg = la6
        arg5.RightArg = arg6

        LastStmt.pArgList = arg1

        ThisMethod = ThisClass.ClFstMethod
        PrevN = ThisClass.ClassLevel * 256

        while ThisMethod is not None:
            if ThisMethod.MethodNo != 0 and ThisMethod.RtnNo != 0:
                n_val = ThisMethod.MethodLevel * 256 + ThisMethod.MethodNo
                iProc = N(NodeKind.IDENTNODE)
                iProc.Name = ThisMethod.Name
                iProc.Node = NodeKind.IDENTNODE
                iProc.Class = NameClass.PROC
                iProc.PFdeclKind = DeclKind.DECLARED
                iProc.PFdecl = PFkind.DECL
                iProc.IdType = None
                iProc.Next = None
                iProc.Lc = 0
                iProc.PFlev = ThisMethod.PFlev
                iProc.RtnNo = ThisMethod.RtnNo
                if (PrevN + 1) == n_val:
                    iProc.PFargList = None
                    iProc.ParmBytes = 0
                else:
                    iProc.ParmBytes = 10
                    pf_arg = N(NodeKind.IDENTNODE)
                    pf_arg.Node = NodeKind.IDENTNODE
                    pf_arg.Class = NameClass.VARS
                    pf_arg.Vkind = AccessKind.DRCT
                    pf_arg.IdType = self.IntPtr
                    pf_arg.IsSELF = False
                    pf_arg.InRegister = -1
                    pf_arg.Next = None
                    pf_arg.Vlev = 2
                    pf_arg.Voff = 8
                    iProc.PFargList = pf_arg

                NewStmt = Stmt(StmtTypes.CALLST)
                NewStmt.StmtNumb = LineNbr
                NewStmt.StmtOp = StmtTypes.CALLST
                NewStmt.ProcpN = iProc
                if iProc.PFargList is None:
                    NewStmt.pArgList = None
                else:
                    pa = N(NodeKind.BINNODE)
                    pa.Node = NodeKind.BINNODE
                    pa.BinOp = 0
                    pa.BinSubOp = 0
                    pa.RightArg = None
                    pla = N(NodeKind.CSTNODE)
                    pla.Node = NodeKind.CSTNODE
                    pla.CstType = self.IntPtr
                    pla.CstValu.Ivalu = n_val
                    pa.LeftArg = pla
                    NewStmt.pArgList = pa

                NewStmt.NextStmt = LastStmt.NextStmt
                LastStmt.NextStmt = NewStmt
                LastStmt = NewStmt
                PrevN = n_val

            ThisMethod = ThisMethod.Next

        NewStmt = Stmt(StmtTypes.CALLST)
        NewStmt.NextStmt = LastStmt.NextStmt
        LastStmt.NextStmt = NewStmt
        NewStmt.StmtNumb = LineNbr
        NewStmt.StmtOp = StmtTypes.CALLST
        NewStmt.pArgList = None
        end_proc = N(NodeKind.IDENTNODE)
        end_proc.Name = '%_CLASS '
        end_proc.Node = NodeKind.IDENTNODE
        end_proc.Class = NameClass.PROC
        end_proc.PFdeclKind = DeclKind.DECLARED
        end_proc.PFdecl = PFkind.DECL
        end_proc.IdType = None
        end_proc.Next = None
        end_proc.PFargList = None
        end_proc.ParmBytes = 0
        end_proc.Lc = 0
        end_proc.PFlev = 1
        end_proc.RtnNo = -1
        NewStmt.ProcpN = end_proc

        return ProcStmt

    def ImplPFList(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile unit `IMPLEMENTATION` routines and `METHODS OF <Class>` sections, including class creation bodies."""
        OldLevel = self.Level
        OldTop = self.Top
        OldProc = self.CurrentProc
        OldForwCount = self.Forwcount
        ExitFlag = False
        SawMethods = False
        self.ThisClass = None
        InitProc = 'No Name!'
        self.CurrClass = ''
        ProcpN: Optional[N] = None
        HeapMark: int = 0

        while not ExitFlag:
            if self.Token == Symbol.METHSY:
                if SawMethods:
                    # Forgot to end methods section.
                    self.Error(44)
                    if self.ThisClass is not None:
                        self.BodyCount(self.ThisClass)
                        self.ThisClass.WasDeclared = True
                    self.Level = OldLevel
                    self.Top = OldTop
                    self.CurrentProc = OldProc
                    self.ThisClass = None
                    InitProc = 'No Name!'
                    self.CurrClass = ''
                    SawMethods = False

                self.Scan()
                if self.Token == Symbol.OFSY:
                    self.Scan()
                else:
                    self.Error(800)

                InitProc = 'No Name!'
                self.CurrClass = ''

                if self.Token == Symbol.IDENTSY:
                    lpN = self.SearchLocal(self.Display[self.Top].NameTree)
                    if lpN is None:
                        self.Error(101)
                    else:
                        if lpN.Class != NameClass.TYPES or lpN.IdType is None:
                            self.Error(101)
                        elif lpN.IdType.Form != TypeForms.CLASSES:
                            self.Error(101)
                        else:
                            self.ThisClass = lpN.IdType
                            self.LocProcNo += 1
                            if self.ThisClass.ItsId is not None:
                                InitProc = self.ThisClass.ItsId.Name
                            else:
                                InitProc = lpN.Name
                            i = 1
                            b = True
                            chars: list[str] = []
                            while b:
                                chars.append(lpN.Name[i - 1])
                                i += 1
                                if i > 8:
                                    b = False
                                elif lpN.Name[i - 1] == ' ':
                                    b = False
                            chars.append('.')
                            self.CurrClass = ''.join(chars)
                    self.Scan()
                    if self.Token == Symbol.SEMISY:
                        self.Scan()

                if self.ThisClass is not None and self.ThisClass.WasDeclared:
                    self.Error(101)
                SawMethods = True

            elif self.Token == Symbol.PROCSY or self.Token == Symbol.FUNCTSY:
                lToken = self.Token
                if self.Level > 0:
                    self.ProcLev = chr(ord('A') + self.Level - 1)
                else:
                    self.ProcLev = 'A'

                self.Scan()
                if self.Token == Symbol.IDENTSY and self.Ident == InitProc:
                    self.Scan()
                    if self.Token == Symbol.PERIODSY:
                        self.Scan()
                    else:
                        self.Error(51)

                ProcpN, HeapMark = self.Declarations(
                    FSys | frozenset({Symbol.IDENTSY}), lToken, ProcpN, HeapMark, self.ThisClass
                )
                assert ProcpN is not None
                self.CurrentProc = ProcpN

                has_body, HeapMark = self.HasBody(FSys, ProcpN, HeapMark)
                if has_body:
                    if ProcpN.PFdecl == PFkind.FORWMETHDECL:
                        ProcpN.PFdecl = PFkind.METHDECL
                    elif ProcpN.PFdecl == PFkind.FORWDECL:
                        ProcpN.PFdecl = PFkind.DECL
                        self.Forwcount -= 1

                    SaveClass = self.CurrClass
                    self.CurrClass = ''
                    while True:
                        self.PFList(FSys)
                        if self.Token in IdDecBegSys:
                            ProcpN, HeapMark = self.Declarations(
                                FSys, self.Token, ProcpN, HeapMark, self.ThisClass
                            )
                            assert ProcpN is not None
                        if self.Token not in DecBegSys:
                            break
                    self.CurrClass = SaveClass

                    if self.Token == Symbol.BEGINSY:
                        self.LeftCheck()
                        if self.Level > 1:
                            self.ProcLev = chr(ord('A') + self.Level - 2)
                        self.Scan()
                    else:
                        self.Error(43)

                    while True:
                        self.ProcStmt = self.Body(FSys | frozenset({Symbol.CASESY}), ProcpN.Name)
                        if self.Token != Symbol.SEMISY:
                            self.Skip(20, FSys)
                        if self.Errors == 0 and self.CodeFlag:
                            self.RegMask.sMask = set()
                            if self.OptFlag:
                                if self.OptLimFlag:
                                    self.Optimize(self.ProcStmt, ProcpN)
                                    self.ProcStmt = self.BindRegisters(self.ProcStmt, ProcpN)
                                else:
                                    self.ProcStmt = self.GlobalOptimize(self.ProcStmt, ProcpN)
                            if self.DebugOpen or self.DebugDebug:
                                disp = self.Display[self.Top]
                                self.DumpSyms(disp.ProcBase, disp.NameTree, self.ProcStmt, ProcpN)
                            if ProcpN.PFdecl == PFkind.METHDECL and ProcpN.Name == 'CREATE  ':
                                ProcpN.Name = InitProc
                                self.Dump(self.ProcStmt, ProcpN, False)
                                ProcpN.Name = 'CREATE  '
                            else:
                                self.Dump(self.ProcStmt, ProcpN, False)
                        if self.Token == Symbol.SEMISY or self.Token in BlockBegSy:
                            break

                if self.Token == Symbol.SEMISY:
                    self.Scan()
                else:
                    self.Error(36)

                self.Level = OldLevel
                self.Top = OldTop
                self.CurrentProc = OldProc

            elif self.Token == Symbol.BEGINSY or (self.Token == Symbol.ENDSY and SawMethods):
                if not SawMethods:
                    self.Error(20)
                SawMethods = False
                lToken = self.Token
                ProcpN, HeapMark = self.Declarations(
                    FSys | frozenset({Symbol.IDENTSY}), lToken, ProcpN, HeapMark, self.ThisClass
                )
                assert ProcpN is not None

                if lToken == Symbol.BEGINSY:
                    if self.Level > 1:
                        self.ProcLev = chr(ord('A') + self.Level - 2)
                    self.LeftCheck()

                self.Scan()

                if self.ThisClass is not None:
                    self.ThisClass.CrProc = ProcpN
                self.CurrentProc = ProcpN

                if lToken == Symbol.BEGINSY:
                    self.ProcStmt = self.Body(AllBegSys, ProcpN.Name)
                else:
                    self.ProcStmt = None
                    if not self.ConsListing or not self.Listing:
                        sys.stdout.write(self.ShowProcName(self.CurrClass, ProcpN.Name, 2) + '\n')

                if self.ThisClass is not None:
                    self.BodyCount(self.ThisClass)
                    self.ThisClass.WasDeclared = True

                if self.Errors == 0 and self.CodeFlag:
                    assert self.ThisClass is not None
                    self.ProcStmt = self.AddMethodInfo(self.ProcStmt, self.ThisClass, InitProc)
                    if self.OptFlag:
                        if self.OptLimFlag:
                            self.Optimize(self.ProcStmt, ProcpN)
                        else:
                            self.ProcStmt = self.GlobalOptimize(self.ProcStmt, ProcpN)
                    self.RegMask.sMask = set()
                    self.Dump(self.ProcStmt, ProcpN, False)

                if self.Token == Symbol.SEMISY:
                    self.Scan()
                else:
                    self.Error(36)

                self.Level = OldLevel
                self.Top = OldTop
                self.CurrentProc = OldProc
                self.ThisClass = None
                InitProc = 'No Name!'
                self.CurrClass = ''

            else:
                ExitFlag = True

        if self.Token not in (frozenset({Symbol.ENDSY}) | IdDecBegSys):
            self.Skip(22, FSys)

        if self.Forwcount > OldForwCount:
            if self.ForwChkFlag:
                self.ForwSearch(self.Display[self.Top].NameTree)
                self.Forwcount = OldForwCount

    def ClassCount(self) -> None:
        """Verify that all classes declared in the current unit had a `METHODS OF` section, reporting error 806 otherwise."""
        if self.NilClassPtr is None:
            return
        ThisClass = self.NilClassPtr.TotalOrder
        while ThisClass is not None:
            if not ThisClass.WasDeclared:
                if ThisClass.ItsId is not None:
                    self.NError(806, ThisClass.ItsId.Name)
            ThisClass = ThisClass.TotalOrder

    def CallUsedUnits(
        self, ProcStmt: Optional[Stmt], LastStmt: Optional[Stmt]
    ) -> tuple[Optional[Stmt], Optional[Stmt]]:
        """Prepend `%_PGM1`/`%_UNIT`, used-unit class initialization calls, and `%_PGM2` onto statement list `ProcStmt`."""
        if ProcStmt is not None:
            LineNbr = ProcStmt.StmtNumb
        else:
            LineNbr = self.TotalLines

        if not self.InUnit:
            NewStmt = Stmt(StmtTypes.CALLST)
            NewStmt.NextStmt = ProcStmt
            ProcStmt = NewStmt
            if LastStmt is None:
                LastStmt = NewStmt
            NewStmt.StmtNumb = LineNbr
            NewStmt.StmtOp = StmtTypes.CALLST
            NewStmt.pArgList = None
            p = N(NodeKind.IDENTNODE)
            p.Name = '%_PGM2  '
            p.Class = NameClass.PROC
            p.Node = NodeKind.IDENTNODE
            p.IdType = None
            p.Next = None
            p.ParmBytes = 0
            p.Lc = 0
            p.PFdeclKind = DeclKind.DECLARED
            p.PFdecl = PFkind.DECL
            p.PFargList = None
            p.PFlev = 1
            p.RtnNo = -1
            NewStmt.ProcpN = p

        lUnitP = self.UnitList
        while lUnitP is not None:
            if lUnitP.HasClasses:
                NewStmt = Stmt(StmtTypes.CALLST)
                NewStmt.NextStmt = ProcStmt
                ProcStmt = NewStmt
                if LastStmt is None:
                    LastStmt = NewStmt
                NewStmt.StmtNumb = LineNbr
                NewStmt.StmtOp = StmtTypes.CALLST
                NewStmt.pArgList = None
                p = N(NodeKind.IDENTNODE)
                p.Name = _lower_alfa(lUnitP.Name)
                p.Class = NameClass.PROC
                p.Node = NodeKind.IDENTNODE
                p.IdType = None
                p.Next = None
                p.PFdeclKind = DeclKind.DECLARED
                p.PFdecl = PFkind.DECL
                p.PFargList = None
                p.ParmBytes = 0
                p.Lc = 0
                p.PFlev = 1
                p.RtnNo = -1
                NewStmt.ProcpN = p

            lUnitP = lUnitP.Next

        NewStmt = Stmt(StmtTypes.CALLST)
        NewStmt.NextStmt = ProcStmt
        ProcStmt = NewStmt
        if LastStmt is None:
            LastStmt = NewStmt
        NewStmt.StmtNumb = LineNbr
        NewStmt.StmtOp = StmtTypes.CALLST
        NewStmt.pArgList = None
        p = N(NodeKind.IDENTNODE)
        if self.InUnit:
            p.Name = '%_UNIT  '
        else:
            p.Name = '%_PGM1  '
        p.Class = NameClass.PROC
        p.Node = NodeKind.IDENTNODE
        p.IdType = None
        p.Next = None
        p.ParmBytes = 0
        p.Lc = 0
        p.PFdeclKind = DeclKind.DECLARED
        p.PFdecl = PFkind.DECL
        p.PFargList = None
        p.PFlev = 1
        p.RtnNo = -1
        NewStmt.ProcpN = p

        return ProcStmt, LastStmt

    def InitClasses(
        self, ProcStmt: Optional[Stmt], LastStmt: Optional[Stmt]
    ) -> tuple[Optional[Stmt], Optional[Stmt]]:
        """Generate calls to `CrProc` class initialization routines in topological superclass-first order (`TotalOrder`)."""
        if ProcStmt is not None:
            LineNbr = ProcStmt.StmtNumb
        else:
            LineNbr = self.TotalLines
        LastStmt = None
        CurClass = self.NilClassPtr.TotalOrder if self.NilClassPtr is not None else None

        while CurClass is not None:
            if CurClass.NeedsInit:
                if CurClass.ItsId is not None:
                    if CurClass.CrProc is not None:
                        NewStmt = Stmt(StmtTypes.CALLST)
                        NewStmt.StmtNumb = LineNbr
                        NewStmt.StmtOp = StmtTypes.CALLST
                        NewStmt.ProcpN = CurClass.CrProc
                        NewStmt.ProcpN.PFdecl = PFkind.DECL
                        NewStmt.pArgList = None

                        if LastStmt is None:
                            NewStmt.NextStmt = ProcStmt
                            ProcStmt = NewStmt
                        else:
                            NewStmt.NextStmt = LastStmt.NextStmt
                            LastStmt.NextStmt = NewStmt
                        LastStmt = NewStmt

            CurClass = CurClass.TotalOrder

        return ProcStmt, LastStmt

    def InitUnit(self, FpN: N) -> None:
        """Synthesize and dump the external lowercase initialization procedure for unit `FpN` to init local classes and used units."""
        OldLevel = self.Level
        OldTop = self.Top
        OldProc = self.CurrentProc
        if not self.ConsListing or not self.Listing:
            sys.stdout.write(
                f'{self.ShowProcName("", FpN.Name, 2)}'
                f'  Unit Initialization in Segment "{self.SegName}"\n'
            )

        UnitpN: Optional[N] = None
        HeapMark: int = 0
        UnitpN, HeapMark = self.Declarations(set(), Symbol.BEGINSY, UnitpN, HeapMark, None)
        assert UnitpN is not None
        UnitpN.Name = _lower_alfa(FpN.Name)
        UnitpN.RtnNo = -1
        UnitpN.PFdecl = PFkind.DECL

        self.ProcStmt = None
        LastStmt: Optional[Stmt] = None
        if self.ClassesToInit or self.UnitsToInit:
            self.ProcStmt, LastStmt = self.InitClasses(self.ProcStmt, LastStmt)
            self.ProcStmt, LastStmt = self.CallUsedUnits(self.ProcStmt, LastStmt)

        lStmt = Stmt(StmtTypes.LABEDST)
        lStmt.NextStmt = None
        lStmt.StmtOp = StmtTypes.LABEDST
        lStmt.StLab = self.Display[self.Level].ExitLabel
        lStmt.LabStmt = None

        if self.ProcStmt is None:
            self.ProcStmt = lStmt
            lStmt.StmtNumb = self.TotalLines
        else:
            assert LastStmt is not None
            LastStmt.NextStmt = lStmt
            lStmt.StmtNumb = LastStmt.StmtNumb

        self.RegMask.sMask = set()
        self.Dump(self.ProcStmt, UnitpN, True)
        self.Level = OldLevel
        self.Top = OldTop
        self.CurrentProc = OldProc

    def UnitText(self, FpN: N) -> None:
        """Flush I-code, copy 1024-byte `INTERFACE` text pages into `ICodeFile`, flag unit init in byte 0, and patch block 0."""
        def ZeroLast(LastGoodByte: int) -> None:
            """Zero trailing bytes after the line-ending CR following `LastGoodByte` to the end of its 1024-byte page."""
            LastOnPage = pdiv(LastGoodByte, 1024) * 1024 + 1023
            while LastGoodByte < LastOnPage and self.Inbuf[LastGoodByte] != 13:
                LastGoodByte += 1
            for idx in range(LastGoodByte + 1, LastOnPage + 1):
                self.Inbuf[idx] = 0

        if self.Errors == 0:
            if self.ByteNo > 0:
                # Flush current contents of code buffer.
                BlocksUsed = (self.ByteNo - 1) // 512 + 1
                if (
                    self.rt.block_write(self.ICodeFile, self.Buff, BlocksUsed, self.BlockNo)
                    != BlocksUsed
                ):
                    self.FatalOutputError()
                self.BlockNo += BlocksUsed
                self.ByteNo = 0
            fBlock = self.BlockNo

            # Copy text block(s) into codefile.
            top_entry = self.OpenFileStack[self.TopOfOpenFileStack]
            if top_entry.FName != self.IntFName:
                self.rt.close_untyped(top_entry.SrcFile)
                self.rt.reset_untyped(top_entry.SrcFile, self.IntFName)
                if self.rt.io_result > 0:
                    self.Error(406)
                self.InbufNumValidBlocks = 0

            BufStart = top_entry.LastRelBlkRead
            LastBufPageStart = BufStart + self.InbufNumValidBlocks - 2
            if (
                self.InbufNumValidBlocks == 0
                or BufStart > self.FirstUBlock
                or LastBufPageStart < self.FirstUBlock
                or self.Inbuf[0] == 3
            ):
                self.FileSeek(self.FirstUBlock)
                self.FillInbuf()
                if self.Inbuf[0] == 3:
                    self.Error(406)
                top_entry = self.OpenFileStack[self.TopOfOpenFileStack]
                BufStart = top_entry.LastRelBlkRead
                LastBufPageStart = BufStart + self.InbufNumValidBlocks - 2

            # Point InbufP to beginning of interface in the buffer.
            self.InbufP = 512 * (self.FirstUBlock - BufStart) + self.FirstUByte
            PageStart = pdiv(self.InbufP, 1024) * 1024

            # Move the data to the beginning of the buffer.
            if PageStart > 1023:
                for i in range(PageStart, self.InbufLastValidByte + 1):
                    self.Inbuf[i - PageStart] = self.Inbuf[i]
                self.InbufP -= PageStart
                self.InbufNumValidBlocks -= self.FirstUBlock - BufStart
                BufStart = self.FirstUBlock

            # Move the data on the first page to the beginning of the page.
            for i in range(self.InbufP, 1024):
                self.Inbuf[i - self.InbufP] = self.Inbuf[i]

            # Set 1st byte to indicate whether this unit needs init call.
            if self.ClassesToInit or self.UnitsToInit:
                self.Inbuf[0] = (self.Inbuf[0] + 128) & 0xFF

            # Zero the rest of the first page.
            for i in range(1024 - self.InbufP, 1024):
                self.Inbuf[i] = 0

            # Write out the interface text, zeroing the unused portion of the last page.
            LastBlock = False
            while not LastBlock:
                if LastBufPageStart >= self.LastUBlock:
                    ZeroLast(512 * (self.LastUBlock - BufStart) + self.LastUByte)
                    self.InbufNumValidBlocks = self.LastUBlock - BufStart + 2
                    LastBlock = True
                if (
                    self.rt.block_write(
                        self.ICodeFile, self.Inbuf, self.InbufNumValidBlocks, self.BlockNo
                    )
                    != self.InbufNumValidBlocks
                ):
                    self.FatalOutputError()
                self.BlockNo += self.InbufNumValidBlocks
                if not LastBlock:
                    self.FillInbuf()
                    if self.Inbuf[0] == 3:
                        self.Error(406)
                    top_entry = self.OpenFileStack[self.TopOfOpenFileStack]
                    BufStart = top_entry.LastRelBlkRead
                    LastBufPageStart = BufStart + self.InbufNumValidBlocks - 2

            # Put address and size of text into first record in object file.
            if self.rt.block_read(self.ICodeFile, self.Buff, 1, 0) != 1:
                self.Error(401)
            NumBlocks = self.BlockNo - fBlock
            self.Buff[10] = pdiv(fBlock, 128) & 0xFF
            self.Buff[11] = pmod(fBlock * 2, 256) & 0xFF
            self.Buff[14] = pdiv(NumBlocks, 128) & 0xFF
            self.Buff[15] = pmod(NumBlocks * 2, 256) & 0xFF
            self.Buff[17] = pdiv(FpN.ULc, 256) & 0xFF
            self.Buff[18] = pmod(FpN.ULc, 256) & 0xFF
            if self.rt.block_write(self.ICodeFile, self.Buff, 1, 0) != 1:
                self.FatalOutputError()
            self.ByteNo = 0

    def Prog(self) -> None:
        """Compile a complete `PROGRAM` or `UNIT`, orchestrating declarations, bodies, optimization, `.I` output, and unit text."""
        if self.Token != Symbol.PROGRAMSY and self.Token != Symbol.UNITSY:
            self.Skip(41, frozenset({Symbol.PROGRAMSY, Symbol.UNITSY}))

        if self.Token == Symbol.PROGRAMSY:
            self.Scan()

            lpN: Optional[N] = N(NodeKind.IDENTNODE)
            lpN.Node = NodeKind.IDENTNODE
            lpN.Class = NameClass.PROC
            lpN.PFdeclKind = DeclKind.DECLARED
            lpN.RtnNo = -1
            lpN.PFlev = 0
            lpN.PFdecl = PFkind.DECL
            lpN.Lc = 0
            lpN.ParmBytes = 0
            lpN.Next = None
            lpN.PFargList = None
            lpN.Llink = None
            lpN.Rlink = None
            lpN.IdType = None

            if self.Token == Symbol.IDENTSY:
                lpN.Name = self.Ident
                self.ProgName = self.Ident
                self.Scan()
                if self.Token != Symbol.LPARENSY and self.Token != Symbol.SEMISY:
                    self.Skip(
                        23,
                        (AllBegSys - frozenset({Symbol.CASESY}))
                        | frozenset({Symbol.SEMISY, Symbol.LPARENSY}),
                    )

                if self.Token == Symbol.LPARENSY:
                    while True:
                        self.Scan()
                        if self.Token == Symbol.IDENTSY:
                            self.Scan()
                        else:
                            self.Error(29)
                        if self.Token != Symbol.RPARENSY and self.Token != Symbol.COMMASY:
                            self.Skip(
                                20,
                                (AllBegSys - frozenset({Symbol.CASESY}))
                                | frozenset({Symbol.COMMASY, Symbol.RPARENSY, Symbol.USESSY}),
                            )
                        if self.Token != Symbol.COMMASY:
                            break

                    if self.Token == Symbol.RPARENSY:
                        self.Scan()
                    else:
                        self.Error(32)

                if self.Token == Symbol.SEMISY:
                    self.Scan()
                else:
                    self.Error(36)
            else:
                lpN.Name = 'No name!'
                self.Skip(
                    29,
                    (AllBegSys - frozenset({Symbol.CASESY})) | frozenset({Symbol.USESSY}),
                )

            LastStmt: Optional[Stmt] = None
            prog_fsys = AllBegSys - frozenset({Symbol.CASESY, Symbol.METHSY})
            while True:
                lpN, self.HeapMark = self.Declarations(
                    prog_fsys | frozenset({Symbol.USESSY}),
                    Symbol.PROGRAMSY,
                    lpN,
                    self.HeapMark,
                    None,
                )
                assert lpN is not None
                self.CurrentProc = lpN

                while True:
                    self.PFList(prog_fsys)
                    if self.Token in IdDecBegSys:
                        lpN, self.HeapMark = self.Declarations(
                            prog_fsys, self.Token, lpN, self.HeapMark, None
                        )
                        assert lpN is not None
                    if self.Token not in DecBegSys:
                        break

                if self.Token == Symbol.BEGINSY:
                    self.LeftCheck()
                    self.Scan()
                else:
                    self.Error(43)

                while True:
                    self.ProcStmt = self.Body(AllBegSys, lpN.Name)
                    if self.Token != Symbol.PERIODSY:
                        self.Skip(51, AllBegSys - frozenset({Symbol.CASESY}))
                    self.SegName = '        '
                    if self.Errors == 0 and self.CodeFlag:
                        if self.OptFlag:
                            if self.OptLimFlag:
                                self.Optimize(self.ProcStmt, lpN)
                            else:
                                self.ProcStmt = self.GlobalOptimize(self.ProcStmt, lpN)
                        if self.DebugOpen or self.DebugDebug:
                            disp = self.Display[self.Top]
                            self.DumpSyms(disp.ProcBase, disp.NameTree, self.ProcStmt, lpN)
                        self.RegMask.sMask = set()

                        if self.UnitsToInit:
                            self.ProcStmt, LastStmt = self.CallUsedUnits(self.ProcStmt, LastStmt)
                            self.Dump(self.ProcStmt, lpN, True)
                        else:
                            self.Dump(self.ProcStmt, lpN, False)
                    if self.Token == Symbol.PERIODSY or self.Token in BlockBegSy:
                        break
                if self.Token == Symbol.PERIODSY:
                    break

            if self.CondStack[self.CondTos] != CondState.NULL:
                self.Error(267)
            # For host programs, dump level 0 symbols, if any.
            self.Top = 0
            if self.Errors == 0 and self.CodeFlag and (self.DebugOpen or self.DebugDebug):
                disp0 = self.Display[0]
                self.DumpSyms(disp0.ProcBase, disp0.NameTree, None, None)
                self.DbgOut2(0)

            self.Scan()
            self.Out(255)

        else:
            # UNIT
            self.Scan()
            self.InUnit = True
            self.NumUnits = 1
            self.Level = -1

            lpN = N(NodeKind.IDENTNODE)
            lpN.Node = NodeKind.IDENTNODE
            lpN.Class = NameClass.UNITS
            lpN.Ulev = -1
            lpN.ULc = 0
            lpN.Llink = None
            lpN.Rlink = None
            lpN.Next = None
            lpN.IdType = None
            lpN.Ukind = UnitKind.REGUNIT
            lpN.HasClasses = False
            self.UnitList = lpN

            if self.Token == Symbol.IDENTSY:
                lpN.Name = self.Ident
                self.ProgName = self.Ident
                self.Scan()
            else:
                lpN.Name = 'No name!'
                self.Skip(
                    29,
                    (AllBegSys - frozenset({Symbol.CASESY}))
                    | frozenset({
                        Symbol.SEMISY,
                        Symbol.INTRINSY,
                        Symbol.USESSY,
                        Symbol.INTERSY,
                        Symbol.IMPLESY,
                    }),
                )

            top_entry = self.OpenFileStack[self.TopOfOpenFileStack]
            self.IntFName = top_entry.FName
            self.FirstUBlock = top_entry.LastRelBlkRead + 2 * pdiv(self.InbufP, 1024)
            self.FirstUByte = pmod(self.InbufP, 1024)

            if self.Token == Symbol.SEMISY:
                self.Scan()
            else:
                self.Error(36)

            if self.Token == Symbol.INTERSY:
                self.Scan()
            elif self.Token != Symbol.INTRINSY:
                self.Error(53)

            unit_fsys = AllBegSys - frozenset({Symbol.CASESY})
            lpN, self.HeapMark = self.Declarations(
                unit_fsys, Symbol.UNITSY, lpN, self.HeapMark, None
            )
            assert lpN is not None

            if self.Errors == 0:
                self.Dump(None, lpN, False)

            while True:
                self.ImplPFList(unit_fsys)
                if self.Token in IdDecBegSys:
                    lpN, self.HeapMark = self.Declarations(
                        unit_fsys | frozenset({Symbol.ENDSY}),
                        self.Token,
                        lpN,
                        self.HeapMark,
                        None,
                    )
                    assert lpN is not None
                if self.Token not in (DecBegSys | frozenset({Symbol.METHSY})):
                    break

            self.ClassCount()

            if self.Forwcount != 0:
                if self.ForwChkFlag:
                    self.ForwSearch(self.Display[self.Top].NameTree)
                    self.Forwcount = 0

            if self.Token == Symbol.ENDSY:
                self.Scan()
            else:
                self.Error(44)

            if self.Token != Symbol.PERIODSY:
                self.Error(51)

            if self.ClassesToInit or self.UnitsToInit:
                self.InitUnit(lpN)

            if self.CondStack[self.CondTos] != CondState.NULL:
                self.Error(267)
            if self.Errors == 0:
                if self.DebugOpen or self.DebugDebug:
                    disp = self.Display[self.Top]
                    self.DumpSyms(disp.ProcBase, disp.NameTree, None, lpN)
                    # Don't dump level 0 symbols for UNITS.
                    self.DbgOut2(0)

            self.Scan()
            self.Out(255)
            self.UnitText(lpN)

    def LoadOPt1(self) -> None:
        """Segment-loader shim for the local optimizer (`OPT1`) that invokes `Prog`."""
        self.Prog()

    def LoadOPt2(self) -> None:
        """Segment-loader shim for the global optimizer (`OPT2`) that invokes `Prog`."""
        self.Prog()

    def LoadDump(self) -> None:
        """Segment-loader shim for `DUMP` that dispatches via `LoadOPt1`, `LoadOPt2`, or directly to `Prog`."""
        if self.OptFlag:
            if self.OptLimFlag:
                self.LoadOPt1()
            else:
                self.LoadOPt2()
        else:
            self.Prog()

    def LoadDebug(self) -> None:
        """Segment-loader shim for `DEBUG` symbol emission that chains to `LoadDump`."""
        self.LoadDump()

    def LoadDecl(self) -> None:
        """Segment-loader shim for `DECL` declaration parsing that chains to `LoadDebug`."""
        self.LoadDebug()

    def LoadBdy2(self) -> None:
        """Segment-loader shim for `BODY2` statement parsing that chains to `LoadDecl`."""
        self.LoadDecl()

    def LoadBdy1(self) -> None:
        """Segment-loader shim for `BODY1` expression parsing that chains to `LoadBdy2`."""
        self.LoadBdy2()

    def LoadConst(self) -> None:
        """Segment-loader shim for `CONST` constant evaluation that chains to `LoadBdy1`."""
        self.LoadBdy1()

    def Finalize(self) -> None:
        """Flush and close `ICodeFile`, output compilation summary statistics, chain to codegen/editor, and close open files."""
        def Summarize() -> None:
            """Format and emit the compilation error and line-count summary to listing, console, and error log."""
            if self.Aborted:
                Line = 'Compilation aborted - '
            else:
                Line = 'Compilation complete - '

            if self.Errors == 0:
                Line = Line + 'no error'
            else:
                Line = Line + self.rt.PutIntP(self.Errors, 0) + ' error'

            if self.Errors != 1:
                Line = Line + 's found.  '
            else:
                Line = Line + ' found.  '

            Line = (Line + self.rt.PutIntP(self.TotalLines - 1, 0) + ' lines.')[:80]

            if self.Listing and self.ListingFCBP is not None:
                self.rt.PutcF(self.ListingFCBP, IONewline)
                self.rt.PutLineS(self.ListingFCBP, Line)

            if not self.ConsListing:
                sys.stdout.write('\n' + Line + '\n')

            if self.ErrFileOpen:
                self.ErrFile.writeln()
                self.ErrFile.writeln(Line)

        def ChainToEdOrGen() -> None:
            """Write `ProgComm` directives to auto-launch the code generator on success or the editor on errors."""
            if self.Errors == 0:
                if self.CallGen:
                    self.rt.PCReWrite(self.rt.PCText, 'For Code Gen')
                    Ok = self.rt.PCPutLine(self.ICodeName)
                    if Ok:
                        Ok = self.rt.PCPutLine(self.ObjName)
                    if Ok:
                        Ok = self.rt.PCPutLine('$I+')
                    if Ok and self.AsmOnly:
                        Ok = self.rt.PCPutLine('$ASM ONLY')
                    if Ok and self.AsmProc:
                        Ok = self.rt.PCPutLine('$ASM PROC')
                    if Ok and self.SaveA2D3:
                        Ok = self.rt.PCPutLine('$A+')
                    if Ok and self.MacFlag:
                        Ok = self.rt.PCPutLine('$M+')
                    if not self.rt.PCClose(False, 'For Code Gen'):
                        Ok = False
                    if Ok:
                        self.rt.PCSetRunCmd(self.Gcmd)
                    else:
                        self.KillExec()
                        sys.stdout.write('\n')
                        sys.stdout.write(
                            f'{SUBell}Cannot communicate with the Code Generator.\n'
                        )
            elif self.ErrFileOpen and self.CallEditor:
                self.rt.PCReWrite(self.rt.PCText, 'For Editor')
                Msg = 'Errors in ' + alfa8(self.ProgName)
                if len(Msg) < 95:
                    Msg = Msg + ' ' * (95 - len(Msg))
                Ok = self.rt.PCPutLine(Msg)
                if Ok:
                    Ok = self.rt.PCPutLine(self.ErrFName)
                    if Ok:
                        Ok = self.rt.PCPutLine('* 1 1 1 1')
                if not self.rt.PCClose(False, 'For Editor'):
                    Ok = False
                if Ok:
                    self.rt.PCSetRunCmd(self.Ecmd)
                else:
                    self.KillExec()
                    sys.stdout.write(
                        f'{SUBell}Unable to set up communication to the Editor.\n'
                    )

        if self.CodeOpened:
            if self.ByteNo > 0 and self.Errors == 0:
                BlocksUsed = (self.ByteNo - 1) // 512 + 1
                if (
                    self.rt.block_write(self.ICodeFile, self.Buff, BlocksUsed, self.BlockNo)
                    != BlocksUsed
                ):
                    try:
                        self.FatalOutputError()
                    except AbortCompilation:
                        if self.ErrIndex != 0:
                            try:
                                self.LinePrinted = True
                                self.EolSource = True
                                self.InbufP = 0
                                self.Inbuf[0] = 32
                                self.InbufLastValidByte = 1
                                self.NextCh()
                            except AbortCompilation:
                                pass
            if self.Errors == 0:
                self.rt.close_untyped(self.ICodeFile, LisaCloseOpt.LOCK)
            else:
                self.rt.close_untyped(self.ICodeFile, LisaCloseOpt.PURGE)
            self.CodeOpened = False

        Summarize()

        if not self.Aborted:
            ChainToEdOrGen()

        if self.ListOpen:
            self.rt.CloseF(self.ListingFCBP, IOCloseKind.IOLock)

        if self.MsgFileOpen:
            self.rt.close_untyped(self.MsgFile)

        if self.ErrFileOpen:
            self.rt.close_text(self.ErrFile, LisaCloseOpt.LOCK)
            self.ErrFileOpen = False

        for i in range(self.TopOfOpenFileStack, 0, -1):
            self.rt.close_untyped(self.OpenFileStack[i].SrcFile)

        if self.DebugOpen:
            if self.DbgIdx > 0:
                for i in range(self.DbgIdx, 512):
                    self.DbgBuf[i] = 0
                if self.rt.block_write(self.DebugFile, self.DbgBuf, 1, self.DbgBlkNum) != 1:
                    self.Error(420)
            if self.Errors == 0:
                self.rt.close_untyped(self.DebugFile, LisaCloseOpt.LOCK)
            else:
                self.rt.close_untyped(self.DebugFile, LisaCloseOpt.PURGE)
            self.DebugOpen = False

        if self.DebugDebug:
            self.rt.close_text(self.Debugging, LisaCloseOpt.LOCK)
            self.DebugDebug = False

        self.rt.EndIO()
        self.rt.SUDone()

    def CallProg(self) -> None:
        """Prime the scanner, invoke `Prog` (if swapping) or `LoadConst` (to preload segments), and check for `EOFSY`."""
        self.Scan()
        if self.SwapFlag:
            self.Prog()
        else:
            self.LoadConst()
        if self.Token != Symbol.EOFSY:
            self.Error(17)
