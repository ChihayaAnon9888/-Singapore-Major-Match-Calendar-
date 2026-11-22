"""Build the static GitHub Pages site and its public iCalendar feed."""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMINDER_MINUTES = 30
WIKI_LICENSE = "https://creativecommons.org/licenses/by-sa/3.0/"


def ical_text(value):
    return (value.replace("\\", "\\\\").replace("\r\n", "\n").replace("\r", "\n")
            .replace("\n", "\\n").replace(";", "\\;").replace(",", "\\,"))


def fold(line):
    """Fold at 75 UTF-8 octets as required by RFC 5545."""
    result = []
    current = []
    length = 0
    for character in line:
        size = len(character.encode("utf-8"))
        if length + size > 75:
            result.append("".join(current))
            current, length = [" "], 1
        current.append(character)
        length += size
    return "\r\n".join(result + ["".join(current)])


def stamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%Y%m%dT%H%M%SZ")


def calendar(config, matches):
    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//CS2 Major Calendar//Match Schedule//EN",
        "CALSCALE:GREGORIAN", "NAME:CS2 Major Calendar", "X-WR-CALNAME:CS2 Major Calendar",
        "REFRESH-INTERVAL;VALUE=DURATION:PT12H", "X-PUBLISHED-TTL:PT12H",
    ]
    stages = {stage["id"]: stage["name"] for stage in config["stages"]}
    for match in sorted(matches, key=lambda match: (match["startsAt"] or "", match["id"])):
        if not match["startsAt"]:
            continue
        teams = " vs ".join(match["teams"])
        round_name = match["round"]
        stage = stages[match["stage"]]
        summary = f"{teams} · {stage} {round_name}" if teams == "TBD vs TBD" else teams
        if match.get("tentative"):
            summary = f"{summary} (tentative)"
        description = [
            config["name"], f"{stage} · {round_name}",
            f"Format: BO{match['bestOf']}" if match["bestOf"] else "",
            "Provisional start time from HLTV. The matchup and time may change." if match.get("tentative") else "",
            f"Match data from Liquipedia contributors (CC BY-SA 3.0): {match['source']}",
            f"License: {WIKI_LICENSE}", f"HLTV coverage: {config['hltv']}",
        ]
        revision = datetime.fromisoformat(match["updatedAt"].replace("Z", "+00:00"))
        cancelled = match.get("status") == "cancelled"
        status = "CANCELLED" if cancelled else ("TENTATIVE" if match.get("tentative") else "CONFIRMED")
        lines.extend([
            "BEGIN:VEVENT", f"UID:{config['id']}-{match['id']}@cs2-major-calendar",
            f"DTSTAMP:{stamp(match['updatedAt'])}", f"LAST-MODIFIED:{stamp(match['updatedAt'])}",
            f"SEQUENCE:{int(revision.timestamp())}", f"DTSTART:{stamp(match['startsAt'])}",
            f"SUMMARY:{ical_text(summary)}",
            f"DESCRIPTION:{ical_text(chr(10).join(filter(None, description)))}",
            f"URL:{match['source']}", f"STATUS:{status}", "TRANSP:TRANSPARENT",
        ])
        if not cancelled:
            lines.extend([
                "BEGIN:VALARM", f"TRIGGER:-PT{REMINDER_MINUTES}M", "ACTION:DISPLAY",
                f"DESCRIPTION:{ical_text(summary)}", "END:VALARM",
            ])
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(map(fold, lines)) + "\r\n"


def build(output, schedule_path):
    config = json.loads((ROOT / "data/major.json").read_text())
    schedule = json.loads(schedule_path.read_text())
    matches = schedule["matches"]
    ids = {match["id"] for match in matches}
    if schedule["majorId"] != config["id"] or len(ids) != len(matches) or not any(match["startsAt"] for match in matches):
        raise ValueError("The schedule must match the configured Major and contain unique, timed matches.")
    if output.resolve() == (ROOT / "site").resolve():
        raise ValueError("Use a build directory outside the site source directory.")
    public_data = {
        "major": {key: config[key] for key in ("name", "location", "timeZone", "start", "end", "official", "hltv")},
        "stages": [{key: stage[key] for key in ("id", "name", "start", "end")} for stage in config["stages"]],
        "updatedAt": schedule["updatedAt"],
        "matches": matches,
    }
    public_data["major"]["wiki"] = "https://liquipedia.net/counterstrike/" + config["wiki"].replace(" ", "_")
    ics = calendar(config, matches)
    shutil.copytree(ROOT / "site", output, dirs_exist_ok=True)
    (output / "schedule.json").write_text(json.dumps(public_data, ensure_ascii=False), encoding="utf-8")
    (output / "major.ics").write_bytes(ics.encode("utf-8"))
    (output / ".nojekyll").touch()
    print(f"Built {output} with {sum(bool(match['startsAt']) for match in matches)} calendar entries")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument("--schedule", type=Path, default=ROOT / "data/schedule.json")
    args = parser.parse_args()
    build(args.output, args.schedule)
