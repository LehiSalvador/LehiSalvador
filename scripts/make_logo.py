"""Sample the official Salva Systems logo into a continuously animated ASCII SVG.

Local-only dependency: Pillow. Daily statistics workflow does not run this file.
"""

from html import escape
from pathlib import Path
import argparse
from PIL import Image

from render_profile import BG, INK, MUTED, ROSE, fire_border, frame, label

ROOT = Path(__file__).resolve().parents[1]


def render_logo(source):
    cols, rows, left, top, art_w, art_h = 144, 76, 48, 65, 744, 744
    # Source has a black background. Dark pixels become spaces, preserving it.
    image = Image.open(source).convert("RGB")
    # Remove avatar padding, then retain a square crop so the mark is not stretched.
    mask = image.convert("L").point(lambda value: 255 if value > 25 else 0)
    bounds = mask.getbbox()
    if bounds is None:
        raise ValueError("Logo source has no visible artwork")
    x0, y0, x1, y1 = bounds
    side = max(x1 - x0, y1 - y0) + 40
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    image = image.crop((round(cx - side / 2), round(cy - side / 2), round(cx + side / 2), round(cy + side / 2)))
    image = image.resize((cols, rows), Image.Resampling.LANCZOS)
    glyphs = ' .:-=+*#%@'
    cell_w, cell_h = art_w / cols, art_h / rows
    row_time = 5.8 / rows
    css = f'''.wipe{{animation:type {row_time:.4f}s linear both}}
@keyframes type{{from{{width:0}}to{{width:{art_w}px}}}}
.cursor{{animation:scan {row_time:.4f}s linear forwards}}
@keyframes scan{{0%{{opacity:.8;transform:translateX(0)}}99%{{opacity:.8}}100%{{opacity:0;transform:translateX({art_w}px)}}}}
.ready{{animation:ready .7s ease-out both;animation-delay:5.8s}}
@keyframes ready{{from{{opacity:0}}to{{opacity:1}}}}
.logo-float{{animation:float 9s ease-in-out infinite;animation-delay:5.8s}}
@keyframes float{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-8px)}}}}
.logo-light{{animation:logo-glow 9s ease-in-out infinite}}
@keyframes logo-glow{{0%,100%{{opacity:1}}50%{{opacity:.72}}}}
@media(prefers-reduced-motion:reduce){{.wipe,.ready,.logo-float{{animation:none!important}}.cursor{{display:none!important}}.logo-light{{animation-duration:12s}}}}'''
    parts = frame(840, 880, "Salva Systems", "Logo animado de Salva Systems",
                  "Símbolo y nombre oficiales de Salva Systems en ASCII, con movimiento y brillo continuos. Con movimiento reducido, solo cambia el brillo. Fundada por Lehi Salvador.", css)
    parts.append('<g class="logo-float"><g class="logo-light">')
    for row in range(rows):
        characters = []
        for col in range(cols):
            r, g, b = image.getpixel((col, row))
            lum = (.2126 * r + .7152 * g + .0722 * b) / 255
            lum = 0 if lum < .045 else min(1, (lum ** .70) * 1.5)
            characters.append(glyphs[round(lum * (len(glyphs) - 1))])
        y = top + row * cell_h
        delay = row * row_time
        parts.append(f'<defs><clipPath id="row{row}"><rect class="wipe" x="{left}" y="{y:.2f}" width="{art_w}" '
                     f'height="{cell_h + .5:.2f}" style="animation-delay:{delay:.4f}s"/></clipPath></defs>')
        parts.append(f'<text font-family="Consolas, Menlo, Monaco, monospace" xml:space="preserve" x="{left}" y="{y + cell_h * .79:.2f}" fill="{INK}" font-size="{cell_h * .84:.2f}" '
                     f'textLength="{art_w}" lengthAdjust="spacing" clip-path="url(#row{row})">{escape("".join(characters))}</text>')
        parts.append(f'<rect class="cursor" opacity="0" x="{left}" y="{y:.2f}" width="{cell_w:.2f}" height="{cell_h:.2f}" '
                     f'fill="{ROSE}" style="animation-delay:{delay:.4f}s"/>')
    parts.append('</g></g>')
    parts.append(f'<path d="M24 819H816" stroke="#30363d"/>')
    parts.append(label(25, 843, "Tecnología aplicada a operaciones", 19, MUTED))
    parts.append(label(25, 869, "Lehi Salvador · Founder", 20, INK, 'class="ready"'))
    parts.append(fire_border(840, 880))
    parts.append('</svg>')
    return ''.join(parts)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'assets/salva-source.png')
    parser.add_argument('--output', type=Path, default=ROOT / 'assets/salva-pixel-fire.svg')
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_logo(args.source), encoding='utf-8')
    print(f'Generated {args.output.name}')
