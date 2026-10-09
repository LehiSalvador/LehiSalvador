"""Self-contained GitHub-compatible SVG artwork with static fallbacks."""

import datetime as dt
import base64
from functools import lru_cache
from html import escape
from pathlib import Path
import struct

try:
    from .profile_data import build_grid
except ImportError:
    from profile_data import build_grid

BG, PANEL, BORDER = "#0d1117", "#161b22", "#30363d"
INK, MUTED, ROSE, GREEN = "#e6edf3", "#9da7b3", "#bc7886", "#39d353"
PALETTE = ["#1c2530", "#0e4429", "#006d32", "#26a641", GREEN]
MONTHS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
FONT = "Arial, Helvetica, sans-serif"
FIRE_CSS = """.pixel-fire{image-rendering:pixelated;animation:fire-frames 1.6s steps(16,end) infinite}
@keyframes fire-frames{from{transform:translateY(0)}to{transform:translateY(var(--fire-travel))}}
@keyframes ember-glow{0%,100%{opacity:.45}50%{opacity:1}}
@media(prefers-reduced-motion:reduce){.pixel-fire{animation:none!important}}"""


@lru_cache(maxsize=2)
def _fire_texture(filename):
    png = (Path(__file__).resolve().parents[1] / 'assets' / filename).read_bytes()
    if png[:8] != b'\x89PNG\r\n\x1a\n' or png[25] != 6:
        raise ValueError('Pixel fire atlas must be an RGBA PNG')
    width, height = struct.unpack('>II', png[16:24])
    return 'data:image/png;base64,' + base64.b64encode(png).decode('ascii'), width, height


def fire_border(width: int, height: int) -> str:
    """Play sixteen independently drawn fire frames through a clipped sprite strip."""
    filename = 'fire-pixels-card.png' if (width, height) == (840, 880) else 'fire-pixels-calendar.png'
    uri, atlas_w, atlas_h = _fire_texture(filename)
    frame_w, frame_h = width + 64, height + 64
    if (atlas_w, atlas_h) != (frame_w, frame_h * 16):
        raise ValueError('Pixel fire atlas dimensions do not match this card')
    return (
        f'<defs><clipPath id="fire-window"><rect x="-32" y="-32" width="{frame_w}" height="{frame_h}"/></clipPath></defs>'
        '<g clip-path="url(#fire-window)" aria-hidden="true">'
        f'<image class="pixel-fire" x="-32" y="-32" width="{atlas_w}" height="{atlas_h}" '
        f'style="--fire-travel:-{atlas_h}px" href="{uri}"/></g>'
    )


def label(x, y, value, size=16, fill=INK, extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" {extra}>{escape(str(value))}</text>'


def frame(width, height, heading, title, description, css=""):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width + 64}" height="{height + 64}" viewBox="-32 -32 {width + 64} {height + 64}" '
        f'role="img" aria-labelledby="title desc" font-family="{FONT}">',
        f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>',
        f'<style>{FIRE_CSS}{css}</style>',
        f'<rect x="-32" y="-32" width="{width + 64}" height="{height + 64}" fill="{BG}"/>',
        f'<rect width="{width}" height="{height}" rx="14" fill="{BG}"/>',
        f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="14" fill="none" stroke="{BORDER}"/>',
        f'<path d="M0 48H{width}" stroke="{BORDER}"/>',
        '<circle cx="22" cy="24" r="5" fill="#ff5f56"/><circle cx="40" cy="24" r="5" fill="#ffbd2e"/>'
        '<circle cx="58" cy="24" r="5" fill="#27c93f"/>',
        label(width / 2, 32, heading, 22 if width == 840 else 18, INK, 'text-anchor="middle" font-weight="600"'),
    ]


