"""Read Major match slots via Liquipedia's public MediaWiki Revisions API."""

import argparse
import gzip
import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
API = "https://liquipedia.net/counterstrike/api.php"
WIKI = "https://liquipedia.net/counterstrike/"
PLAYOFF_ROUNDS = {
    "R1": "Quarterfinal",
    "R2": "Semifinal",
    "R3": "Grand final",
    "Rx": "Third-place match",
}
TEAM_NAMES = {
    "1w": "The One", "100t": "100 Thieves", "9z": "9z",
    "aurora": "Aurora Gaming", "bb team": "BB Team", "chinggis": "Chinggis Warriors",
    "ef": "Eternal Fire", "falcons": "Team Falcons", "faze": "FaZe", "fq": "FlyQuest",
    "furia": "FURIA", "fut": "FUT", "gosh": "GOSH", "heroic": "HEROIC",
    "imp": "Imperial", "lvg": "Lynn Vision", "m80": "M80", "mibr": "MIBR",
    "mongolz": "The MongolZ", "mouz": "MOUZ", "navi": "NAVI",
    "nip": "Ninjas in Pyjamas", "pvision": "PVISION", "spirit": "Team Spirit",
    "tl": "Team Liquid", "vit": "Team Vitality",
}
OFFSETS = {"SGT": 8, "UTC": 0, "GMT": 0, "CET": 1, "CEST": 2}


def template_parts(source):
    """Return the top-level fields of a template starting at source[0]."""
    depth = 0
    link_depth = 0
    start = 2
    parts = []
    for token in re.finditer(r"\{\{|\}\}|\[\[|\]\]|\|", source):
        value = token.group()
        if value == "{{":
            depth += 1
        elif value == "}}":
            depth -= 1
            if depth == 0:
                return parts + [source[start:token.start()].strip()]
        elif value == "[[":
            link_depth += 1
        elif value == "]]":
            link_depth -= 1
        elif depth == 1 and link_depth == 0:
            parts.append(source[start:token.start()].strip())
            start = token.end()
    raise ValueError("Unclosed Liquipedia template")


def named_fields(parts):
    return {
        key.strip(): value.strip()
        for part in parts
        if re.match(r"^[\w-]+\s*=", part)
        for key, value in [part.split("=", 1)]
    }


def utc_string(value):
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def match_start(value):
    if not value:
        return None
    match = re.fullmatch(
        r"([A-Za-z]+ \d{1,2}, \d{4})\s*[-–]\s*(\d{1,2}:\d{2})\s*\{\{Abbr/(\w+)\}\}", value,
        flags=re.IGNORECASE,
    )
    if not match or match[3].upper() not in OFFSETS:
        raise ValueError(f"Unsupported match date from Liquipedia: {value}")
    local = datetime.strptime(f"{match[1]} {match[2]}", "%B %d, %Y %H:%M")
    return utc_string(local.replace(tzinfo=timezone(timedelta(hours=OFFSETS[match[3].upper()]))))


def team_name(value):
    if value.startswith("{{"):
        parts = template_parts(value)
        value = parts[1] if len(parts) > 1 else ""
    name = value.strip()
    if not name or name.lower() in {"tbd", "tba", "bye"}:
        return "TBD"
    return TEAM_NAMES.get(name.lower(), name.upper() if len(name) <= 3 else name.title())


def parse_stage(wikitext, stage, updated_at):
    wikitext = re.sub(r"<!--.*?-->", "", wikitext, flags=re.DOTALL)
    slots = []
    for group in re.finditer(r"\{\{(Matchlist|Bracket)(?=\s*\|)", wikitext, flags=re.IGNORECASE):
        parts = template_parts(wikitext[group.start():])[1:]
        fields = named_fields(parts)
        group_id = fields.get("id", "")
        if not re.fullmatch(r"[\w-]+", group_id):
            raise ValueError("Missing match group ID")
        for index, part in enumerate(part for part in parts if re.match(r"(?:\w+=)?\s*\{\{Match\b", part)):
            slot, _, match = part.partition("=")
            # Anonymous matches can contain '=' in their own template fields.
            if part.startswith("{{"):
                slot, match = f"M{index + 1}", part
            else:
                slot = slot.strip()
            details = named_fields(template_parts(match.lstrip())[1:])
            round_name = fields.get("matchsection") or PLAYOFF_ROUNDS[slot.split("M")[0]]
            hltv_id = details.get("hltv", "")
            maps = sum(bool(re.fullmatch(r"map\d+", key)) for key in details)
            best_of = int(details.get("bestof") or fields.get("bestof") or maps or 0) or None
            if round_name == "Grand final":
                best_of = 5
            slots.append({
                "id": f"{stage['id']}-{group_id}-{slot}",
                "stage": stage["id"],
                "round": round_name,
                "startsAt": match_start(details.get("date", "")),
                "teams": [team_name(details.get(f"opponent{i}literal") or details.get(f"opponent{i}", "")) for i in (1, 2)],
                "bestOf": best_of,
                "hltvId": int(hltv_id) if hltv_id.isascii() and hltv_id.isdigit() else None,
                "status": "cancelled" if details.get("cancelled", "").lower() in {"1", "true", "yes"} else "scheduled",
                "updatedAt": updated_at,
            })
    if len(slots) != stage["slots"] or len({slot["id"] for slot in slots}) != len(slots):
        raise ValueError(f"Unexpected {stage['name']} bracket structure: {len(slots)} slots")
    return slots


