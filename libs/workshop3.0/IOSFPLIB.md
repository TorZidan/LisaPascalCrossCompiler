# `IOSFPLIB` (`IOSFPLIB.obj`) — IEEE-754 Floating-Point & SANE Math Library

[Back to Library Index](LIBRARIES.md)

Motorola MC68000 IEEE-754 floating-point runtime (`FPLib`) and Standard Apple Numerics Environment (`MathLib`) elementary, transcendental, financial, and binary-decimal conversion routines.

- **Object file**: `libs/workshop3.0/IOSFPLIB.obj` (Intrinsic library)
- **Contents**: 2 units, 122 top-level procedures/functions

## Importing and Linking

```pascal
USES FPLib, MathLib;
```

```sh
pascal/lpc.py --link=IOSPASLIB,IOSFPLIB MYPROG
```

## Units in This Library

| Unit | 8-Char Symbol | `USES` Dependencies | Routines | Summary |
|---|---|---|---|---|
| [`FPLib`](#unit-fplib) | `FPLIB` | — | 91 | Implements the Standard Apple Numeric Environment (SANE) floating-point library for the Lisa, providing IEEE-754 80-bit `Extended` arithmetic, conversions among `Single`, `Double`, 64-bit `Comp`, integers, `Decimal` records, and strings, rounding/exception/halt environment control, and elementary transcendental and financial functions. |
| [`MathLib`](#unit-mathlib) | `MATHLIB` | `FPLib` | 31 | Extends `FPLib` with higher-level mathematical, financial, and numerical-analysis routines, including inverse and hyperbolic trigonometric functions, polar magnitude/angle helpers, 30-digit correctly rounded binary-decimal conversions, free-form ASCII formatting, stable sorting, NPV/IRR analysis, matrix multiplication, QR linear/least-squares solvers, and scalar root finding. |

---

## Unit FPLib

Implements the Standard Apple Numeric Environment (SANE) floating-point library for the Lisa, providing IEEE-754 80-bit `Extended` arithmetic, conversions among `Single`, `Double`, 64-bit `Comp`, integers, `Decimal` records, and strings, rounding/exception/halt environment control, and elementary transcendental and financial functions.

- **Import**: `USES FPLib;`
- **Unit kind**: `INTRINSIC` (`FPLIB`)

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `AddS` | `procedure AddS(x: Single; var y: Extended);` | Adds 32-bit IEEE-754 `Single` value `x` to 80-bit `Extended` accumulator `y` in place (`y := y + x`). |
| `AddD` | `procedure AddD(x: Double; var y: Extended);` | Adds 64-bit IEEE-754 `Double` value `x` to 80-bit `Extended` accumulator `y` in place (`y := y + x`). |
| `AddC` | `procedure AddC(x: Comp; var y: Extended);` | Adds 64-bit SANE `Comp` integral value `x` to 80-bit `Extended` accumulator `y` in place (`y := y + x`). |
| `AddX` | `procedure AddX(x: Extended; var y: Extended);` | Adds 80-bit IEEE-754 `Extended` value `x` to `Extended` accumulator `y` in place (`y := y + x`). |
| `SubS` | `procedure SubS(x: Single; var y: Extended);` | Subtracts 32-bit IEEE-754 `Single` value `x` from 80-bit `Extended` accumulator `y` in place (`y := y - x`). |
| `SubD` | `procedure SubD(x: Double; var y: Extended);` | Subtracts 64-bit IEEE-754 `Double` value `x` from 80-bit `Extended` accumulator `y` in place (`y := y - x`). |
| `SubC` | `procedure SubC(x: Comp; var y: Extended);` | Subtracts 64-bit SANE `Comp` integral value `x` from 80-bit `Extended` accumulator `y` in place (`y := y - x`). |
| `SubX` | `procedure SubX(x: Extended; var y: Extended);` | Subtracts 80-bit IEEE-754 `Extended` value `x` from `Extended` accumulator `y` in place (`y := y - x`). |
| `MulS` | `procedure MulS(x: Single; var y: Extended);` | Multiplies 80-bit `Extended` accumulator `y` by 32-bit IEEE-754 `Single` value `x` in place (`y := y * x`). |
| `MulD` | `procedure MulD(x: Double; var y: Extended);` | Multiplies 80-bit `Extended` accumulator `y` by 64-bit IEEE-754 `Double` value `x` in place (`y := y * x`). |
| `MulC` | `procedure MulC(x: Comp; var y: Extended);` | Multiplies 80-bit `Extended` accumulator `y` by 64-bit SANE `Comp` value `x` in place (`y := y * x`). |
| `MulX` | `procedure MulX(x: Extended; var y: Extended);` | Multiplies 80-bit IEEE-754 `Extended` accumulator `y` by `Extended` value `x` in place (`y := y * x`). |
| `DivS` | `procedure DivS(x: Single; var y: Extended);` | Divides 80-bit `Extended` accumulator `y` by 32-bit IEEE-754 `Single` divisor `x` in place (`y := y / x`). |
| `DivD` | `procedure DivD(x: Double; var y: Extended);` | Divides 80-bit `Extended` accumulator `y` by 64-bit IEEE-754 `Double` divisor `x` in place (`y := y / x`). |
| `DivC` | `procedure DivC(x: Comp; var y: Extended);` | Divides 80-bit `Extended` accumulator `y` by 64-bit SANE `Comp` divisor `x` in place (`y := y / x`). |
| `DivX` | `procedure DivX(x: Extended; var y: Extended);` | Divides 80-bit IEEE-754 `Extended` accumulator `y` by `Extended` divisor `x` in place (`y := y / x`). |
| `CmpX` | `function CmpX(x: Extended; r: RelOp; y: Extended): boolean;` | Evaluates IEEE-754 relational predicate `x r y` (`GT`, `LT`, `GL`, `EQ`, `GE`, `LE`, `GEL`, `UNORD`) on `Extended` operands `x` and `y` and returns `TRUE` if satisfied. |
| `RelX` | `function RelX(x, y: Extended): RelOp;` | Compares 80-bit `Extended` operands `x` and `y` and returns their IEEE-754 ordering relation (`GT`, `LT`, `EQ`, or `UNORD`). |
| `I2X` | `procedure I2X(x: integer; var y: Extended);` | Converts 16-bit signed `integer` `x` to an 80-bit IEEE-754 `Extended` value in `y`. |
| `S2X` | `procedure S2X(x: Single; var y: Extended);` | Converts 32-bit IEEE-754 `Single` value `x` to an 80-bit `Extended` value in `y`. |
| `D2X` | `procedure D2X(x: Double; var y: Extended);` | Converts 64-bit IEEE-754 `Double` value `x` to an 80-bit `Extended` value in `y`. |
| `C2X` | `procedure C2X(x: Comp; var y: Extended);` | Converts 64-bit SANE `Comp` value `x` (treating `-2^63` as `NaN`) to an 80-bit `Extended` value in `y`. |
| `X2X` | `procedure X2X(x: Extended; var y: Extended);` | Copies and normalizes/rounds 80-bit `Extended` value `x` into `Extended` destination `y` under the current SANE environment. |
| `X2I` | `procedure X2I(x: Extended; var y: integer);` | Rounds 80-bit `Extended` value `x` according to the current SANE rounding direction and stores the 16-bit signed `integer` result in `y`. |
| `X2S` | `procedure X2S(x: Extended; var y: Single);` | Rounds and converts 80-bit `Extended` value `x` to a 32-bit IEEE-754 `Single` value in `y`. |
| `X2D` | `procedure X2D(x: Extended; var y: Double);` | Rounds and converts 80-bit `Extended` value `x` to a 64-bit IEEE-754 `Double` value in `y`. |
| `X2C` | `procedure X2C(x: Extended; var y: Comp);` | Rounds and converts 80-bit `Extended` value `x` to a 64-bit SANE `Comp` integral value in `y` (producing `-2^63` `NaN` on invalid/overflow). |
| `L2X` | `procedure L2X(x: longint; var y: Extended);` | Converts 32-bit signed `longint` `x` to an 80-bit IEEE-754 `Extended` value in `y`. |
| `X2L` | `procedure X2L(x: Extended; var y: longint);` | Rounds 80-bit `Extended` value `x` according to the current SANE rounding direction and stores the 32-bit `longint` result in `y`. |
| `S2Dec` | `procedure S2Dec(f: DecForm; x: Single; var y: Decimal);` | Converts 32-bit `Single` value `x` into SANE unpacked `Decimal` record `y` formatted according to `DecForm` `f`. |
| `D2Dec` | `procedure D2Dec(f: DecForm; x: Double; var y: Decimal);` | Converts 64-bit `Double` value `x` into SANE unpacked `Decimal` record `y` formatted according to `DecForm` `f`. |
| `C2Dec` | `procedure C2Dec(f: DecForm; x: Comp; var y: Decimal);` | Converts 64-bit `Comp` value `x` into SANE unpacked `Decimal` record `y` formatted according to `DecForm` `f`. |
| `X2Dec` | `procedure X2Dec(f: DecForm; x: Extended; var y: Decimal);` | Converts 80-bit `Extended` value `x` into SANE unpacked `Decimal` record `y` formatted according to `DecForm` `f`. |
| `Dec2S` | `procedure Dec2S(x: Decimal; var y: Single);` | Converts SANE unpacked `Decimal` record `x` (`(-1)^sgn * 10^exp * sig`) to a rounded 32-bit IEEE-754 `Single` in `y`. |
| `Dec2D` | `procedure Dec2D(x: Decimal; var y: Double);` | Converts SANE unpacked `Decimal` record `x` (`(-1)^sgn * 10^exp * sig`) to a rounded 64-bit IEEE-754 `Double` in `y`. |
| `Dec2C` | `procedure Dec2C(x: Decimal; var y: Comp);` | Converts SANE unpacked `Decimal` record `x` (`(-1)^sgn * 10^exp * sig`) to a rounded 64-bit SANE `Comp` integer in `y`. |
| `Dec2X` | `procedure Dec2X(x: Decimal; var y: Extended);` | Converts SANE unpacked `Decimal` record `x` (`(-1)^sgn * 10^exp * sig`) to a rounded 80-bit IEEE-754 `Extended` value in `y`. |
| `Str2Dec` | `procedure Str2Dec(s: DecStr; var index: integer; var d: Decimal; var ValidPrefix: boolean);` | Scans numeric ASCII token from `s` starting at `s[index]` into `Decimal` record `d`, advancing `index` past the accepted characters and setting `ValidPrefix` if the scanned prefix could continue as a valid number. |
| `Dec2Str` | `procedure Dec2Str(f: DecForm; d: Decimal; var s: DecStr);` | Formats SANE `Decimal` record `d` into ASCII decimal string `s` according to `DecForm` `f` (`FLOATDECIMAL` or `FIXEDDECIMAL`). |
| `S2Str` | `procedure S2Str(f: DecForm; x: Single; var y: DecStr);` | Formats 32-bit IEEE-754 `Single` value `x` into ASCII decimal string `y` according to `DecForm` `f`. |
| `D2Str` | `procedure D2Str(f: DecForm; x: Double; var y: DecStr);` | Formats 64-bit IEEE-754 `Double` value `x` into ASCII decimal string `y` according to `DecForm` `f`. |
| `C2Str` | `procedure C2Str(f: DecForm; x: Comp; var y: DecStr);` | Formats 64-bit SANE `Comp` value `x` into ASCII decimal string `y` according to `DecForm` `f`. |
| `X2Str` | `procedure X2Str(f: DecForm; x: Extended; var y: DecStr);` | Formats 80-bit IEEE-754 `Extended` value `x` into ASCII decimal string `y` according to `DecForm` `f`. |
| `Str2S` | `procedure Str2S(x: DecStr; var y: Single);` | Parses ASCII numeric string `x` and converts it to a 32-bit IEEE-754 `Single` value in `y`. |
| `Str2D` | `procedure Str2D(x: DecStr; var y: Double);` | Parses ASCII numeric string `x` and converts it to a 64-bit IEEE-754 `Double` value in `y`. |
| `Str2C` | `procedure Str2C(x: DecStr; var y: Comp);` | Parses ASCII numeric string `x` and converts it to a 64-bit SANE `Comp` integral value in `y`. |
| `Str2X` | `procedure Str2X(x: DecStr; var y: Extended);` | Parses ASCII numeric string `x` and converts it to an 80-bit IEEE-754 `Extended` value in `y`. |
| `RemX` | `procedure RemX(x: Extended; var y: Extended; var quo: integer);` | Replaces `y` with the IEEE-754 remainder `y - x * n` (where `n` is the round-to-nearest-even integer quotient of `y / x`) and stores the signed low-order 7 bits of `n` (`-127..127`) in `quo`. |
| `SqrtX` | `procedure SqrtX(var x: Extended);` | Computes the correctly rounded IEEE-754 square root of 80-bit `Extended` value `x` in place (`x := sqrt(x)`). |
| `RintX` | `procedure RintX(var x: Extended);` | Rounds 80-bit `Extended` value `x` in place to an integral floating-point value according to the current SANE rounding direction. |
| `NegX` | `procedure NegX(var x: Extended);` | Flips the sign bit of 80-bit `Extended` value `x` in place (`x := -x`). |
| `AbsX` | `procedure AbsX(var x: Extended);` | Clears the sign bit of 80-bit `Extended` value `x` in place to produce its absolute value (`x := \|x\|`). |
| `CpySgnX` | `procedure CpySgnX(var x: Extended; y: Extended);` | Copies the sign bit of `Extended` value `y` onto `Extended` value `x` in place. |
| `NextS` | `procedure NextS(var x: Single; y: Single);` | Updates 32-bit `Single` `x` in place to the next representable `Single` value from `x` in the direction of `y`. |
| `NextD` | `procedure NextD(var x: Double; y: Double);` | Updates 64-bit `Double` `x` in place to the next representable `Double` value from `x` in the direction of `y`. |
| `NextX` | `procedure NextX(var x: Extended; y: Extended);` | Updates 80-bit `Extended` `x` in place to the next representable value from `x` in the direction of `y` under the active rounding precision. |
| `ClassS` | `function ClassS(x: Single; var sgn: integer): NumClass;` | Classifies 32-bit `Single` value `x`, storing its sign (`0` positive, `1` negative) in `sgn` and returning its `NumClass` (`SNAN`, `QNAN`, `INFINITE`, `ZERO`, `NORMAL`, `DENORMAL`). |
| `ClassD` | `function ClassD(x: Double; var sgn: integer): NumClass;` | Classifies 64-bit `Double` value `x`, storing its sign (`0` positive, `1` negative) in `sgn` and returning its `NumClass` (`SNAN`, `QNAN`, `INFINITE`, `ZERO`, `NORMAL`, `DENORMAL`). |
| `ClassC` | `function ClassC(x: Comp; var sgn: integer): NumClass;` | Classifies 64-bit SANE `Comp` value `x`, storing its sign (`0` positive, `1` negative) in `sgn` and returning its `NumClass` (`QNAN` for `-2^63`, `ZERO`, or `NORMAL`). |
| `ClassX` | `function ClassX(x: Extended; var sgn: integer): NumClass;` | Classifies 80-bit `Extended` value `x`, storing its sign (`0` positive, `1` negative) in `sgn` and returning its `NumClass` (`SNAN`, `QNAN`, `INFINITE`, `ZERO`, `NORMAL`, `DENORMAL`). |
| `ScalbX` | `procedure ScalbX(n: integer; var y: Extended);` | Scales 80-bit `Extended` value `y` in place by $2^n$ (`y := y * 2^n`) without intermediate rounding loss. |
| `LogbX` | `procedure LogbX(var x: Extended);` | Replaces 80-bit `Extended` value `x` in place with its unbiased IEEE-754 binary exponent as an integral `Extended` value. |
| `SetRnd` | `procedure SetRnd(r: RoundDir);` | Sets the active SANE IEEE-754 rounding direction (`TONEAREST`, `UPWARD`, `DOWNWARD`, or `TOWARDZERO`) to `r`. |
| `SetEnv` | `procedure SetEnv(e: Environ);` | Restores the entire SANE floating-point environment word (rounding direction, rounding precision, exception flags, and halt enables) from `e`. |
| `GetRnd` | `function GetRnd: RoundDir;` | Returns the currently active SANE IEEE-754 rounding direction (`RoundDir`). |
| `GetEnv` | `procedure GetEnv(var e: Environ);` | Saves the current SANE floating-point environment word (rounding, precision, exception flags, and halt masks) into `e`. |
| `TestXcp` | `function TestXcp(x: Exception): boolean;` | Returns `TRUE` if sticky SANE floating-point exception flag `x` (`INVALID`, `UNDERFLOW`, `OVERFLOW`, `DIVBYZERO`, `INEXACT`) is currently set. |
| `SetXcp` | `procedure SetXcp(x: Exception; OnOff: boolean);` | Sets (`OnOff = TRUE`, triggering a halt if enabled) or clears (`OnOff = FALSE`) sticky SANE floating-point exception flag `x`. |
| `TestHlt` | `function TestHlt(x: Exception): boolean;` | Returns `TRUE` if SANE trap/halt on floating-point exception `x` is currently enabled. |
| `SetHlt` | `procedure SetHlt(x: Exception; OnOff: boolean);` | Enables (`OnOff = TRUE`) or disables (`OnOff = FALSE`) SANE trap/halt generation when floating-point exception `x` occurs. |
| `ProcEntry` | `procedure ProcEntry(var e: Environ);` | Saves the caller's SANE floating-point environment into `e` and resets the active environment to default IEEE-754 modes with cleared exceptions and halts disabled. |
| `ProcExit` | `procedure ProcExit(e: Environ);` | Restores caller SANE environment `e` while OR-ing any exceptions raised during the procedure into the restored sticky flags (and invoking any newly triggered halts). |
| `Log2X` | `procedure Log2X(var x: Extended);` | Computes the base-2 logarithm $\log_2(x)$ of 80-bit `Extended` value `x` in place. |
| `LnX` | `procedure LnX(var x: Extended);` | Computes the natural logarithm $\ln(x)$ of 80-bit `Extended` value `x` in place. |
| `Ln1X` | `procedure Ln1X(var x: Extended);` | Computes $\ln(1 + x)$ accurately for small `x` on 80-bit `Extended` value `x` in place. |
| `Exp2X` | `procedure Exp2X(var x: Extended);` | Computes the base-2 exponential $2^x$ of 80-bit `Extended` value `x` in place. |
| `ExpX` | `procedure ExpX(var x: Extended);` | Computes the natural exponential $e^x$ of 80-bit `Extended` value `x` in place. |
| `Exp1X` | `procedure Exp1X(var x: Extended);` | Computes $e^x - 1$ accurately for small `x` on 80-bit `Extended` value `x` in place. |
| `XpwrI` | `procedure XpwrI(i: integer; var x: Extended);` | Raises 80-bit `Extended` value `x` to 16-bit signed integer power `i` in place ($x := x^i$). |
| `XpwrY` | `procedure XpwrY(y: Extended; var x: Extended);` | Raises 80-bit `Extended` base `x` to `Extended` exponent `y` in place ($x := x^y$). |
| `Compound` | `procedure Compound(r, n: Extended; var x: Extended);` | Computes the compound-interest factor $(1 + r)^n$ from `Extended` rate `r` and periods `n`, storing the result in `x`. |
| `Annuity` | `procedure Annuity(r, n: Extended; var x: Extended);` | Computes the present-value annuity factor $(1 - (1 + r)^{-n}) / r$ from `Extended` rate `r` and periods `n`, storing the result in `x`. |
| `AtanX` | `procedure AtanX(var x: Extended);` | Computes the principal arctangent $\arctan(x)$ in radians of 80-bit `Extended` value `x` in place. |
| `SinX` | `procedure SinX(var x: Extended);` | Computes the sine $\sin(x)$ of 80-bit `Extended` angle `x` (in radians) in place. |
| `CosX` | `procedure CosX(var x: Extended);` | Computes the cosine $\cos(x)$ of 80-bit `Extended` angle `x` (in radians) in place. |
| `TanX` | `procedure TanX(var x: Extended);` | Computes the tangent $\tan(x)$ of 80-bit `Extended` angle `x` (in radians) in place. |
| `RandomX` | `procedure RandomX(var x: Extended);` | Advances pseudorandom integer seed `x` (`1 <= x <= 2^31 - 2` as `Extended`) in place via multiplicative congruential generator $x := (7^5 \cdot x) \bmod (2^{31} - 1)$. |
| `GetHltAddress` | `function GetHltAddress: longint;` | Returns the 32-bit entry address of the currently installed SANE floating-point halt handler procedure. |
| `SetHltAddress` | `procedure SetHltAddress(HltAddress: longint);` | Sets the 32-bit entry address of the SANE floating-point halt handler procedure to `HltAddress`. |
| `InitFPLib` | `procedure InitFPLib;` | Initializes the SANE floating-point control word (`FPcb := 0`) and clears the halt handler address to `NIL`. |
| `SANE_Environ` | `function SANE_Environ: longint;` | Returns the 32-bit memory address (`ord4(@FPcb)`) of the internal SANE floating-point environment word. |

---

## Unit MathLib

Extends `FPLib` with higher-level mathematical, financial, and numerical-analysis routines, including inverse and hyperbolic trigonometric functions, polar magnitude/angle helpers, 30-digit correctly rounded binary-decimal conversions, free-form ASCII formatting, stable sorting, NPV/IRR analysis, matrix multiplication, QR linear/least-squares solvers, and scalar root finding.

- **Import**: `USES MathLib;`
- **Unit kind**: `INTRINSIC` (`MATHLIB`)
- **Interface dependencies**: `FPLib`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `ASinX` | `procedure ASinX(var x: Extended);` | Computes the principal arcsine $\arcsin(x)$ in radians of 80-bit `Extended` value `x` in place. |
| `ACosX` | `procedure ACosX(var x: Extended);` | Computes the principal arccosine $\arccos(x)$ in radians of 80-bit `Extended` value `x` in place. |
| `SinhX` | `procedure SinhX(var x: Extended);` | Computes the hyperbolic sine $\sinh(x)$ of 80-bit `Extended` value `x` in place. |
| `CoshX` | `procedure CoshX(var x: Extended);` | Computes the hyperbolic cosine $\cosh(x)$ of 80-bit `Extended` value `x` in place. |
| `TanhX` | `procedure TanhX(var x: Extended);` | Computes the hyperbolic tangent $\tanh(x)$ of 80-bit `Extended` value `x` in place. |
| `Abs2X` | `procedure Abs2X(x, y: Extended; var z: Extended);` | Computes the overflow/underflow-scaled Euclidean magnitude $\sqrt{x^2 + y^2}$ (`\|x + iy\|`) of `Extended` values `x` and `y` into `z`. |
| `ATan2X` | `procedure ATan2X(x, y: Extended; var z: Extended);` | Computes the four-quadrant arctangent $\operatorname{atan2}(x, y)$ (`atan(x / y)` in $[-\pi, \pi]$ using the signs of `x` and `y`) into `z`. |
| `NextRandom` | `function NextRandom(lastrandom: longint): longint;` | Computes and returns the next pseudorandom `longint` in `1..RandModulus - 1` (`2^31 - 2`) from `lastrandom`. |
| `ClearXcps` | `procedure ClearXcps;` | Clears all sticky SANE floating-point exception flags in the current environment. |
| `ClearHlts` | `procedure ClearHlts;` | Disables all SANE floating-point exception halt/trap flags in the current environment. |
| `SetPrecision` | `procedure SetPrecision(p: RoundPrecision);` | Sets the SANE extended rounding precision mode (`ExtPrecision`, `DblPrecision`, or `RealPrecision`) to `p`. |
| `GetPrecision` | `function GetPrecision: RoundPrecision;` | Returns the currently active SANE extended rounding precision mode (`RoundPrecision`). |
| `Math_Sort` | `procedure Math_Sort(first, last: integer; function sorted(i, j: integer): boolean; procedure swap(i, j: integer) var error: boolean);` | Stably sorts records `first..last` using caller-supplied comparator `sorted(i, j)` and swap callback `swap(i, j)`, setting `error` if temporary heap allocation fails. |
| `SignOfX` | `function SignOfX(x: Extended): boolean;` | Returns `TRUE` if 80-bit `Extended` value `x` has its negative sign bit set. |
| `FP_New` | `function FP_New(n: longint): longint;` | Attempts to allocate `n` bytes on the Pascal heap and returns the allocated block's 32-bit address, or `ord(nil)` (`0`) if insufficient space is available. |
| `FP_Size` | `procedure FP_Size(x: Extended; var sgn: integer; var class: NumClass; var size: FP_Type);` | Determines the sign bit `sgn`, `NumClass` `class`, and smallest numeric storage type `size` (`FP_Type`, from `TFP_byte` up to `TFP_Extended`) that can represent `x` without loss. |
| `FP_Free_Ascii` | `procedure FP_Free_Ascii(x: Extended; width: integer; form: Free_Format; var s: Decstr);` | Formats 80-bit `Extended` value `x` into free-form ASCII string `s` of at most `width` characters according to `Free_Format` `form` (leaving `Length(s) > width` if constraints cannot be met). |
| `Fin_Npv` | `procedure Fin_Npv(first, last, net: integer; rate: Extended; var Npv: Extended; procedure payment(i: integer; var pmt: Extended));` | Computes the net value `Npv` at period `net` of cash-flow payments over periods `first..last` supplied by callback `payment` at periodic interest `rate`. |
| `Fin_Return` | `procedure Fin_Return(first, last: integer; negperiod, posperiod: integer; negrate, posrate: Extended; var ncs: integer; var ret: Extended; procedure payment(i: integer; var pmt: Extended));` | Computes the internal or external rate of return `ret` (and sign-change status `ncs`) for cash flows `first..last` from `payment`, optionally discounting negative/positive flows to `negperiod`/`posperiod` at `negrate`/`posrate`. |
| `Mat_Mult` | `procedure Mat_Mult(n, p, m: integer; overlap: boolean; var error: boolean; procedure afetch(i, j: integer; var aij: Extended) procedure xfetch(i, j: integer; var xij: Extended) procedure bstore(i, j: integer; bij: Extended));` | Multiplies an $n \times p$ matrix $A$ (`afetch`) by a $p \times m$ matrix $X$ (`xfetch`) into $n \times m$ matrix $B$ (`bstore`), buffering on the heap when `overlap` is `TRUE` and setting `error` on out-of-memory. |
| `QR_Factor` | `procedure QR_Factor(n, p: integer; pivot: boolean; var QR: P_QR_Record; procedure afetch(i, j: integer; var aij: Extended));` | Computes the Householder QR factorization (with optional column `pivot`) of $n \times p$ matrix $A$ (`afetch`) and stores a heap handle to the decomposed matrix in `QR` (or `0` if heap space is exhausted). |
| `QR_Condition` | `procedure QR_Condition(QR: P_QR_Record; var cond: Extended);` | Estimates the condition number `cond` of the matrix whose QR factorization is stored in `QR`. |
| `QR_Determinant` | `procedure QR_Determinant(QR: P_QR_Record; var det: Extended);` | Computes the determinant `det` of the square matrix whose QR factorization is stored in `QR`. |
| `QR_Solve` | `procedure QR_Solve(m: integer; QR: P_QR_Record; var error: boolean; procedure bfetch(i, j: integer; var bij: Extended); procedure xstore(i, j: integer; xij: Extended));` | Solves the linear system or linear least-squares problem $A X \approx B$ for $m$ right-hand-side columns (`bfetch` -> `xstore`) using QR factorization `QR`, setting `error` on insufficient heap space. |
| `QR_Residual` | `procedure QR_Residual(n, p: integer; m: integer; procedure afetch(i, j: integer; var aij: Extended); procedure bfetch(i, j: integer; var bij: Extended); procedure xfetch(i, j: integer; var xij: Extended); procedure rstore(i, j: integer; rij: Extended));` | Computes the $n \times m$ residual matrix $R := B - A X$ (`rstore`) for $n \times p$ matrix $A$ (`afetch`), right-hand side $B$ (`bfetch`), and approximate solution $X$ (`xfetch`). |
| `QR_Improve` | `procedure QR_Improve(m: integer; QR: P_QR_Record; var error: boolean; procedure afetch(i, j: integer; var aij: Extended); procedure bfetch(i, j: integer; var bij: Extended); procedure xfetch(i, j: integer; var xij: Extended); procedure xstore(i, j: integer; xij: Extended));` | Performs one iterative-refinement step on $p \times m$ solution $X$ (`xfetch` -> `xstore`) of $A X = B$ (`afetch`, `bfetch`) using QR factorization `QR`, setting `error` if heap allocation fails. |
| `QR_TranSolve` | `procedure QR_TranSolve(m: integer; QR: P_QR_Record; var error: boolean; procedure bfetch(i, j: integer; var bij: Extended); procedure xstore(i, j: integer; xij: Extended));` | Solves the normal-equations system $(A^T A) X = B$ for $m$ right-hand-side columns (`bfetch` -> `xstore`) using QR factorization `QR` of $A$, setting `error` on insufficient heap space. |
| `QR_TranDeterminant` | `procedure QR_TranDeterminant(QR: P_QR_Record; var det: Extended);` | Computes the determinant `det` of $A^T A$ from the QR factorization `QR` of matrix $A$. |
| `X2LDec` | `procedure X2LDec(f: DecForm; x: Extended; var y: LongDecimal);` | Converts 80-bit `Extended` value `x` into a 30-digit `LongDecimal` record `y`, correctly rounded according to `DecForm` `f`. |
| `LDec2X` | `procedure LDec2X(prec: RoundPrecision; x: LongDecimal; var y: Extended);` | Converts 30-digit `LongDecimal` record `x` into an 80-bit `Extended` value `y`, correctly rounded to `RoundPrecision` `prec`. |
| `Math_Solve` | `procedure Math_Solve(est1, est2: Extended; var result: Extended; procedure f(x: Extended; var fx: Extended));` | Finds a root or sign-change/minimum-magnitude point `result` of scalar callback function `f(x, fx)` starting from initial estimates `est1` and `est2`. |
