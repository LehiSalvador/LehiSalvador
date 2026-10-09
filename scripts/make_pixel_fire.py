"""Draw 16 distinct pixel-fire frames; Pillow is needed only to rebuild atlases."""

import math
from pathlib import Path

FRAMES, PIXEL, GUTTER = 16, 4, 32
COLORS = ('#fff3a4', '#ffdf59', '#ffb62c', '#ff8519', '#e74c12', '#a6280d')


def fire_pixels(width: int, height: int, frame: int) -> list[tuple[int, int, str]]:
    """Draw independent pixel states, never place a pixel inside the card."""
    frame %= FRAMES
    pixels = []
    for y in range(-GUTTER, height + GUTTER, PIXEL):
        for x in range(-GUTTER, width + GUTTER, PIXEL):
            if x + PIXEL > 0 and x < width and y + PIXEL > 0 and y < height:
                continue
            distance = max(-x, x + PIXEL - width, -y, y + PIXEL - height)
            if y < 0:
                position = x / PIXEL
            elif x >= width:
                position = (width + y) / PIXEL
            elif y >= height:
                position = (2 * width + height - x) / PIXEL
            else:
                position = (2 * width + 2 * height - y) / PIXEL
            # Each tongue has its own birth/growth/decay cycle and lean.
            # Neighboring tongues overlap, but never translate a base picture.
            tongue = math.floor(position / 5)
            flame_height = 8
            for seed in range(tongue - 1, tongue + 2):
                age = ((frame + seed * 7) % FRAMES) / FRAMES
                growth = math.sin(math.pi * age) ** .7
                center = seed * 5 + 2 + round(1.5 * math.sin(age * math.tau + seed))
                tip = 12 + round(16 * growth)
                flame_height = max(flame_height, tip - abs(position - center) * 8)
            flame_height = round(flame_height / PIXEL) * PIXEL
            if distance <= flame_height:
                flicker = ((int(position) * 13 + frame * 7 + distance) % 5) / 5
                color = min(5, max(0, int((distance - PIXEL) * 5 / max(PIXEL, flame_height - PIXEL) + flicker)))
                pixels.append((x, y, COLORS[color]))
            elif distance >= 24 and (int(position) * 17 + frame * 11 + distance * 3) % 137 == 0:
                pixels.append((x, y, COLORS[2]))
    return pixels


def write_atlas(width: int, height: int, target: Path) -> None:
    from PIL import Image, ImageDraw  # Local build dependency; daily workflow only reads PNG.

    frame_w, frame_h = width + 2 * GUTTER, height + 2 * GUTTER
    atlas = Image.new('RGBA', (frame_w, frame_h * FRAMES), (0, 0, 0, 0))
    for frame in range(FRAMES):
        # A separate canvas clips edge blocks when dimensions are not multiples
        # of PIXEL; otherwise the last row could leak into the following frame.
        canvas = Image.new('RGBA', (frame_w, frame_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)
        offset_y = GUTTER
        for x, y, color in fire_pixels(width, height, frame):
            draw.rectangle((x + GUTTER, y + offset_y,
                            x + GUTTER + PIXEL - 1, y + offset_y + PIXEL - 1), fill=color)
        atlas.paste(canvas, (0, frame * frame_h))
    atlas.save(target, optimize=True)


if __name__ == '__main__':
    assets = Path(__file__).resolve().parents[1] / 'assets'
    write_atlas(840, 880, assets / 'fire-pixels-card.png')
    write_atlas(860, 262, assets / 'fire-pixels-calendar.png')
    print('Generated two pixel-fire atlases, 16 distinct frames each.')
