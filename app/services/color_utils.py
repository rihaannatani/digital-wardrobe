import colorsys

def hex_to_rgb(hex_color: str) -> tuple[int, int, int] | None:
    if not hex_color:
        return None
    s = hex_color.strip()
    if s.startswith("#"):
        s = s[1:]
    if len(s) != 6:
        return None
    try:
        r = int(s[0:2], 16)
        g = int(s[2:4], 16)
        b = int(s[4:6], 16)
        return (r, g, b)
    except ValueError:
        return None

def rgb_to_hsl(r: int, g: int, b: int) -> tuple[int, int, int]:
    rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
    h, l, s = colorsys.rgb_to_hls(rf, gf, bf)  # note: HLS order
    # convert to common HSL display
    H = int(round(h * 360))
    S = int(round(s * 100))
    L = int(round(l * 100))
    return (H, S, L)

def hex_to_hsl(hex_color: str) -> tuple[int, int, int] | None:
    rgb = hex_to_rgb(hex_color)
    if not rgb:
        return None
    return rgb_to_hsl(*rgb)