def apply_tentative_times(matches, stage, config):
    """Fill unpublished starts from manually recorded HLTV time slots."""
    for round_name, times in config.get("tentativeUtcTimes", {}).get(stage["id"], {}).items():
        round_matches = [match for match in matches if match["round"] == round_name]
        if len(round_matches) != len(times):
            raise ValueError(f"Unexpected slot count for {stage['name']} {round_name}")
        offset = max(0, int(round_name.split()[-1]) - 2)
        day = date.fromisoformat(stage["start"]) + timedelta(days=offset)
        planned = [f"{day}T{time}:00Z" for time in times]
        # Known starts consume their published slots first. Keep every remaining
        # provisional slot available for the draw, with no team assigned to it.
        for match in round_matches:
            if match["startsAt"] in planned:
                planned.remove(match["startsAt"])
        open_matches = [match for match in round_matches if not match["startsAt"]]
        formats = {match["bestOf"] for match in round_matches}
        for match, start in zip(open_matches, planned):
            match.update(startsAt=start, teams=["TBD", "TBD"], bestOf=next(iter(formats)) if len(formats) == 1 else None)
            match["tentative"] = True
            match["updatedAt"] = max(match["updatedAt"], f"{config['tentativeAsOf']}T00:00:00Z")


def fetch_pages(titles, contact_url):
    if not contact_url:
        raise ValueError("Set CALENDAR_CONTACT_URL or pass --contact-url with your public repository URL.")
    query = urlencode({
        "action": "query", "prop": "revisions", "rvprop": "timestamp|content",
        "rvslots": "main", "format": "json", "formatversion": 2, "titles": "|".join(titles),
    })
    request = Request(f"{API}?{query}", headers={
        "User-Agent": f"CS2MajorCalendar/1.0 ({contact_url})",
        "Accept-Encoding": "gzip",
    })
    with urlopen(request, timeout=30) as response:
        body = response.read()
        if response.headers.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
    return json.loads(body)


def normalize(payload, config):
    if "error" in payload or "query" not in payload:
        raise ValueError(f"Liquipedia API error: {payload.get('error', 'missing query')}")
    pages = {page["title"]: page for page in payload["query"]["pages"]}
    matches = []
    for stage in config["stages"]:
        title = f"{config['wiki']}/{stage['wiki']}"
        revision = pages[title]["revisions"][0]
        stage_matches = parse_stage(revision["slots"]["main"]["content"], stage, revision["timestamp"])
        # A blank round list is valid, but losing the known opening times
        # indicates a provider or template change and must not replace the feed.
        if stage["id"] == "stage-1" and not any(match["startsAt"] for match in stage_matches):
            raise ValueError("No Stage 1 match times found")
        apply_tentative_times(stage_matches, stage, config)
        wiki_url = WIKI + title.replace(" ", "_")
        for match in stage_matches:
            match["source"] = wiki_url
        matches.extend(stage_matches)
    return {
        "majorId": config["id"],
        "updatedAt": utc_string(datetime.now(timezone.utc)),
        "matches": matches,
    }


def main():
    import os

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data/schedule.json")
    parser.add_argument("--contact-url", default=os.environ.get("CALENDAR_CONTACT_URL"))
    parser.add_argument("--from-response", type=Path, help="Read a saved MediaWiki API response")
    parser.add_argument("--active", action="store_true", help="Print whether the scheduled sync window is active")
    args = parser.parse_args()
    config = json.loads((ROOT / "data/major.json").read_text())
    if args.active:
        today = datetime.now(timezone.utc).date()
        start = date.fromisoformat(config["start"]) - timedelta(days=14)
        end = date.fromisoformat(config["end"]) + timedelta(days=2)
        print(str(start <= today <= end).lower())
        return
    titles = [f"{config['wiki']}/{stage['wiki']}" for stage in config["stages"]]
    payload = json.loads(args.from_response.read_text()) if args.from_response else fetch_pages(titles, args.contact_url)
    snapshot = normalize(payload, config)
    temporary = args.output.with_suffix(".tmp")
    temporary.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(f"Read {len(snapshot['matches'])} match slots from Liquipedia")


if __name__ == "__main__":
    main()
