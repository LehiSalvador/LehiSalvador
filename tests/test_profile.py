import datetime as dt
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

from scripts.profile_data import build_grid, parse_calendar, summarize
from scripts.render_profile import render_heatmap, render_stats
from scripts.update_profile import save_outputs, update, validate_calendar_span


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

    def test_metrics_show_one_stable_final_value_without_counter_animation(self):
        data = summarize([cell("2026-10-05", 262, 4), cell("2026-10-06", 0)], self.today)
        data.update(username="LehiSalvador", generated_at="2026-10-06T10:00:00Z")
        root = ET.fromstring(render_stats(data))
        ns = '{http://www.w3.org/2000/svg}'
        value = root.find(f".//{ns}text[@data-metric='contributions']")
        self.assertIsNotNone(value, 'Metrics must use one readable final value')
        self.assertEqual(value.text, '262')
        self.assertEqual(len(root.findall(f'.//{ns}text[@data-metric]')), 6)
        self.assertNotIn('counter-strip', render_stats(data))

    def test_calendar_pulses_only_real_activity_and_preserves_counts_and_colors(self):
        data = summarize([cell('2026-10-05', 262, 4), cell('2026-10-06', 0)], self.today)
        data.update(username='LehiSalvador', generated_at='2026-10-06T10:00:00Z')
        svg = render_heatmap(data)
        root = ET.fromstring(svg)
        ns = '{http://www.w3.org/2000/svg}'
        active = root.findall(f".//{ns}rect[@data-active='true']")
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].get('fill'), '#39d353')
        self.assertEqual(active[0].find(f'{ns}title').text, '2026-10-05: 262 contribuciones')
        self.assertIn('infinite', svg)
        self.assertIn('soft-pulse', svg)

    def test_stats_border_keeps_looping_and_reduced_motion_has_no_travel(self):
        data = summarize([cell('2026-10-05', 1, 1), cell('2026-10-06', 0)], self.today)
        data.update(username='LehiSalvador', generated_at='2026-10-06T10:00:00Z')
        svg = render_stats(data)
        root = ET.fromstring(svg)
        ns = '{http://www.w3.org/2000/svg}'
        self.assertIsNotNone(root.find(f".//{ns}rect[@class='frame-motion']"))
        self.assertIn('infinite', svg)
        self.assertIn('frame-glow', svg)
        self.assertIn('stroke-dasharray:none', svg)

    def test_daily_generation_targets_the_readme_assets(self):
        data = summarize([cell('2026-10-05', 1, 1), cell('2026-10-06', 0)], self.today)
        data.update(username='LehiSalvador', generated_at='2026-10-06T10:00:00Z')
        readme = (Path(__file__).resolve().parents[1] / 'README.md').read_text(encoding='utf-8')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            save_outputs(root, data)
            for name in ('contributions-golden-fire.svg', 'github-golden-fire.svg'):
                self.assertIn(f'./assets/{name}', readme)
                art = (root / 'assets' / name).read_text(encoding='utf-8')
                ET.fromstring(art)
                self.assertIn('infinite', art)

    def test_gold_fire_frame_is_shared_by_calendar_and_statistics_without_covering_content(self):
        data = summarize([cell('2026-10-05', 2, 1), cell('2026-10-06', 0)], self.today)
        data.update(username='LehiSalvador', generated_at='2026-10-06T10:00:00Z')
        ns = '{http://www.w3.org/2000/svg}'
        for renderer in (render_heatmap, render_stats):
            with self.subTest(renderer=renderer.__name__):
                root = ET.fromstring(renderer(data))
                flames = root.findall(f".//{ns}g[@class='fire-tongue']/{ns}path")
                self.assertGreater(len(flames), 60)
                self.assertIsNotNone(root.find(f".//{ns}linearGradient[@id='fire-gold']"))
                self.assertTrue(root.get('viewBox').startswith('-24 -24 '))
                self.assertIn('ember-glow', renderer(data))

    def test_calendar_has_visible_wave_even_with_no_activity_without_faking_contributions(self):
        data = summarize([cell('2026-10-05', 0), cell('2026-10-06', 0)], self.today)
        data.update(username='LehiSalvador', generated_at='2026-10-06T10:00:00Z')
        root = ET.fromstring(render_heatmap(data))
        ns = '{http://www.w3.org/2000/svg}'
        wave = root.findall(f".//{ns}rect[@class='calendar-wave']")
        self.assertEqual(len(wave), len(build_grid(data['days'])))
        self.assertTrue(all(node.get('fill') == 'none' for node in wave))
        cells = root.findall(f".//{ns}rect[@class='day']")
        self.assertTrue(all(node.get('fill') == '#1c2530' for node in cells))
        self.assertIn('0 contribuciones en el último año', ''.join(root.itertext()))

    def test_published_logo_keeps_glowing_after_entrance_in_both_motion_modes(self):
        root_path = Path(__file__).resolve().parents[1]
        svg = (root_path / 'assets/salva-golden-fire.svg').read_text(encoding='utf-8')
        root = ET.fromstring(svg)
        ns = '{http://www.w3.org/2000/svg}'
        self.assertIsNotNone(root.find(f".//{ns}g[@class='logo-float']/{ns}g[@class='logo-light']/{ns}text"))
        self.assertGreater(len(root.findall(f".//{ns}g[@class='fire-tongue']")), 100)
        self.assertIn('float 9s ease-in-out infinite', svg)
        self.assertIn('logo-glow 9s ease-in-out infinite', svg)
        reduced = svg.split('@media(prefers-reduced-motion:reduce)', 1)[1]
        self.assertIn('.logo-float{animation:none', reduced)
        self.assertIn('.logo-light{animation-duration:12s}', reduced)

    def test_failed_scrape_preserves_previous_snapshot_and_art(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'data').mkdir()
            (root / 'assets').mkdir()
            expected = {'data/contributions.json': '{"previous":"valid"}',
                        'assets/contributions-golden-fire.svg': '<svg>previous calendar</svg>',
                        'assets/github-golden-fire.svg': '<svg>previous stats</svg>'}
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
                        'assets/contributions-golden-fire.svg': '<svg>previous calendar</svg>',
                        'assets/github-golden-fire.svg': '<svg>previous stats</svg>'}
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
