"use strict";

const byId = (id) => document.getElementById(id);
const feedUrl = new URL("./major.ics", document.baseURI);
const isPublic = feedUrl.protocol === "https:" && !["localhost", "127.0.0.1", "[::1]"].includes(feedUrl.hostname);
const instructions = byId("instructions");
const instructionsText = byId("instructions-text");
const feedInput = byId("feed-url");

feedInput.value = feedUrl.href;
if (isPublic) byId("apple").href = feedUrl.href.replace(/^https:/, "webcal:");

document.querySelectorAll("[data-provider]").forEach((link) => {
  link.addEventListener("click", async (event) => {
    instructions.hidden = false;
    feedInput.hidden = true;
    if (!isPublic) {
      event.preventDefault();
      instructionsText.textContent = "Online subscriptions become available when the site is published. You can download the calendar now.";
      return;
    }
    const nextStep = link.dataset.provider === "google"
      ? "In Google Calendar on desktop, paste the URL into From URL and choose Add calendar."
      : "In Outlook, choose Add calendar, then Subscribe from web, and paste the URL.";
    instructionsText.textContent = nextStep;
    try {
      await navigator.clipboard.writeText(feedUrl.href);
      instructionsText.textContent = `Calendar URL copied. ${nextStep}`;
    } catch {
      feedInput.hidden = false;
      feedInput.select();
    }
  });
});

async function showLocalStart() {
  try {
    const response = await fetch("./schedule.json");
    if (!response.ok) throw new Error(`Schedule request failed with HTTP ${response.status}`);
    const { major, matches } = await response.json();
    byId("edition").textContent = major.name;
    byId("wiki-link").href = major.wiki;
    byId("hltv-link").href = major.hltv;

    const now = Date.now();
    const starts = matches
      .filter((match) => match.startsAt && match.status !== "cancelled")
      .map((match) => match.startsAt)
      .sort();
    const nextStart = starts.find((start) => Date.parse(start) >= now);
    const isoDate = nextStart || starts[0];
    if (!isoDate) return;

    const localStart = new Date(isoDate);
    const locale = navigator.language;
    const formatter = new Intl.DateTimeFormat(locale, {
      month: "short", day: "numeric", hour: "numeric", minute: "2-digit", timeZoneName: "shortOffset",
    });
    const deviceZone = formatter.resolvedOptions().timeZone;
    const zoneLabel = deviceZone.split("/").at(-1).replaceAll("_", " ");
    const time = byId("start-time");
    time.dateTime = isoDate;
    time.textContent = formatter.format(localStart);
    byId("start-label").textContent = nextStart ? "Next match" : "Tournament opening";
    byId("start-zone").textContent = `· ${zoneLabel}`;
    byId("match-start").hidden = false;
  } catch (error) {
    console.error(error);
  }
}

showLocalStart();
