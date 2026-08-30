# Digest email format

Reference for parsing the HBS Student Event Calendar daily digest. Verified against digests sent August 2026.

## Identifying the email

| Field | Value |
| --- | --- |
| Sender name | `Email from Student Event Calendar` |
| Sender address | `noreply@hbs.edu` |
| Subject | `[mbaeventcalendar] Student Event Calendar Daily Digest` |
| To | `svc_mbaevents@hbs.edu` (the reader is a list subscriber, not a direct recipient) |
| Sent | Daily at 23:00 UTC, which is 7:00 PM ET |

The digest sent on the evening of day N covers day N+1. A digest read in the morning is describing that same day.

Do not filter on the sender display name. Outlook search matches the address, so use `sender: "noreply@hbs.edu"` and check the subject client-side.

## Body structure

`body.contentType` is `html`. The layout is a nested table with two content cells.

### `td#primaryContent`

A sequence of `div.section` blocks. Each opens with an `<h2>` that determines the section type:

- `<h2>New Events</h2>` — events newly added since the last digest. These also appear again under Upcoming Events, so dedup by `masterEventId`.
- `<h2>Saturday, August 29, 2026</h2>` — a literal date heading. This is the day the digest covers. Events under it have no date line of their own.
- `<h2>Upcoming Events</h2>` — future events, each carrying its own date line.

Within a section, each event is an `<h3>` followed by a `<p>`:

```html
<h3><a href="{safelink}">Club Fair </a></h3>
<p>Wednesday, September 2, 2026<br />
4:30 - 6:00 PM, (Shad Hall Basketball Courts) <br />
<em>All Students; Partners (ALL) </em><br />
<a href="{safelink}">More Info</a> </p>
```

Field extraction from the `<p>`:

1. **Date** — present only if the first text node before a `<br/>` parses as a date. Absent under a date heading; present under New Events and Upcoming Events.
2. **Time and location** — `{start} - {end} {MERIDIEM}, ({location})`. The location is everything inside the outermost parentheses and can itself contain parentheses, as in `Peterson Park Grille Lounge 010A (rain location)`. It can also be a bare URL, as in `(https://harvard.zoom.us/j/92978532068)`, or the literal `(Virtual)`.
3. **Audience** — the `<em>`. Values seen: `RC Students`, `EC Students`, `All Students`, `All Students; Partners (ALL)`.
4. **Detail link** — the `More Info` anchor, same target as the title anchor.

Titles and audiences carry a trailing space. Trim everything.

### `td#secondaryContent`

Two optional sidebar blocks:

```html
<div class="section cancelled">
  <h3>Cancelled Events</h3>
  <ul><li><a href="{safelink}">Therapy dog</a> 09/23 - cancelled </li></ul>
</div>

<div class="section upcoming">
  <h3>Upcoming to Do</h3>
  <ul><li><a href="{safelink}">HBS Rock Entrepreneurship Day </a>&gt; RSVP Now by 09/01 at 12:00 PM </li></ul>
</div>
```

Cancelled entries carry an `MM/DD` date. Upcoming to Do entries are RSVP deadlines, formatted `> RSVP Now by MM/DD at H:MM AM/PM`.

**Empty sidebar blocks still render.** When there is nothing to report the block contains a sentence and an empty list, not nothing:

```html
<div class="section cancelled">
  <h3>Cancelled Events</h3>
  <div><p>There are no new cancelled student events.</p><ul></ul></div>
</div>
```

Check for `<li>` elements, not for the presence of the block. Never print a "There are no new cancelled student events" line back to the reader; just omit the section.

## Unwrapping safelinks

Every `href` is rewritten by Outlook ATP:

```
https://nam04.safelinks.protection.outlook.com/?url=https%3A%2F%2Fbeech.hbs.edu%2FeventCalendar%2Fuser%2FeventDetail.do%3FmasterEventId%3D205351&data=...&sdata=...&reserved=0
```

Take the `url` query parameter and URL-decode it once:

```
https://beech.hbs.edu/eventCalendar/user/eventDetail.do?masterEventId=205351
```

