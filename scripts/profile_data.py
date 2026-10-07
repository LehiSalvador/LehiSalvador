"""Parse and validate public GitHub contribution data without dependencies."""

import datetime as dt
from html.parser import HTMLParser
import re


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = []
        self.tooltips = {}
        self.tooltip_id = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("td", "rect") and "data-date" in attrs:
            if "ContributionCalendar-day" in attrs.get("class", ""):
                self.cells.append(attrs)
        if tag == "tool-tip":
            self.tooltip_id = attrs.get("for")
            if self.tooltip_id:
                self.tooltips[self.tooltip_id] = ""

    def handle_data(self, data):
        if self.tooltip_id:
            self.tooltips[self.tooltip_id] += data

    def handle_endtag(self, tag):
        if tag == "tool-tip":
            self.tooltip_id = None


def validate_days(days):
    if not days:
        raise ValueError("Contribution calendar is empty")
    previous = None
    for day in days:
        date = dt.date.fromisoformat(day["date"])
        if previous and date != previous + dt.timedelta(days=1):
            raise ValueError("Contribution dates must be unique and consecutive")
        if not isinstance(day["count"], int) or day["count"] < 0:
            raise ValueError("Contribution counts must be non-negative integers")
        if day["level"] not in range(5):
            raise ValueError("Unknown GitHub contribution color level")
        previous = date


def parse_calendar(markup, today):
    parser = CalendarParser()
    parser.feed(markup)
    days = []
    for attrs in parser.cells:
        date = dt.date.fromisoformat(attrs["data-date"])
        if date > today:
            continue
        text = parser.tooltips.get(attrs.get("id"), "").strip()
        if re.search(r"\bno contributions\b", text, re.I):
            count = 0
        else:
            match = re.search(r"^([\d,\s]+)\s+contributions?\b", text, re.I)
            if not match:
                raise ValueError(f"Missing or unrecognized contribution tooltip for {date}")
            count = int(re.sub(r"[\s,]", "", match[1]))
        level = int(attrs.get("data-level", "0"))
        if (count == 0) != (level == 0):
            raise ValueError(f"Contribution count and color disagree for {date}")
        days.append({"date": date.isoformat(), "count": count, "level": level})
    days.sort(key=lambda day: day["date"])
    validate_days(days)
    return days


def summarize(days, today):
    days = [day for day in days if dt.date.fromisoformat(day["date"]) <= today]
    validate_days(days)
    total = sum(day["count"] for day in days)
    active = sum(day["count"] > 0 for day in days)
    longest = {"length": 0, "start": None, "end": None}
    run = 0
    run_start = None
    monthly = {}
    for day in days:
        month = day["date"][:7]
        monthly[month] = monthly.get(month, 0) + day["count"]
        if day["count"]:
            if not run:
                run_start = day["date"]
            run += 1
            if run > longest["length"]:
                longest = {"length": run, "start": run_start, "end": day["date"]}
        else:
            run = 0

    current = {"length": 0, "start": None, "end": None}
    index = len(days) - 1
    last_date = dt.date.fromisoformat(days[index]["date"])
    if last_date >= today - dt.timedelta(days=1):
        if last_date == today and days[index]["count"] == 0:
            index -= 1
        end = index
        while index >= 0 and days[index]["count"]:
            index -= 1
        length = end - index
        if length:
            current = {"length": length, "start": days[index + 1]["date"], "end": days[end]["date"]}

    return {
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total_contributions": total,
        "active_days": active,
        "avg_per_active_day": round(total / active, 1) if active else 0,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": max(days, key=lambda day: day["count"]),
        "monthly": [{"month": month, "total": value} for month, value in sorted(monthly.items())],
        "days": days,
    }


def build_grid(days):
    validate_days(days)
    first = dt.date.fromisoformat(days[0]["date"])
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    last = dt.date.fromisoformat(days[-1]["date"])
    weeks = [[None] * 7 for _ in range((last - start).days // 7 + 1)]
    for day in days:
        offset = (dt.date.fromisoformat(day["date"]) - start).days
        weeks[offset // 7][offset % 7] = day
    return weeks
