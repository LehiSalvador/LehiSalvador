"""Fetch public GitHub data and safely regenerate contribution artwork."""

import datetime as dt
import json
import os
from pathlib import Path
import re
import tempfile
import time
from urllib.request import Request, urlopen

try:
    from .profile_data import parse_calendar, summarize
    from .render_profile import render_heatmap, render_stats
except ImportError:
    from profile_data import parse_calendar, summarize
    from render_profile import render_heatmap, render_stats

ROOT = Path(__file__).resolve().parents[1]


def fetch_calendar(username):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}', username):
        raise ValueError('Invalid GitHub username')
    request = Request(f'https://github.com/users/{username}/contributions',
                      headers={'User-Agent': 'Salva-Systems-profile/1.0', 'Accept-Language': 'en-US'})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                return response.read().decode('utf-8')
        except OSError:
            if attempt == 2:
                raise
            time.sleep(2 ** (attempt + 1))


def save_outputs(root, data):
    # Render all content before touching the previous good snapshot.
    outputs = {
        'data/contributions.json': json.dumps(data, indent=2, ensure_ascii=False) + '\n',
        'assets/contributions-pixel-fire.svg': render_heatmap(data),
        'assets/github-pixel-fire.svg': render_stats(data),
    }
    staged = []
    try:
        for name, content in outputs.items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=target.parent,
                                             prefix='.profile-', delete=False) as temporary:
                temporary.write(content)
                staged.append((Path(temporary.name), target))
        for temporary, target in staged:
            os.replace(temporary, target)
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)


def validate_calendar_span(days, today):
    first = dt.date.fromisoformat(days[0]['date'])
    last = dt.date.fromisoformat(days[-1]['date'])
    if not 365 <= len(days) <= 373:
        raise ValueError('Incomplete calendar response; preserving last valid artwork')
    if last not in (today, today - dt.timedelta(days=1)):
        raise ValueError('Stale calendar response; preserving last valid artwork')
    try:
        anniversary = last.replace(year=last.year - 1)
    except ValueError:  # February 29 maps to February 28 in the previous year.
        anniversary = last.replace(year=last.year - 1, day=28)
    expected = anniversary - dt.timedelta(days=(anniversary.weekday() + 1) % 7)
    # GitHub can clip to 53 calendar columns around leap-year boundaries.
    if first not in (expected, expected + dt.timedelta(days=7)):
        raise ValueError('Incomplete annual calendar range; preserving last valid artwork')


def update(root=ROOT, username=None):
    username = username or os.environ.get('GH_PROFILE_USER', 'LehiSalvador')
    now = dt.datetime.now(dt.timezone.utc)
    today = now.date()
    days = parse_calendar(fetch_calendar(username), today)
    validate_calendar_span(days, today)
    data = summarize(days, today)
    data['username'] = username
    snapshot = root / 'data/contributions.json'
    previous = json.loads(snapshot.read_text(encoding='utf-8')) if snapshot.exists() else None
    comparable = {key: value for key, value in (previous or {}).items() if key != 'generated_at'}
    data['generated_at'] = previous['generated_at'] if comparable == data else now.isoformat(timespec='seconds').replace('+00:00', 'Z')
    save_outputs(root, data)
    print(f'{username}: {data["total_contributions"]:,} contributions / {len(days)} days / current streak {data["current_streak"]["length"]}')
    return data


if __name__ == '__main__':
    update()