`masterEventId` is stable across digests and is the correct identity key for an event. Use it to dedup New Events against Upcoming Events, and to recognize events this skill has already added to the calendar.

## The missing meridiem

Start times omit AM/PM. Only the end time carries it.

| Digest text | Actual |
| --- | --- |
| `4:30 - 6:00 PM` | 4:30 PM to 6:00 PM |
| `10:00 - 3:00 PM` | 10:00 **AM** to 3:00 PM |
| `12:00 - 6:00 PM` | 12:00 PM (noon) to 6:00 PM |
| `3:30 - 4:20 PM` | 3:30 PM to 4:20 PM |

Algorithm: parse the end time with its meridiem. Try the start with the same meridiem; if that yields a non-negative duration, take it. Otherwise flip the start to the other meridiem. Equivalently, pick whichever start meridiem gives the shortest non-negative duration.

`12:00` is the edge case worth testing: 12:00 with a PM end is noon, not midnight.

## Stale dates under Upcoming Events

Multi-day and recurring events are listed under Upcoming Events with the date of the **first** occurrence in the series, which is often in the past.

In the digest of 2026-08-29 covering Sunday August 30, Upcoming Events contained:

```
Liberty Mutual Info Sessions   Wednesday, August 26, 2026
Liberty Mutual Coffee Chats    Thursday, August 27, 2026
```

Both dates had already passed, and both events also appeared under the `Sunday, August 30, 2026` heading for that day's actual occurrence.

Handle this with two rules:

1. **Dedup by `masterEventId` across sections.** New Events and Upcoming Events both repeat events that appear elsewhere in the same digest. Keep the occurrence with the soonest date that is not in the past.
2. **Drop any event dated before today.** It is a stale series-start date, not a real upcoming event.

Without these rules the reader is shown events that already happened.

## Timezone

Every time in the digest is America/New_York wall-clock. The digest never states this.

The reader's Outlook mailbox timezone may be something else entirely, and the `outlook_calendar_search` results will be returned in that zone. Do not use the mailbox zone to interpret digest times, and always pass `timeZone: "Eastern Standard Time"` when creating events. Windows zone names include DST rules, so that single value is correct in both EST and EDT.

## Worked example

From the digest received 2026-08-28T23:02:36Z, covering Saturday August 29:

| Title | Date | Start | End | Location | Audience |
| --- | --- | --- | --- | --- | --- |
| RC Lemonade Happy Hour Sponsored by Student Sustainability Associates | Sep 3 | 15:30 | 16:30 | Peterson Park Grille Lounge 010A (rain location) | RC Students |
| Liberty Mutual Info Sessions | Aug 29 | 12:00 | 18:00 | Virtual | EC Students |
| Liberty Mutual Coffee Chats | Aug 29 | 10:00 | 15:00 | Virtual | EC Students |
| HIO @ HBS \| Popup Hours | Sep 1 | 14:00 | 15:00 | https://harvard.zoom.us/j/92978532068 | All Students |
| Building a Skills-Based Resume | Sep 1 | 15:30 | 16:20 | Aldrich 207 | RC Students |
| Guided meditation | Sep 1 | 16:00 | 16:30 | Chapel | All Students |
| Club Fair | Sep 2 | 16:30 | 18:00 | Shad Hall Basketball Courts | All Students; Partners (ALL) |
| Social Enterprise Initiative Kick-off Presentation and Reception | Sep 3 | 17:00 | 18:30 | Batten Hall Hives 302 | RC Students |
| Q&A on the Student Sustainability Associate Role (9/3 Deadline) | Sep 3 | 17:30 | 18:00 | Zoom Link: https://hbs.zoom.us/j/98686511196?jst=1 | RC Students |

Sidebar: `Therapy dog` cancelled 09/23. `HBS Rock Entrepreneurship Day` RSVP by 09/01 at 12:00 PM.

Note the two Liberty Mutual entries. Both are EC-only, so for an RC reader they belong in the demoted "Other audiences" section, and the Coffee Chats entry is the meridiem test case: 10:00 AM, not 10:00 PM.
