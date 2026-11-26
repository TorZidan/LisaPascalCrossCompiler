# `IOSFPLIB` (`IOSFPLIB.obj`) — Workshop 2.0 IEEE-754 Floating-Point Library (A52)

[Back to Library Index](LIBRARIES.md)

Pre-SANE MC68000 IEEE-754 floating-point library (`FPLib` version A52) providing simulated floating-point registers, 32-bit `Real`, 64-bit `fp_double`, and 80-bit `fp_extended` arithmetic, binary-ASCII conversions, rounding/trap modes, and transcendental functions.

- **Object file**: `libs/workshop2.0/IOSFPLIB.obj` (Intrinsic library)
- **Contents**: 1 unit, 203 procedures/functions

## Importing and Linking

```pascal
USES FPLib;
```

```sh
LISA_BOOT=libs/workshop2.0 pascal/lpc.py --2.0 --link=IOSPASLIB,IOSFPLIB MYPROG
```

## Units in This Library

| Unit | 8-Char Symbol | `USES` Dependencies | Routines | Summary |
|---|---|---|---|---|
| [`FPLib`](#unit-fplib) | `FPLIB` | — | 203 | Provides the Workshop 1.0/2.0 floating-point runtime library (version A52), implementing proposed IEEE-754 arithmetic across 32-bit Single (real), 64-bit Double (fp_double), and 80-bit Extended (fp_extended) formats with simulated registers FP0 and FP1 in FPCB_. Includes binary-ASCII conversions, rounding/closure/precision mode and exception trap controls, 64-bit integer helpers, and elementary transcendental and financial functions. |

---

## Unit FPLib

Provides the Workshop 1.0/2.0 floating-point runtime library (version A52), implementing proposed IEEE-754 arithmetic across 32-bit Single (real), 64-bit Double (fp_double), and 80-bit Extended (fp_extended) formats with simulated registers FP0 and FP1 in FPCB_. Includes binary-ASCII conversions, rounding/closure/precision mode and exception trap controls, 64-bit integer helpers, and elementary transcendental and financial functions.

- **Import**: `USES FPLib;`
- **Unit kind**: `INTRINSIC` (`FPLIB`)

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `f32_minus` | `function f32_minus(x: real): boolean;` | Returns TRUE if the 32-bit single-precision real value x has its negative sign bit set, or FALSE if positive. |
| `f32_integral` | `function f32_integral(x: real): boolean;` | Returns TRUE if the 32-bit single-precision real value x is zero or an exact finite integer, or FALSE if fractional, infinite, or NaN. |
| `f32_fraction` | `function f32_fraction(x: real): real;` | Returns the fractional part of the 32-bit single-precision real value x (x minus x truncated toward zero), returning zero for integers or infinities. |
| `f32_ilogb` | `function f32_ilogb(x: real): integer;` | Returns the unbiased binary exponent of the 32-bit single-precision real value x, signaling invop if x is zero, infinite, or NaN. |
| `f32_scale` | `function f32_scale(x: real; i: integer): real;` | Scales the 32-bit single-precision real value x by 2^i (x * 2^i), preserving zeros, infinities, and quiet NaNs. |
| `f32_kind` | `function f32_kind(x: real): fp_kindtype;` | Classifies the 32-bit single-precision real value x as zero, norml (including denormalized values), inf, or NaN. |
| `f32_fpcb` | `function f32_fpcb: p_fpcb_type;` | Returns a pointer (@FPCB_) to the global floating-point control block from the 32-bit f32sub segment. |
| `fpneg` | `procedure fpneg;` | Negates the value in simulated floating-point register FP0 (FP0 := -FP0). |
| `fpabs` | `procedure fpabs;` | Replaces the value in simulated floating-point register FP0 with its absolute value (FP0 := abs(FP0)). |
| `fpint` | `procedure fpint;` | Rounds the value in simulated floating-point register FP0 to an integral value according to the current rounding mode. |
| `fpsqrt` | `procedure fpsqrt;` | Replaces the value in simulated floating-point register FP0 with its IEEE square root (FP0 := sqrt(FP0)). |
| `fpadd` | `procedure fpadd;` | Adds simulated floating-point register FP1 to FP0 and stores the sum in FP0 (FP0 := FP0 + FP1). |
| `fpsub` | `procedure fpsub;` | Subtracts simulated floating-point register FP1 from FP0 and stores the difference in FP0 (FP0 := FP0 - FP1). |
| `fpmul` | `procedure fpmul;` | Multiplies simulated floating-point register FP0 by FP1 and stores the product in FP0 (FP0 := FP0 * FP1). |
| `fpdiv` | `procedure fpdiv;` | Divides simulated floating-point register FP0 by FP1 and stores the quotient in FP0 (FP0 := FP0 / FP1). |
| `fprem` | `procedure fprem;` | Computes the IEEE remainder of FP0 divided by FP1 and stores the result in FP0 (FP0 := FP0 rem FP1). |
| `fpcom` | `function fpcom: fp_cc;` | Compares simulated floating-point register FP0 against FP1 and returns the condition code (equal, lesser, greater, or unord). |
| `fpints` | `function fpints(x: real): real;` | Rounds the 32-bit single-precision real value x to an integral real value according to the current rounding mode. |
| `fpsqrts` | `function fpsqrts(x: real): real;` | Computes and returns the IEEE square root of the 32-bit single-precision real value x. |
| `fpnegd` | `procedure fpnegd(var x, z: fp_double);` | Negates the 64-bit fp_double value x and stores -x in z. |
| `fpabsd` | `procedure fpabsd(var x, z: fp_double);` | Computes the absolute value of the 64-bit fp_double value x and stores abs(x) in z. |
| `fpintd` | `procedure fpintd(var x, z: fp_double);` | Rounds the 64-bit fp_double value x to an integral floating-point value according to the current rounding mode and stores it in z. |
| `fpsqrtd` | `procedure fpsqrtd(var x, z: fp_double);` | Computes the IEEE square root of the 64-bit fp_double value x and stores sqrt(x) in z. |
| `fpnegx` | `procedure fpnegx(var x, z: fp_extended);` | Negates the 80-bit fp_extended value x and stores -x in z. |
| `fpabsx` | `procedure fpabsx(var x, z: fp_extended);` | Computes the absolute value of the 80-bit fp_extended value x and stores abs(x) in z. |
| `fpintx` | `procedure fpintx(var x, z: fp_extended);` | Rounds the 80-bit fp_extended value x to an integral floating-point value according to the current rounding mode and stores it in z. |
| `fpsqrtx` | `procedure fpsqrtx(var x, z: fp_extended);` | Computes the IEEE square root of the 80-bit fp_extended value x and stores sqrt(x) in z. |
| `fpadds` | `function fpadds(x, y: real): real;` | Adds the 32-bit single-precision real values x and y and returns x + y. |
| `fpsubs` | `function fpsubs(x, y: real): real;` | Subtracts the 32-bit single-precision real value y from x and returns x - y. |
| `fpmuls` | `function fpmuls(x, y: real): real;` | Multiplies the 32-bit single-precision real values x and y and returns x * y. |
| `fpdivs` | `function fpdivs(x, y: real): real;` | Divides the 32-bit single-precision real value x by y and returns x / y. |
| `fprems` | `function fprems(x, y: real): real;` | Computes and returns the IEEE remainder x rem y for 32-bit single-precision real operands x and y. |
| `fpcoms` | `function fpcoms(x, y: real): fp_cc;` | Compares 32-bit single-precision real values x and y and returns the condition code (equal, lesser, greater, or unord). |
| `fpaddd` | `procedure fpaddd(var x, y, z: fp_double);` | Adds 64-bit fp_double values x and y and stores x + y in z. |
| `fpsubd` | `procedure fpsubd(var x, y, z: fp_double);` | Subtracts 64-bit fp_double value y from x and stores x - y in z. |
| `fpmuld` | `procedure fpmuld(var x, y, z: fp_double);` | Multiplies 64-bit fp_double values x and y and stores x * y in z. |
| `fpdivd` | `procedure fpdivd(var x, y, z: fp_double);` | Divides 64-bit fp_double value x by y and stores x / y in z. |
| `fpremd` | `procedure fpremd(var x, y, z: fp_double);` | Computes the IEEE remainder of 64-bit fp_double value x divided by y and stores x rem y in z. |
| `fpcomd` | `function fpcomd(var x, y: fp_double): fp_cc;` | Compares 64-bit fp_double values x and y and returns the condition code (equal, lesser, greater, or unord). |
| `fpaddx` | `procedure fpaddx(var x, y, z: fp_extended);` | Adds 80-bit fp_extended values x and y and stores x + y in z. |
| `fpsubx` | `procedure fpsubx(var x, y, z: fp_extended);` | Subtracts 80-bit fp_extended value y from x and stores x - y in z. |
| `fpmulx` | `procedure fpmulx(var x, y, z: fp_extended);` | Multiplies 80-bit fp_extended values x and y and stores x * y in z. |
| `fpdivx` | `procedure fpdivx(var x, y, z: fp_extended);` | Divides 80-bit fp_extended value x by y and stores x / y in z. |
| `fpremx` | `procedure fpremx(var x, y, z: fp_extended);` | Computes the IEEE remainder of 80-bit fp_extended value x divided by y and stores x rem y in z. |
| `fpcomx` | `function fpcomx(var x, y: fp_extended): fp_cc;` | Compares 80-bit fp_extended values x and y and returns the condition code (equal, lesser, greater, or unord). |
| `wmovefp` | `procedure wmovefp(x: integer);` | Converts the 16-bit integer value x to internal floating-point format and loads it into register FP0. |
| `lmovefp` | `procedure lmovefp(x: longint);` | Converts the 32-bit longint value x to internal floating-point format and loads it into register FP0. |
| `smovefp` | `procedure smovefp(x: real);` | Converts the 32-bit single-precision real value x to internal floating-point format and loads it into register FP0. |
| `dmovefp` | `procedure dmovefp(var x: fp_double);` | Converts the 64-bit fp_double value x to internal floating-point format and loads it into register FP0. |
| `xmovefp` | `procedure xmovefp(var x: fp_extended);` | Unpacks the 80-bit fp_extended value x into internal floating-point format and loads it into register FP0. |
| `wmovefp1` | `procedure wmovefp1(x: integer);` | Converts the 16-bit integer value x to internal floating-point format and loads it into register FP1. |
| `lmovefp1` | `procedure lmovefp1(x: longint);` | Converts the 32-bit longint value x to internal floating-point format and loads it into register FP1. |
| `smovefp1` | `procedure smovefp1(x: real);` | Converts the 32-bit single-precision real value x to internal floating-point format and loads it into register FP1. |
| `dmovefp1` | `procedure dmovefp1(var x: fp_double);` | Converts the 64-bit fp_double value x to internal floating-point format and loads it into register FP1. |
| `xmovefp1` | `procedure xmovefp1(var x: fp_extended);` | Unpacks the 80-bit fp_extended value x into internal floating-point format and loads it into register FP1. |
| `fpmovew` | `function fpmovew: integer;` | Rounds and converts the value in simulated floating-point register FP0 to a 16-bit integer. |
| `fpmovel` | `function fpmovel: longint;` | Rounds and converts the value in simulated floating-point register FP0 to a 32-bit longint. |
| `fpmoves` | `function fpmoves: real;` | Rounds and converts the value in simulated floating-point register FP0 to a 32-bit single-precision real. |
| `fpmoved` | `procedure fpmoved(var z: fp_double);` | Rounds and converts the value in simulated floating-point register FP0 to a 64-bit fp_double stored in z. |
| `fpmovex` | `procedure fpmovex(var z: fp_extended);` | Packs the value in simulated floating-point register FP0 into an 80-bit fp_extended value stored in z. |
| `xmovew` | `function xmovew(var x: fp_extended): integer;` | Rounds and converts the 80-bit fp_extended value x to a 16-bit integer. |
| `dmovew` | `function dmovew(var x: fp_double): integer;` | Rounds and converts the 64-bit fp_double value x to a 16-bit integer. |
| `xmovel` | `function xmovel(var x: fp_extended): longint;` | Rounds and converts the 80-bit fp_extended value x to a 32-bit longint. |
| `dmovel` | `function dmovel(var x: fp_double): longint;` | Rounds and converts the 64-bit fp_double value x to a 32-bit longint. |
| `xmoves` | `function xmoves(var x: fp_extended): real;` | Rounds and converts the 80-bit fp_extended value x to a 32-bit single-precision real. |
| `dmoves` | `function dmoves(var x: fp_double): real;` | Rounds and converts the 64-bit fp_double value x to a 32-bit single-precision real. |
| `wmoved` | `procedure wmoved(x: integer; var z: fp_double);` | Converts the 16-bit integer value x to a 64-bit fp_double stored in z. |
| `lmoved` | `procedure lmoved(x: longint; var z: fp_double);` | Converts the 32-bit longint value x to a 64-bit fp_double stored in z. |
| `smoved` | `procedure smoved(x: real; var z: fp_double);` | Promotes the 32-bit single-precision real value x to a 64-bit fp_double stored in z. |
| `xmoved` | `procedure xmoved(var x: fp_extended; var z: fp_double);` | Rounds and converts the 80-bit fp_extended value x to a 64-bit fp_double stored in z. |
| `wmovex` | `procedure wmovex(x: integer; var z: fp_extended);` | Converts the 16-bit integer value x to an 80-bit fp_extended value stored in z. |
| `lmovex` | `procedure lmovex(x: longint; var z: fp_extended);` | Converts the 32-bit longint value x to an 80-bit fp_extended value stored in z. |
| `smovex` | `procedure smovex(x: real; var z: fp_extended);` | Promotes the 32-bit single-precision real value x to an 80-bit fp_extended value stored in z. |
| `dmovex` | `procedure dmovex(var x: fp_double; var z: fp_extended);` | Promotes the 64-bit fp_double value x to an 80-bit fp_extended value stored in z. |
| `cmovefp` | `procedure cmovefp(var b: fp_bcdstring);` | Converts the 28-nibble packed decimal fp_bcdstring b into internal binary floating-point format and loads it into register FP0. |
| `i64neg` | `procedure i64neg(var x, z: fp_int64);` | Negates the 64-bit signed integer x (fp_int64, with -2^63 representing NaN) and stores -x in z. |
| `x80_integral` | `function x80_integral(var x: fp_extended): boolean;` | Returns TRUE if the 80-bit fp_extended value x is zero or an exact finite integer, or FALSE if fractional, infinite, or NaN. |
| `x80_break` | `procedure x80_break(var x, intx, fracx: fp_extended; var izero, fzero: boolean);` | Splits finite 80-bit fp_extended x into normalized integral and fractional parts intx and fracx, setting izero and fzero when either part is zero. |
| `x80_fpcb` | `function x80_fpcb: p_fpcb_type;` | Returns a pointer (@FPCB_) to the global floating-point control block from the 80-bit x80sub segment. |
| `fp_zero_ascii` | `procedure fp_zero_ascii(sign: boolean; before, after: integer; format: fp_format; var s: fp_string; var error: boolean);` | Formats signed zero (-0 if sign is TRUE, else 0) into ASCII string s according to format, before, and after, setting error on string overflow. |
| `fp_inf_ascii` | `procedure fp_inf_ascii(sign: boolean; width: integer; var s: fp_string; var error: boolean);` | Formats positive or negative infinity into s as width repeated '+' or '-' characters, setting error if width is outside 2..maxfpstring. |
| `getxcpn` | `function getxcpn(e: xcpn): boolean;` | Returns TRUE if the sticky floating-point exception flag e is currently set in FPCB_.block.status.excep. |
| `setxcpn` | `procedure setxcpn(e: xcpn; b: boolean);` | Sets or clears the sticky floating-point exception flag e in FPCB_.block.status.excep according to b. |
| `getexcepset` | `procedure getexcepset(var es: excepset);` | Retrieves the set of accumulated sticky floating-point exception flags from FPCB_.block.status.excep into es. |
| `setexcepset` | `procedure setexcepset(es: excepset);` | Replaces the accumulated sticky floating-point exception flags in FPCB_.block.status.excep with es. |
| `gettexcepset` | `procedure gettexcepset(var es: excepset);` | Retrieves the set of last-operation floating-point exception flags from FPCB_.block.status.texcep into es. |
| `settexcepset` | `procedure settexcepset(es: excepset);` | Sets the last-operation floating-point exception flags in FPCB_.block.status.texcep to es. |
| `clrexcepset` | `procedure clrexcepset;` | Clears all sticky floating-point exception flags in FPCB_.block.status.excep. |
| `gettrapset` | `procedure gettrapset(var es: excepset);` | Retrieves the set of currently trap-enabled floating-point exceptions from FPCB_.block.status.trap into es. |
| `clrtrapset` | `procedure clrtrapset;` | Disables all floating-point exception traps by clearing FPCB_.block.status.trap. |
| `fp_postoperation` | `procedure fp_postoperation(r: fp_traprecord);` | Marks trap record r as a composite floating-point operation (r.header := 0) and invokes checktrap(r) to dispatch any enabled exception trap. |
| `checktrap` | `procedure checktrap(r: fp_traprecord);` | Checks whether any exception in r.es is trap-enabled in FPCB_ and, if so, records @r in instad and invokes the highest-priority handler in ptrapvector. |
| `fpminus` | `function fpminus: boolean;` | Returns TRUE if the value in simulated floating-point register FP0 has a negative sign. |
| `fpkind` | `function fpkind: fp_kindtype;` | Returns the operand classification (zero, nonnormal, norml, inf, or NaN) of the value in register FP0. |
| `fpminusx` | `function fpminusx(var x: fp_extended): boolean;` | Returns TRUE if the 80-bit fp_extended value x has its negative sign bit set. |
| `fpkindx` | `function fpkindx(var x: fp_extended): fp_kindtype;` | Classifies the 80-bit fp_extended value x as zero, nonnormal, norml, inf, or NaN. |
| `copysign` | `procedure copysign(var x, y, z: fp_extended);` | Copies the 80-bit fp_extended magnitude of y with the sign bit of x into z. |
| `infinity` | `procedure infinity(var z: fp_extended);` | Sets the 80-bit fp_extended variable z to positive infinity (+INF). |
| `errornan` | `procedure errornan(error: byt; var z: fp_extended);` | Creates a quiet 80-bit fp_extended NaN with error code error in z and sets the invop exception flag. |
| `createnan` | `procedure createnan(trap: boolean; extension: fp_6bit; error, index: byt; var z: fp_extended);` | Constructs an 80-bit fp_extended NaN in z from the trapping flag trap, 6-bit extension, error code, and index byte. |
| `checknan` | `procedure checknan(var x, z: fp_extended);` | Copies 80-bit fp_extended x to z, clearing the trapping bit and signaling invop if x is a trapping NaN. |
| `NaN_parts` | `procedure NaN_parts(var x: fp_extended; var trap: boolean; var extension: fp_6bit; var error, index, index2: byt; var lowpart: fp_procaddress);` | Extracts the trap flag, 6-bit extension, error, index, index2, and 32-bit lowpart fields from an 80-bit fp_extended NaN x. |
| `choosenan` | `procedure choosenan(var x, y, z: fp_extended);` | Selects between x and y (at least one a NaN) to store a quiet NaN with the higher error code or significand in z, signaling invop if either is trapping. |
| `fpswap` | `procedure fpswap;` | Exchanges the contents of simulated floating-point registers FP0 and FP1. |
| `blockprelude` | `procedure blockprelude(var fpb: fp_blocktype);` | Saves the current floating-point register and status block FPCB_.block into fpb and clears all sticky exceptions and trap enables. |
| `blockpostlude` | `procedure blockpostlude(var fpb: fp_blocktype; var trapcoming: boolean);` | Restores FPCB_.block from fpb, merges newly raised exceptions into texcep and excep, and sets trapcoming if any enabled trap occurred. |
| `ilogb` | `function ilogb(var x: fp_extended): integer;` | Returns the unbiased binary exponent of 80-bit fp_extended x (normalizing denormalized values in normalizing mode). |
| `fpscalex` | `procedure fpscalex(var x: fp_extended; i: integer; var z: fp_extended);` | Scales the 80-bit fp_extended value x by 2^i for integer i and stores x * 2^i in z. |
| `scalb` | `procedure scalb(var x, y, z: fp_extended);` | Scales the 80-bit fp_extended value x by 2^y for integral fp_extended y and stores x * 2^y in z. |
| `exp2` | `procedure exp2(var x, z: fp_extended);` | Computes the base-2 exponential 2^x in 80-bit fp_extended precision and stores the result in z. |
| `expe` | `procedure expe(var x, z: fp_extended);` | Computes the natural exponential e^x in 80-bit fp_extended precision and stores the result in z. |
| `exp21` | `procedure exp21(var x, z: fp_extended);` | Computes 2^x - 1 accurately for small x in 80-bit fp_extended precision and stores the result in z. |
| `log2` | `procedure log2(var x, z: fp_extended);` | Computes the base-2 logarithm log2(x) in 80-bit fp_extended precision and stores the result in z. |
| `loge` | `procedure loge(var x, z: fp_extended);` | Computes the natural logarithm ln(x) in 80-bit fp_extended precision and stores the result in z. |
| `log10` | `procedure log10(var x, z: fp_extended);` | Computes the base-10 logarithm log10(x) in 80-bit fp_extended precision and stores the result in z. |
| `log12` | `procedure log12(var x, z: fp_extended);` | Computes log2(1 + x) accurately for small x in 80-bit fp_extended precision and stores the result in z. |
| `xtoy` | `procedure xtoy(var x, y, z: fp_extended);` | Raises 80-bit fp_extended x to the fp_extended power y (x^y) and stores the result in z. |
| `compound` | `procedure compound(var r, p, z: fp_extended);` | Computes the compound interest factor (1 + r)^p in 80-bit fp_extended precision and stores the result in z. |
| `annuity` | `procedure annuity(var r, p, z: fp_extended);` | Computes the present-value annuity factor (1 - (1 + r)^(-p)) / r in 80-bit fp_extended precision and stores the result in z. |
| `postdyadic` | `procedure postdyadic(name: fp_string; var x, y, z: fp_extended);` | Populates a composite fp_traprecord for the named two-operand fp_extended elementary function name (x, y, z) and calls fp_postoperation. |
| `xpwry` | `procedure xpwry(var x: fp_extended; y: integer; var z: fp_extended);` | Raises finite 80-bit fp_extended x to the nonzero integer power y by binary exponentiation and stores x^y in z. |
| `xexpy` | `procedure xexpy(var x, y, z: fp_extended);` | Computes x^y for non-negative 80-bit fp_extended x and finite y via 2^(y * log2(x)) and stores the result in z. |
| `pivalue` | `procedure pivalue(var z: fp_extended);` | Stores the 80-bit fp_extended constant pi in z. |
| `sinx` | `procedure sinx(var x, z: fp_extended);` | Computes the sine sin(x) (for x in radians) in 80-bit fp_extended precision and stores the result in z. |
| `cosx` | `procedure cosx(var x, z: fp_extended);` | Computes the cosine cos(x) (for x in radians) in 80-bit fp_extended precision and stores the result in z. |
| `tanx` | `procedure tanx(var x, z: fp_extended);` | Computes the tangent tan(x) (for x in radians) in 80-bit fp_extended precision and stores the result in z. |
| `asin` | `procedure asin(var x, z: fp_extended);` | Computes the principal arcsine arcsin(x) in radians in 80-bit fp_extended precision and stores the result in z. |
| `acos` | `procedure acos(var x, z: fp_extended);` | Computes the principal arccosine arccos(x) in radians in 80-bit fp_extended precision and stores the result in z. |
| `atan` | `procedure atan(var x, z: fp_extended);` | Computes the principal arctangent arctan(x) in radians in 80-bit fp_extended precision and stores the result in z. |
| `f32_pwrten` | `function f32_pwrten(n: integer): real;` | Computes and returns 10^n as a 32-bit single-precision real for Pascal power-of-ten operations. |
| `f32_exp` | `function f32_exp(x: real): real;` | Computes and returns the natural exponential e^x of 32-bit real x via 80-bit extended evaluation. |
| `f32_ln` | `function f32_ln(x: real): real;` | Computes and returns the natural logarithm ln(x) of 32-bit real x via 80-bit extended evaluation. |
| `f32_sin` | `function f32_sin(x: real): real;` | Computes and returns the sine sin(x) (in radians) of 32-bit real x via 80-bit extended evaluation. |
| `f32_cos` | `function f32_cos(x: real): real;` | Computes and returns the cosine cos(x) (in radians) of 32-bit real x via 80-bit extended evaluation. |
| `f32_atan` | `function f32_atan(x: real): real;` | Computes and returns the arctangent arctan(x) (in radians) of 32-bit real x via 80-bit extended evaluation. |
| `f32_trap` | `procedure f32_trap;` | Builds a 32-bit Pascal real trap record from texcep and invokes checktrap to dispatch enabled floating-point traps. |
| `p_f32` | `function p_f32(var s: fp_string): real;` | Parses the ASCII floating-point string s (allowing trailing blanks) and returns its 32-bit real value, or a NaN on syntax error. |
| `f32_r_r` | `function f32_r_r(var f: text): real;` | Reads and parses an ASCII floating-point token from text file f and returns its 32-bit real value for Pascal read(f, x). |
| `read_f32` | `procedure read_f32(var Infile: text; var Readchars: fp_string; var Z: real; var Error: boolean);` | Reads an ASCII floating-point number from Infile, returning the characters read in Readchars, the 32-bit real value in Z, and syntax status in Error. |
| `asciireal` | `procedure asciireal(Fileio: boolean; var Infile: text; var S: fp_string; First, Last: integer; var Next: integer; var Z: real; var Error: boolean);` | Scans and converts an ASCII floating-point number from Infile (when Fileio is TRUE) or S[First..Last] into 32-bit real Z, updating Next and Error. |
| `f32_w_e` | `procedure f32_w_e(var f: text; x: real; width: integer);` | Formats and writes 32-bit real x in scientific notation to text file f with field width width for Pascal write(f, x:width). |
| `f32_w_f` | `procedure f32_w_f(var f: text; x: real; width, after: integer);` | Formats and writes 32-bit real x in fixed-point notation to text file f with field width width and after fraction digits for Pascal write(f, x:width:after). |
| `f32_nan_ascii` | `procedure f32_nan_ascii(x: real; width: integer; var s: fp_string; var error: boolean);` | Formats a 32-bit real NaN x into ASCII representation (NaN'...') within width characters in s, setting error if width < 3 or truncated. |
| `f32_f_ascii` | `procedure f32_f_ascii(x: real; beforepoint: boolean; after: integer; var s: fp_string; var error: boolean);` | Formats finite 32-bit real x into fixed-point ASCII string s with after fraction digits (forcing a leading zero if beforepoint is TRUE), setting error on overflow. |
| `f32_e_ascii` | `procedure f32_e_ascii(x: real; before, after, ew: integer;                                                                 var s: fp_string; var error: boolean);` | Formats finite 32-bit real x into scientific-notation ASCII string s with before integer digits, after fraction digits, and ew exponent digits, setting error if invalid. |
| `pmovefp` | `procedure pmovefp(var S: fp_string; First, Last: integer; var Next: integer; var Error: boolean);` | Scans an ASCII floating-point number from S[First..Last] into register FP0, setting Next to the next character index and Error if invalid. |
| `asciimovex` | `procedure asciimovex(Fileio: boolean; var Infile: text; var S: fp_string; First, Last: integer; var Next: integer; var x: fp_extended; var Error: boolean);` | Scans and converts an ASCII floating-point number from Infile (when Fileio is TRUE) or S[First..Last] into 80-bit fp_extended x, updating Next and Error. |
| `x80_nan_ascii` | `procedure x80_nan_ascii(var x: fp_extended; width: integer; var s: fp_string; var error: boolean);` | Formats an 80-bit fp_extended NaN x into ASCII hexadecimal NaN notation (NaN'...') within width characters in s, setting error if it exceeds width. |
| `x80_i_ascii` | `procedure x80_i_ascii(var x: fp_extended; var s: fp_string; var error: boolean);` | Rounds finite 80-bit fp_extended x to an integer using the current rounding mode and formats it into minimal ASCII integer string s, setting error on overflow. |
| `x80_ir_ascii` | `procedure x80_ir_ascii(var x: fp_extended; var s: fp_string; var error: boolean);` | Rounds finite 80-bit fp_extended x to the nearest integer (outward on halfway ties, fp_iround) and formats it into ASCII integer string s, setting error on overflow. |
| `x80_f_ascii` | `procedure x80_f_ascii(var x: fp_extended; beforepoint: boolean; after: integer; var s: fp_string; var error: boolean);` | Formats finite 80-bit fp_extended x into fixed-point ASCII string s with after fraction digits (forcing a leading zero if beforepoint is TRUE), setting error on overflow. |
| `x80_e_ascii` | `procedure x80_e_ascii(var x: fp_extended; before, after, ew: integer; var s: fp_string; var error: boolean);` | Formats finite 80-bit fp_extended x into scientific-notation ASCII string s with before integer digits, after fraction digits, and ew exponent digits, setting error if invalid. |
| `x80_free_ascii` | `procedure x80_free_ascii(var x: fp_extended; width, maxsig: integer; format: fp_format; var s: fp_string; var error: boolean);` | Formats 80-bit fp_extended x into s within width characters and at most maxsig significant digits using free-form (fp_free or fp_lisa) selection, setting error if it cannot fit. |
| `x80_ascii` | `procedure x80_ascii(var x: fp_extended; Width, Before, After: integer; Format: fp_Format; var S: fp_string; var Error: boolean);` | Formats any 80-bit fp_extended value x (including zero, infinity, and NaN) into S according to Format, Width, Before, and After, filling S with '?' and setting Error on failure. |
| `x_eform` | `procedure x_eform(var x: fp_extended; n: integer; var sigma: integer; var s: fp_string; var e: integer);` | Decomposes finite 80-bit fp_extended x into sign sigma (1 if negative, 0 otherwise), up to n significant ASCII digits in s, and base-10 exponent e. |
| `x_iform` | `procedure x_iform(var x: fp_extended; var sigma: integer; var s: fp_string; var e: integer);` | Converts normalized integral 80-bit fp_extended x into sign sigma (1 if negative, 0 otherwise), ASCII digit string s, and non-negative base-10 scale e. |
| `movefp` | `procedure movefp(var x: fp_register);` | Copies the unpacked fp_register record x directly into simulated floating-point register FP0. |
| `movefp1` | `procedure movefp1(var x: fp_register);` | Copies the unpacked fp_register record x directly into simulated floating-point register FP1. |
| `fpmove` | `procedure fpmove(var z: fp_register);` | Copies the unpacked contents of simulated floating-point register FP0 into fp_register record z. |
| `fp1move` | `procedure fp1move(var z: fp_register);` | Copies the unpacked contents of simulated floating-point register FP1 into fp_register record z. |
| `i64abs` | `procedure i64abs(var x, z: fp_int64);` | Computes the absolute value of 64-bit signed integer x (fp_int64, preserving -2^63 as NaN) and stores it in z. |
| `i64mfp` | `procedure i64mfp(var x: fp_int64);` | Converts the 64-bit integer x (fp_int64, treating -2^63 as an integer NaN) to internal floating-point format and loads it into FP0. |
| `i64mfp1` | `procedure i64mfp1(var x: fp_int64);` | Converts the 64-bit integer x (fp_int64, treating -2^63 as an integer NaN) to internal floating-point format and loads it into FP1. |
| `fpmovei64` | `procedure fpmovei64(var z: fp_int64);` | Rounds and converts the value in floating-point register FP0 to a 64-bit integer z (fp_int64), setting cvtovfl and returning -2^63 on overflow. |
| `logb` | `procedure logb(var x, z: fp_extended);` | Computes the IEEE unbiased exponent of 80-bit fp_extended x as an fp_extended value in z (returning -INF with div0 for zero and +INF for infinity). |
| `nextafter` | `procedure nextafter(var x, y, z: fp_extended);` | Stores in z the next representable floating-point value after x toward y under the current rounding precision mode (getprec). |
| `evalue` | `procedure evalue(var z: fp_extended);` | Stores the 80-bit fp_extended constant e (base of natural logarithms) in z. |
| `xtoi` | `procedure xtoi(var x: fp_extended; i: integer; var z: fp_extended);` | Raises 80-bit fp_extended x to the 16-bit integer power i (x^i, with 0^0 = 1) and stores the result in z. |
| `expe1` | `procedure expe1(var x, z: fp_extended);` | Computes e^x - 1 accurately for small x in 80-bit fp_extended precision and stores the result in z. |
| `log1e` | `procedure log1e(var x, z: fp_extended);` | Computes ln(1 + x) accurately for small x in 80-bit fp_extended precision and stores the result in z. |
| `sinhx` | `procedure sinhx(var x, z: fp_extended);` | Computes the hyperbolic sine sinh(x) in 80-bit fp_extended precision and stores the result in z. |
| `coshx` | `procedure coshx(var x, z: fp_extended);` | Computes the hyperbolic cosine cosh(x) in 80-bit fp_extended precision and stores the result in z. |
| `tanhx` | `procedure tanhx(var x, z: fp_extended);` | Computes the hyperbolic tangent tanh(x) in 80-bit fp_extended precision and stores the result in z. |
| `abs2x` | `procedure abs2x(var x, y, z: fp_extended);` | Computes the Euclidean hypotenuse sqrt(x^2 + y^2) (\|x + iy\|) without premature overflow or underflow and stores it in z. |
| `atan2x` | `procedure atan2x(var x, y, z: fp_extended);` | Computes the four-quadrant principal arctangent arctan(x / y) in radians in [-pi, pi] using the signs of x and y and stores it in z. |
| `pmoved` | `procedure pmoved(var s: fp_string; var x: fp_double);` | Parses the ASCII floating-point string s (allowing trailing blanks) into 64-bit fp_double x, storing an nanascbin error NaN if invalid. |
| `pmovex` | `procedure pmovex(var s: fp_string; var x: fp_extended);` | Parses the ASCII floating-point string s (allowing trailing blanks) into 80-bit fp_extended x, storing an nanascbin error NaN if invalid. |
| `dmovep` | `procedure dmovep(var x: fp_double; var s: fp_string);` | Formats 64-bit fp_double x into a right-justified 24-character fp_lisa ASCII string s. |
| `xmovep` | `procedure xmovep(var x: fp_extended; var s: fp_string);` | Formats 80-bit fp_extended x into a right-justified 27-character fp_lisa ASCII string s. |
| `nextrandom` | `function nextrandom(lastrandom: longint): longint;` | Computes the next multiplicative congruential pseudo-random longint (16807 * lastrandom mod (2^31 - 1)) in 1..2147483646. |
| `x80_maxform` | `procedure x80_maxform(var x: fp_extended; var sigma: integer; var s: fp_string; var e: integer);` | Decomposes finite 80-bit fp_extended x into sign sigma, maximum-precision ASCII digits s (combining integer and fraction parts), and base-10 exponent e. |
| `x80_eform` | `procedure x80_eform(var x: fp_extended; var sigma: integer; var s: fp_string; var e: integer);` | Decomposes finite 80-bit fp_extended x into sign sigma, default maximum E-format ASCII significant digits s, and base-10 exponent e. |
| `excepname` | `procedure excepname(e: xcpn; var name: fp_string);` | Returns the symbolic name ('Invop', 'Overfl', 'Underfl', 'Div0', 'Inxact', 'Cvtovfl', etc.) of floating-point exception e in name. |
| `getround` | `function getround: rmode;` | Returns the current IEEE rounding mode (rnear, rzero, rpos, or rneg) from FPCB_.block.status.mode. |
| `setround` | `procedure setround(x: rmode);` | Sets the current IEEE rounding mode (rnear, rzero, rpos, or rneg) in FPCB_.block.status.mode to x. |
| `getclos` | `function getclos: closure;` | Returns the current IEEE infinity closure mode (proj or affine) from FPCB_.block.status.mode. |
| `setclos` | `procedure setclos(x: closure);` | Sets the current IEEE infinity closure mode (proj or affine) in FPCB_.block.status.mode to x. |
| `getdnorm` | `function getdnorm: denorm;` | Returns the current IEEE denormalized-number handling mode (warning or normalizing) from FPCB_.block.status.mode. |
| `setdnorm` | `procedure setdnorm(x: denorm);` | Sets the current IEEE denormalized-number handling mode (warning or normalizing) in FPCB_.block.status.mode to x. |
| `getprec` | `function getprec: extprec;` | Returns the current IEEE extended rounding precision mode (xprec, sprec, or dprec) from FPCB_.block.status.mode. |
| `setprec` | `procedure setprec(x: extprec);` | Sets the current IEEE extended rounding precision mode (xprec, sprec, or dprec) in FPCB_.block.status.mode to x. |
| `gethalt` | `function gethalt(e: xcpn): boolean;` | Returns TRUE if floating-point trapping is enabled for exception e in FPCB_.block.status.trap. |
| `sethalt` | `procedure sethalt(e: xcpn; b: boolean);` | Enables or disables floating-point trapping for exception e in FPCB_.block.status.trap according to b. |
| `settrapset` | `procedure settrapset(es: excepset);` | Sets the set of trap-enabled floating-point exceptions in FPCB_.block.status.trap to es. |
| `gettrap` | `function gettrap(e: xcpn): fp_procaddress;` | Returns the Pascal trap-handler procedure address installed in FPCB_.ptrapvector[e] for exception e. |
| `settrap` | `procedure settrap(e: xcpn; f: fp_procaddress);` | Installs Pascal trap-handler procedure address f in FPCB_.ptrapvector[e] for floating-point exception e. |
| `initfp` | `procedure initfp;` | Initializes the floating-point control block FPCB_ to default IEEE modes, cleared exceptions, and disabled traps. |
| `initfptrap` | `procedure initfptrap;` | Initializes FPCB_ with diagnostic trap handlers and enables maximal floating-point exception trapping. |
| `initelem` | `procedure initelem;` | Initializes the floating-point control block FPCB_ and the constant and polynomial tables required by the elementary transcendental functions. |
| `ldfpmodes` | `procedure ldfpmodes;` | Executes a no-op stub in segment fpm (fpmodes) to force the operating system loader to bring that code segment into memory. |
| `ldf32` | `procedure ldf32;` | Executes a no-op stub in segment uf32 (ldf32) to force the operating system loader to bring the 32-bit floating-point segment into memory. |
| `ldx80` | `procedure ldx80;` | Executes a no-op stub in segment ux80 (x80) to force the operating system loader to bring the 80-bit extended segment into memory. |
| `ldx80elem` | `procedure ldx80elem;` | Executes a no-op stub in segment ux80elem (x80elem) to force the operating system loader to bring the extended elementary-function segment into memory. |
