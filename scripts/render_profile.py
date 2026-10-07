"""Self-contained GitHub-compatible SVG artwork with static fallbacks."""

import datetime as dt
from html import escape

try:
    from .profile_data import build_grid
except ImportError:
    from profile_data import build_grid

BG, PANEL, BORDER = "#0d1117", "#161b22", "#30363d"
INK, MUTED, ROSE, GREEN = "#e6edf3", "#9da7b3", "#bc7886", "#39d353"
PALETTE = ["#1c2530", "#0e4429", "#006d32", "#26a641", GREEN]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
FONT = "Consolas, Menlo, Monaco, monospace"


def label(x, y, value, size=16, fill=INK, extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" {extra}>{escape(str(value))}</text>'


def frame(width, height, command, title, description, css=""):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'role="img" aria-labelledby="title desc" font-family="{FONT}">',
        f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>',
        f'<style>{css}</style>',
        f'<rect width="{width}" height="{height}" rx="14" fill="{BG}"/>',
        f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="14" fill="none" stroke="{BORDER}"/>',
        f'<path d="M0 36H{width}" stroke="{BORDER}"/>',
        '<circle cx="20" cy="18" r="4" fill="#ff5f56"/><circle cx="35" cy="18" r="4" fill="#ffbd2e"/>'
        '<circle cx="50" cy="18" r="4" fill="#27c93f"/>',
        label(width / 2, 23, command, 12, MUTED, 'text-anchor="middle"'),
    ]


def render_heatmap(data):
    grid = build_grid(data["days"])
    width, height, left, top = 860, 250, 49, 75
    step = min(14.4, (width - left - 26) / len(grid))
    cell = step - 3
    css = '''.day{animation:reveal .55s cubic-bezier(.2,.8,.2,1) both;transform-box:fill-box;transform-origin:center}
@keyframes reveal{0%{opacity:0;transform:scale(.2)}65%{opacity:1;transform:scale(1.1)}100%{opacity:1;transform:scale(1)}}
@media(prefers-reduced-motion:reduce){.day{animation:none!important}}'''
    parts = frame(width, height, "lehi@github: ~/contributions --graph", "Lehi Salvador contribution calendar",
                  f'{data["total_contributions"]:,} contributions from {data["range"]["start"]} to {data["range"]["end"]}.', css)
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
            parts.append(f'<rect class="day" x="{left + column * step:.2f}" y="{top + row * step:.2f}" '
                         f'width="{cell:.2f}" height="{cell:.2f}" rx="2.4" fill="{PALETTE[day["level"]]}" '
                         f'style="animation-delay:{delay:.3f}s"><title>{day["date"]}: {day["count"]} contributions</title></rect>')
    for row, day in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        parts.append(label(16, top + row * step + cell - 1, day, 10, MUTED))
    parts.append(label(49, 201, f'{data["total_contributions"]:,} contributions in the last year', 14, INK))
    parts.append(label(684, 201, "Less", 10, MUTED))
    for level, color in enumerate(PALETTE):
        parts.append(f'<rect x="{718 + level * 16}" y="190" width="11" height="11" rx="2" fill="{color}"/>')
    parts.append(label(802, 201, "More", 10, MUTED))
    parts.append(f'<path d="M20 216H840" stroke="{BORDER}"/>')
    parts.append(label(22, 237, "public GitHub calendar / refreshed daily", 11, MUTED))
    parts.append(label(838, 237, f'data: {data["generated_at"][:10]} UTC', 11, MUTED, 'text-anchor="end"'))
    parts.append('</svg>')
    return ''.join(parts)


def short_date(date):
    value = dt.date.fromisoformat(date)
    return f'{MONTHS[value.month - 1]} {value.day}'


def streak_span(streak):
    return f'{short_date(streak["start"])} – {short_date(streak["end"])}' if streak["length"] else "No active streak"


def number(value):
    return f'{value:,.1f}' if isinstance(value, float) else f'{round(value):,}'


