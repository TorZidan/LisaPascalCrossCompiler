#!/usr/bin/env python3
"""png2lisaicon.py -- turn a 48 x 32 PNG into a Lisa Office System tool icon
file ({Tnnn}ICON).

The LOS Filer loads "{T<toolnumber>}icon" from the tool's volume with FMAddFont:
the icon file is a QuickDraw FONT with three 48 x 32 characters:
    char 0  overlayCode  drawn over the standard tool/stationery shape
    char 1  dataCode     the icon picture   (tools without documents)
    char 2  maskCode     the icon mask
plus the font's missing-character glyph (50% gray), padded to 1024 bytes.

Usage:
    python3 png2lisaicon.py icon_48x32.png ICON.BIN [mask.png]
    then copy the resulting ICON.BIN to the tool's volume and rename it to {T<toolnumber>}ICON, e.g. to {T197001}ICON
"""
from __future__ import annotations

import struct, sys, zlib

W, H = 48, 32


def read_png(path: str) -> list[list[bool]]:
    """Read a 48x32 8-bit PNG file and threshold its pixels into a boolean bitmap."""
    data = open(path, 'rb').read()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        sys.exit(f'{path}: not a PNG file')
    pos, idat, palette, trns = 8, b'', None, None
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos + 4])[0]
        typ, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + ln]
        if typ == b'IHDR':
            w, h, depth, ctype, _, _, interlace = struct.unpack('>IIBBBBB', body)
        elif typ == b'PLTE':
            palette = [body[i:i + 3] for i in range(0, len(body), 3)]
        elif typ == b'tRNS':
            trns = body
        elif typ == b'IDAT':
            idat += body
        pos += 12 + ln
    if (w, h) != (W, H):
        sys.exit(f'{path}: the icon must be {W} x {H} pixels, not {w} x {h}')
    if depth != 8 or interlace != 0:
        sys.exit(f'{path}: only 8-bit, non-interlaced PNGs are supported')
    bpp = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(ctype)
    if bpp is None:
        sys.exit(f'{path}: unsupported PNG colour type {ctype}')
    raw, stride = zlib.decompress(idat), w * bpp
    rows, prev, p = [], bytearray(stride), 0
    for _ in range(h):
        f, line = raw[p], bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + b) & 255
            elif f == 3:
                line[x] = (line[x] + ((a + b) >> 1)) & 255
            elif f == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(bytes(line))
        prev = line
    img = []
    for line in rows:
        out = []
        for x in range(w):
            px = line[x * bpp:(x + 1) * bpp]
            alpha = 255
            if ctype == 0:
                lum = px[0]
            elif ctype == 2:
                lum = (299 * px[0] + 587 * px[1] + 114 * px[2]) // 1000
            elif ctype == 3:
                r, g, bb = palette[px[0]]
                lum = (299 * r + 587 * g + 114 * bb) // 1000
                if trns is not None and px[0] < len(trns):
                    alpha = trns[px[0]]
            elif ctype == 4:
                lum, alpha = px[0], px[1]
            else:
                lum = (299 * px[0] + 587 * px[1] + 114 * px[2]) // 1000
                alpha = px[3]
            out.append(alpha >= 128 and lum < 128)
        img.append(out)
    return img


def outline_mask(img: list[list[bool]]) -> list[list[bool]]:
    """Flood-fill from the image border to compute an opaque interior silhouette mask."""
    outside = [[False] * W for _ in range(H)]
    stack = [(x, y) for x in range(W) for y in (0, H - 1)] + \
            [(x, y) for y in range(H) for x in (0, W - 1)]
    while stack:
        x, y = stack.pop()
        if 0 <= x < W and 0 <= y < H and not outside[y][x] and not img[y][x]:
            outside[y][x] = True
            stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return [[not outside[y][x] for x in range(W)] for y in range(H)]


def build_font(picture: list[list[bool]], mask: list[list[bool]]) -> bytes:
    """Pack the icon picture, mask, and 50% gray glyph into a 1024-byte QuickDraw FONT."""
    first, last = 0, 2
    nglyphs = last - first + 2
    row_words = nglyphs * W // 16
    gray = [[(x + y) % 2 == 0 for x in range(W)] for y in range(H)]
    glyphs = [picture, picture, mask, gray]
    strike = bytearray()
    for y in range(H):
        bits = [px for g in glyphs for px in g[y]]
        for i in range(0, len(bits), 8):
            byte = 0
            for b in bits[i:i + 8]:
                byte = (byte << 1) | int(b)
            strike.append(byte)
    loc = [i * W for i in range(nglyphs + 1)]
    owt = [W] * nglyphs + [-1]
    header_words = 13
    owt_loc = (header_words + row_words * H + len(loc)) - 8
    header = struct.pack('>13h',
                         3, first, last, W, 0, -H, W, H,
                         owt_loc, 0, H, 0, row_words)
    font = header + bytes(strike) + struct.pack(f'>{len(loc)}h', *loc) + \
        struct.pack(f'>{len(owt)}h', *owt)
    if len(font) > 1024:
        sys.exit('internal error: the font does not fit in 1024 bytes')
    return font + bytes(1024 - len(font))


def main() -> None:
    """Parse command-line arguments and write a 1024-byte Lisa tool icon file."""
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    picture = read_png(sys.argv[1])
    mask = read_png(sys.argv[3]) if len(sys.argv) == 4 else outline_mask(picture)
    open(sys.argv[2], 'wb').write(build_font(picture, mask))
    print(f'wrote {sys.argv[2]} (1024 bytes)')


if __name__ == '__main__':
    main()