def render_heatmap(data):
    grid = build_grid(data["days"])
    width, height, left, top = 860, 262, 49, 85
    step = min(14.4, (width - left - 26) / len(grid))
    cell = step - 3
    css = '''.day-entrance{animation:reveal .55s cubic-bezier(.2,.8,.2,1) both;transform-box:fill-box;transform-origin:center}
@keyframes reveal{0%{opacity:0;transform:scale(.2)}65%{opacity:1;transform:scale(1.1)}100%{opacity:1;transform:scale(1)}}
.day[data-active="true"]{animation:activity-pulse 8s ease-in-out infinite}
@keyframes activity-pulse{0%,100%{opacity:1}50%{opacity:.58}}
@keyframes soft-pulse{0%,100%{opacity:1}50%{opacity:.55}}
.calendar-wave{animation:calendar-scan 6s linear infinite;opacity:0}
@keyframes calendar-scan{0%,100%{opacity:0}6%{opacity:1}20%{opacity:0}}
.activity-rim{animation:ember-glow 4s ease-in-out infinite}
@media(prefers-reduced-motion:reduce){.day-entrance{animation:none!important}.day[data-active="true"]{animation-name:soft-pulse;animation-duration:6s}}'''
    parts = frame(width, height, "Contribuciones públicas", "Calendario de contribuciones de Lehi Salvador",
                  f'{data["total_contributions"]:,} contribuciones entre {data["range"]["start"]} y {data["range"]["end"]}.', css)
    seen = set()
    for column, week in enumerate(grid):
        for row, day in enumerate(week):
            if day is None:
                continue
            date = dt.date.fromisoformat(day["date"])
            month = day["date"][:7]
            if month not in seen:
                seen.add(month)
                # The trailing partial month is too close to the previous label.
                if column == 0 or column <= len(grid) - 3:
                    parts.append(label(left + column * step, top - 13, MONTHS[date.month - 1], 11, MUTED))
            delay = .2 + column * .046 + row * .055
            parts.append(f'<g class="day-entrance" style="animation-delay:{delay:.3f}s">')
            active = 'true' if day['count'] else 'false'
            pulse_delay = -(column * .18 + row * .13)
            parts.append(f'<rect class="day" data-active="{active}" x="{left + column * step:.2f}" y="{top + row * step:.2f}" '
                         f'width="{cell:.2f}" height="{cell:.2f}" rx="2.4" fill="{PALETTE[day["level"]]}" '
                         f'style="animation-delay:{pulse_delay:.3f}s"><title>{day["date"]}: {day["count"]} contribuciones</title></rect>')
            if day['count']:
                parts.append(f'<rect class="activity-rim" x="{left + column * step:.2f}" y="{top + row * step:.2f}" '
                             f'width="{cell:.2f}" height="{cell:.2f}" rx="2.4" fill="none" stroke="#ffe59a" '
                             f'stroke-width="1.1" style="animation-delay:{pulse_delay:.3f}s" aria-hidden="true"/>')
            parts.append('</g>')
    # An opacity wave marks the scan, never changes any contribution color/count.
    for column in range(len(grid)):
        parts.append(f'<rect class="calendar-wave" x="{left + column * step - 1:.2f}" y="{top - 2}" '
                     f'width="{cell + 2:.2f}" height="{6 * step + cell + 4:.2f}" rx="3" '
                     f'fill="none" stroke="#ffe69d" stroke-width="2" '
                     f'style="animation-delay:{-6 + column * 6 / len(grid):.3f}s" aria-hidden="true"/>')
    for row, day in [(1, "Lun"), (3, "Mié"), (5, "Vie")]:
        parts.append(label(16, top + row * step + cell - 1, day, 10, MUTED))
    parts.append(label(49, 213, f'{number(data["total_contributions"])} contribuciones en el último año', 16, INK))
    parts.append(label(676, 213, "Menos", 10, MUTED))
    for level, color in enumerate(PALETTE):
        parts.append(f'<rect x="{718 + level * 16}" y="202" width="11" height="11" rx="2" fill="{color}"/>')
    parts.append(label(802, 213, "Más", 10, MUTED))
    parts.append(f'<path d="M20 228H840" stroke="{BORDER}"/>')
    parts.append(label(22, 249, "Datos públicos de GitHub · actualización diaria", 12, MUTED))
    parts.append(label(838, 249, f'{data["generated_at"][:10]} · UTC', 12, MUTED, 'text-anchor="end"'))
    parts.append(fire_border(width, height))
    parts.append('</svg>')
    return ''.join(parts)


def short_date(date):
    value = dt.date.fromisoformat(date)
    return f'{value.day} {MONTHS[value.month - 1].lower()}'


def streak_span(streak):
    return f'{short_date(streak["start"])} – {short_date(streak["end"])}' if streak["length"] else "Sin racha activa"


