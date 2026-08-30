# hbs-event-email-digest

A Claude Code plugin that reads the daily **HBS Student Event Calendar** digest email, shows you a filtered brief of what is actually worth attending, and adds the events you pick to your Outlook calendar.

The digest email arrives at 7:00 PM ET every day. It is useful, but it mixes RC, EC, All Students and Partners events into one wall of HTML, and anything you want to attend has to be retyped into Outlook by hand. This fixes both halves of that.

## What you get

```
/hbs-event-email-digest
```

```
Wednesday Sep 2: 3 events for you, 1 RSVP deadline closing today.

Today
  1. Building a Skills-Based Resume
     Wed Sep 2, 3:30 - 4:20 PM | Aldrich 207 | RC Students
  2. Guided meditation
     Wed Sep 2, 4:00 - 4:30 PM | Chapel | All Students
  ✓ Club Fair  (already on your calendar)

RSVP deadlines
  HBS Rock Entrepreneurship Day, RSVP by today at 12:00 PM

Other audiences
  Liberty Mutual Coffee Chats, 10:00 AM - 3:00 PM, Virtual (EC Students)

Add events by number.
```

Then `add 1, 2` and they are on your calendar, with the location filled in and a link back to the event page.

- Filters to **your** class year plus All Students, worked out from your `@mba20XX.hbs.edu` address. Nothing to configure.
- Demotes rather than hides. EC-only and Partners events drop to the bottom instead of disappearing.
- Skips events already on your calendar, whether this plugin added them or you did.
- Surfaces RSVP deadlines and cancellations from the sidebar, which are easy to miss in the email.
- Adds events as **free**, not busy, so campus events do not make you look unavailable to classmates.

## Install

**Prerequisite:** connect the **Microsoft 365 connector** on claude.ai first, under Settings then Connectors. Without it the plugin has no way to reach your mail or calendar and every run will fail. Use your HBS account.

Then, in Claude Code:

```
/plugin marketplace add realslimslaney/hbs-event-email-digest
/plugin install hbs-event-email-digest
```

Run it with `/hbs-event-email-digest`. That is the whole setup.

## Getting it daily

Run `/hbs-event-email-digest` whenever you want the brief. Mornings work well, since the digest email lands at 7:00 PM the night before and is final by then.

**Automating it does not currently work, and this is worth knowing before you try.** The Microsoft 365 connector is only available inside an interactive Claude session. It is not reachable from:

- **Scheduled cloud agents (routines).** The routine API accepts an `mcp_connections` entry for the connector and reports it as connected, but its tools never appear in the sandbox. Tested twice, including with `permitted_tools` named explicitly.
- **Headless CLI runs** (`claude -p "/hbs-event-email-digest"`), which is what you would point a cron job or Windows Task Scheduler at. The connector is absent there too.

So a scheduled run has no way to read your mail. If you set one up anyway it will not silently invent events, but it will not produce a brief either.

If that changes, this section will be the first thing updated.

## A note on timezones

The digest is always in Eastern time, and this plugin always writes events in Eastern time, so events land on your calendar at the correct moment no matter what.

But if your **Outlook timezone** is set to something other than Eastern, every event will *display* shifted. If your 9:30 AM class shows as 8:30 AM in Outlook, that is what is happening. Fix it in Outlook under Settings, Calendar, then Time zone. The plugin will tell you if it detects this.

## Configuration

Optional. Everything is auto-detected. To override, create `hbs-event-email-digest.config.json` in your Claude config directory (`~/.claude/` by default). See `hbs-event-email-digest.config.example.json` in this repo.

```json
{
  "audiences": ["RC Students", "All Students"],
  "showOtherAudiences": true,
  "timeZone": "Eastern Standard Time"
}
```

## Sharing it

Send classmates the two install lines above. They need their own Microsoft 365 connector; the plugin reads whoever is signed in and works out their class year on its own, so an EC gets EC events with no changes.

## Limitations

- Reads only the digest email, so it sees what the digest sees. An event added to the calendar website after the 7:00 PM send does not appear until the next digest.
- Adds events, never removes them. If an event is cancelled it will tell you, but you delete it yourself.
- Never RSVPs on your behalf. RSVP deadlines are surfaced with a link; the RSVP itself is on you.

## License

MIT. Not affiliated with or endorsed by Harvard Business School.