def render_stats(data):
    css = '''.tile{animation:slide .55s ease-out both}
@keyframes slide{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
.bar{transform-box:fill-box;transform-origin:bottom;animation:grow .7s ease-out both}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
.counter{animation:counter .09s steps(1) forwards}
@keyframes counter{0%,99%{opacity:1}100%{opacity:0}}
.final{animation:final .01s steps(1) backwards}
@keyframes final{from{opacity:0}to{opacity:1}}
@media(prefers-reduced-motion:reduce){.tile,.bar,.final{animation:none!important}.counter{display:none!important}}'''
    cur, longest, best = data["current_streak"], data["longest_streak"], data["best_day"]
    n_days = len(data["days"])
    tiles = [
        ("current streak", cur["length"], "days", streak_span(cur), GREEN),
        ("longest streak", longest["length"], "days", "within calendar period", INK),
        ("contributions", data["total_contributions"], "", "in the last year", INK),
        ("active days", data["active_days"], f"/ {n_days}", f'{data["active_days"] / n_days:.0%} of calendar days', INK),
        ("best day", best["count"], "", short_date(best["date"]) if best["count"] else "No contributions yet", INK),
        ("avg / active day", data["avg_per_active_day"], "", "contributions", INK),
    ]
    parts = frame(840, 880, "lehi@github: ~$ ./stats.sh", "Lehi Salvador contribution statistics",
                  f'Total {data["total_contributions"]:,}; current streak {cur["length"]} days; longest streak {longest["length"]} days in calendar period.', css)
    for i, (name, value, suffix, caption, color) in enumerate(tiles):
        x, y = 24 + i % 2 * 404, 62 + i // 2 * 145
        start = .35 + i * .14
        count_start = start + .25
        parts.append(f'<g class="tile" style="animation-delay:{start:.2f}s">')
        parts.append(f'<rect x="{x}" y="{y}" width="388" height="129" rx="9" fill="{PANEL}" stroke="{BORDER}"/>')
        parts.append(label(x + 22, y + 31, '$ ' + name, 21, MUTED))
        # Intermediate frames disappear; the final number is visible without CSS.
        for k in range(12):
            t = k / 12
            estimate = value * (1 - (1 - t) ** 3)
            parts.append(label(x + 22, y + 83, number(estimate), 49, color,
                               f'class="counter" opacity="0" font-weight="700" style="animation-delay:{count_start + k * .09:.3f}s"'))
        parts.append(label(x + 22, y + 83, number(value), 49, color,
                           f'class="final" font-weight="700" style="animation-delay:{count_start + 12 * .09:.3f}s"'))
        if suffix:
            parts.append(label(x + 22 + len(number(value)) * 29.5 + 12, y + 82, suffix, 22, MUTED))
        parts.append(label(x + 22, y + 111, caption, 17, MUTED))
        parts.append('</g>')

    chart_x, chart_y, chart_w, chart_h = 24, 513, 792, 302
    parts.append(f'<rect x="{chart_x}" y="{chart_y}" width="{chart_w}" height="{chart_h}" rx="9" fill="{PANEL}" stroke="{BORDER}"/>')
    parts.append(label(46, 551, "$ contributions / month", 21, MUTED))
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
                     f'<title>{month["month"]}: {month["total"]} contributions</title></rect>')
        name = MONTHS[int(month["month"][5:7]) - 1]
        parts.append(label(x + bar_w / 2, 797, name, 15, MUTED, 'text-anchor="middle"'))
        if month["total"] == peak:
            parts.append(label(x + bar_w / 2, plot_bot - h - 12, f'{peak:,}', 16, INK, 'text-anchor="middle"'))
    parts.append(f'<path d="M24 838H816" stroke="{BORDER}"/>')
    parts.append(label(25, 862, "lehi@github:~$", 14, ROSE))
    parts.append(label(165, 862, "build useful things.", 14, MUTED))
    parts.append('</svg>')
    return ''.join(parts)