def number(value):
    formatted = f'{value:,.1f}' if isinstance(value, float) else f'{round(value):,}'
    return formatted.replace(',', ' ').replace('.', ',')


def render_stats(data):
    css = '''.tile{animation:slide .55s ease-out both}
@keyframes slide{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
.bar{transform-box:fill-box;transform-origin:bottom;animation:grow .7s ease-out both}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@media(prefers-reduced-motion:reduce){.tile,.bar{animation:none!important}}'''
    cur, longest, best = data["current_streak"], data["longest_streak"], data["best_day"]
    n_days = len(data["days"])
    tiles = [
        ("Racha actual", cur["length"], "días", streak_span(cur), GREEN, "current-streak"),
        ("Mayor racha", longest["length"], "días", "En el período mostrado", INK, "longest-streak"),
        ("Contribuciones", data["total_contributions"], "", "En el último año", INK, "contributions"),
        ("Días activos", data["active_days"], f"de {n_days}", f'{data["active_days"] / n_days:.0%} del período', INK, "active-days"),
        ("Mejor día", best["count"], "", short_date(best["date"]) if best["count"] else "Sin contribuciones", INK, "best-day"),
        ("Promedio diario", data["avg_per_active_day"], "", "Por día con actividad", INK, "daily-average"),
    ]
    parts = frame(840, 880, "Resumen de GitHub", "Estadísticas públicas de Lehi Salvador",
                  f'{data["total_contributions"]:,} contribuciones; racha actual de {cur["length"]} días; mayor racha de {longest["length"]} días en el período.', css)
    for i, (name, value, suffix, caption, color, metric) in enumerate(tiles):
        x, y = 24 + i % 2 * 404, 70 + i // 2 * 145
        start = .35 + i * .14
        parts.append(f'<g class="tile" style="animation-delay:{start:.2f}s">')
        parts.append(f'<rect x="{x}" y="{y}" width="388" height="129" rx="9" fill="{PANEL}" stroke="{BORDER}"/>')
        parts.append(label(x + 22, y + 31, name, 24, MUTED))
        # Metrics stay readable; only the surrounding frame loops.
        parts.append(label(x + 22, y + 88, number(value), 54, color,
                           f'font-weight="700" data-metric="{metric}"'))
        if suffix:
            parts.append(label(x + 228, y + 87, suffix, 23, MUTED))
        parts.append(label(x + 22, y + 116, caption, 19, MUTED))
        parts.append('</g>')

    chart_x, chart_y, chart_w, chart_h = 24, 513, 792, 302
    parts.append(f'<rect x="{chart_x}" y="{chart_y}" width="{chart_w}" height="{chart_h}" rx="9" fill="{PANEL}" stroke="{BORDER}"/>')
    parts.append(label(46, 551, "Actividad mensual", 24, MUTED))
    plot_l, plot_r, plot_top, plot_bot = 48, 792, 588, 766
    peak = max(month["total"] for month in data["monthly"]) or 1
    slot = (plot_r - plot_l) / len(data["monthly"])
    bar_w = slot * .58
    for i, month in enumerate(data["monthly"]):
        h = (plot_bot - plot_top) * month["total"] / peak
        x = plot_l + i * slot + (slot - bar_w) / 2
        delay = 1.5 + i * .08
        parts.append(f'<rect class="bar" x="{x:.2f}" y="{plot_bot - h:.2f}" width="{bar_w:.2f}" height="{h:.2f}" rx="3" '
                     f'fill="{GREEN if month["total"] == peak else "#26a641"}" style="animation-delay:{delay:.2f}s">'
                     f'<title>{month["month"]}: {month["total"]} contribuciones</title></rect>')
        name = MONTHS[int(month["month"][5:7]) - 1]
        parts.append(label(x + bar_w / 2, 797, name, 15, MUTED, 'text-anchor="middle"'))
        if month["total"] == peak:
            parts.append(label(x + bar_w / 2, plot_bot - h - 12, f'{peak:,}', 16, INK, 'text-anchor="middle"'))
    parts.append(f'<path d="M24 838H816" stroke="{BORDER}"/>')
    parts.append(label(25, 862, "Actividad pública", 18, ROSE))
    parts.append(label(816, 862, "Actualización diaria", 18, MUTED, 'text-anchor="end"'))
    parts.append(fire_border(840, 880))
    parts.append('</svg>')
    return ''.join(parts)
