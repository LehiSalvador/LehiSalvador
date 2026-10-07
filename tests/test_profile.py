import datetime as dt
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

from scripts.profile_data import build_grid, parse_calendar, summarize
from scripts.render_profile import render_heatmap, render_stats
from scripts.update_profile import update, validate_calendar_span


def cell(date, count, level=0):
    return {"date": date, "count": count, "level": level}


class ContributionTests(unittest.TestCase):
    today = dt.date(2026, 10, 6)

    def test_tooltip_counts_include_thousands_and_ignore_future_dates(self):
        markup = '''<td class="ContributionCalendar-day" id="a" data-date="2026-10-05" data-level="4"></td>
        <tool-tip for="a">1,234 contributions on October 5th.</tool-tip>
        <td class="ContributionCalendar-day" id="b" data-date="2026-10-06" data-level="0"></td>
        <tool-tip for="b">No contributions on October 6th.</tool-tip>
        <td class="ContributionCalendar-day" id="c" data-date="2026-10-07" data-level="0"></td>'''
        self.assertEqual(parse_calendar(markup, self.today), [cell("2026-10-05", 1234, 4), cell("2026-10-06", 0)])

    def test_missing_tooltip_is_failure_instead_of_fake_zero(self):
        markup = '<td class="ContributionCalendar-day" id="a" data-date="2026-10-06" data-level="2"></td>'
        with self.assertRaises(ValueError):
            parse_calendar(markup, self.today)

    def test_changed_markup_is_failure(self):
        with self.assertRaises(ValueError):
            parse_calendar('<html>please sign in</html>', self.today)

    def test_zero_activity_has_zero_metrics(self):
        data = summarize([cell("2026-10-05", 0), cell("2026-10-06", 0)], self.today)
        self.assertEqual(data["total_contributions"], 0)
        self.assertEqual(data["avg_per_active_day"], 0)
        self.assertEqual(data["active_days"], 0)
        self.assertEqual(data["current_streak"]["length"], 0)

    def test_unfinished_today_does_not_break_streak(self):
        data = summarize([cell("2026-10-04", 1), cell("2026-10-05", 4), cell("2026-10-06", 0)], self.today)
        self.assertEqual(data["current_streak"], {"length": 2, "start": "2026-10-04", "end": "2026-10-05"})
        self.assertEqual(data["monthly"], [{"month": "2026-10", "total": 5}])

    def test_yesterdays_zero_breaks_streak(self):
        data = summarize([cell("2026-10-04", 1), cell("2026-10-05", 0)], self.today)
        self.assertEqual(data["current_streak"]["length"], 0)
        self.assertEqual(data["longest_streak"]["length"], 1)

    def test_calendar_aligns_monday_to_monday(self):
        weeks = build_grid([cell("2026-10-05", 2), cell("2026-10-06", 3)])
        self.assertIsNone(weeks[0][0])
        self.assertEqual(weeks[0][1]["date"], "2026-10-05")
        self.assertEqual(weeks[0][2]["date"], "2026-10-06")
        self.assertEqual(len(weeks[0]), 7)

    def test_gaps_are_rejected_instead_of_inflating_streak(self):
        with self.assertRaises(ValueError):
            summarize([cell("2026-10-04", 1), cell("2026-10-06", 1)], self.today)

    def test_zero_activity_renders_complete_accessible_svg(self):
        data = summarize([cell("2026-10-05", 0), cell("2026-10-06", 0)], self.today)
        data.update(username="LehiSalvador", generated_at="2026-10-06T10:00:00Z")
        for render in (render_heatmap, render_stats):
            svg = render(data)
            root = ET.fromstring(svg)
            self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
            self.assertIn("prefers-reduced-motion", svg)
            self.assertIn("<title>", svg)
            self.assertIn("0", "".join(root.itertext()))
        graph = ET.fromstring(render_heatmap(data))
        cells = graph.findall(".//{http://www.w3.org/2000/svg}rect[@class='day']")
        self.assertEqual(len(cells), 2)

    def test_integer_counters_keep_integer_frames_and_one_visible_row(self):
        data = summarize([cell("2026-10-05", 262, 4), cell("2026-10-06", 0)], self.today)
        data.update(username="LehiSalvador", generated_at="2026-10-06T10:00:00Z")
        root = ET.fromstring(render_stats(data))
        ns = '{http://www.w3.org/2000/svg}'
        strip = root.find(f".//{ns}g[@data-metric='contributions']")
        self.assertIsNotNone(strip, 'Counter must use one clipped value column')
        values = [node.text for node in strip.findall(f'{ns}text')]
        self.assertEqual(values[0], '0')
        self.assertEqual(values[-1], '262')
        for value in values:
            self.assertRegex(value, r'^\d+(?: \d{3})*$')
        clip = root.find(f".//{ns}clipPath[@id='counter-2']/{ns}rect")
        self.assertIsNotNone(clip)
        rows = strip.findall(f'{ns}text')
        row_spacing = float(rows[1].get('y')) - float(rows[0].get('y'))
        self.assertLess(float(clip.get('height')), row_spacing)

    def test_failed_scrape_preserves_previous_snapshot_and_art(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'data').mkdir()
            (root / 'assets').mkdir()
            expected = {'data/contributions.json': '{"previous":"valid"}',
                        'assets/contributions.svg': '<svg>previous calendar</svg>',
                        'assets/stats.svg': '<svg>previous stats</svg>'}
            for name, content in expected.items():
                (root / name).write_text(content, encoding='utf-8')
            with patch('scripts.update_profile.fetch_calendar', return_value='<html>blocked</html>'):
                with self.assertRaises(ValueError):
                    update(root=root, username='LehiSalvador')
            for name, content in expected.items():
                self.assertEqual((root / name).read_text(encoding='utf-8'), content)

    def test_truncated_calendar_cannot_replace_valid_snapshot(self):
        today = dt.datetime.now(dt.timezone.utc).date()
        start = today - dt.timedelta(days=370)
        start -= dt.timedelta(days=(start.weekday() + 1) % 7)
        markup = ''.join(
            f'<td class="ContributionCalendar-day" id="d{i}" data-date="{start + dt.timedelta(days=i)}" data-level="0"></td>'
            f'<tool-tip for="d{i}">No contributions on this date.</tool-tip>'
            for i in range(350)
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'data').mkdir()
            (root / 'assets').mkdir()
            expected = {'data/contributions.json': '{"previous":"valid"}',
                        'assets/contributions.svg': '<svg>previous calendar</svg>',
                        'assets/stats.svg': '<svg>previous stats</svg>'}
            for name, content in expected.items():
                (root / name).write_text(content, encoding='utf-8')
            with patch('scripts.update_profile.fetch_calendar', return_value=markup):
                with self.assertRaisesRegex(ValueError, 'Incomplete|Stale'):
                    update(root=root, username='LehiSalvador')
            for name, content in expected.items():
                self.assertEqual((root / name).read_text(encoding='utf-8'), content)

    def test_complete_but_stale_calendar_is_rejected(self):
        end = self.today - dt.timedelta(days=10)
        start = end.replace(year=end.year - 1)
        start -= dt.timedelta(days=(start.weekday() + 1) % 7)
        days = [cell((start + dt.timedelta(days=i)).isoformat(), 0)
                for i in range((end - start).days + 1)]
        with self.assertRaisesRegex(ValueError, 'Stale'):
            validate_calendar_span(days, self.today)


if __name__ == "__main__":
    unittest.main()
