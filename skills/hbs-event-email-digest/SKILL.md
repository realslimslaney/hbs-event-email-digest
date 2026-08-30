---
name: hbs-event-email-digest
description: Read the daily HBS Student Event Calendar digest email, show a filtered brief of what is worth attending, and add the events the user picks to their Outlook calendar. Use when the user asks about HBS student events, campus events, the event calendar, what is happening today or this week on campus, RSVP deadlines, or types /hbs-event-email-digest.
---

# HBS Student Event Calendar digest

Turns the daily Student Event Calendar email into a short, filtered brief, then adds the events the user picks to their Outlook calendar.

Requires the **Microsoft 365 connector** on claude.ai. Every step here uses `mcp__claude_ai_Microsoft_365__*` tools. If those tools are unavailable, say so plainly and stop; there is no fallback.

The full parsing contract, with a worked example, is in `reference/digest-format.md`. Read it before parsing your first digest of the session.

## 1. Identify the reader

Call `get_me`. Take the `mba{YYYY}` segment of `userPrincipalName` (for example `bslaney@mba2028.hbs.edu` gives class year 2028).

Derive the audience. The HBS academic year starts in August, so the current academic year begins in `AY` = current year if the month is August or later, otherwise the previous year:

- `classYear - AY == 2` means the reader is **RC** (first year).
- `classYear - AY == 1` means the reader is **EC** (second year).

Relevant audiences are then the reader's own year plus `All Students`. If the class year cannot be determined, treat every audience as relevant and say which assumption you made.

A config file at `hbs-event-email-digest.config.json` in the user's Claude config directory overrides all of this. Read it if it exists; do not create it or error if it is missing.

## 2. Fetch the digest

```
outlook_email_search(sender: "noreply@hbs.edu", afterDateTime: "2 days ago", order: "newest", limit: 5)
```

Then filter the results client-side for subject containing `Student Event Calendar Daily Digest`.

Do **not** pass `query` together with `order`. The tool documents them as incompatible and the results become relevance-ranked rather than newest-first.

Read the newest match in full:

```
read_resource(uri: "mail:///messages/{id}")
```

The HTML is in `body.content`. If no digest arrived in the window, say so and stop. If the only digest available is more than a day old, use it but label it clearly as stale with its actual date.

## 3. Parse

Follow `reference/digest-format.md`. Produce one record per event:

`{ masterEventId, title, date, startET, endET, location, audience, detailUrl, section }`

Five rules that will silently produce wrong output if skipped:

- **Unwrap safelinks.** Take the `url=` query parameter and URL-decode it to recover `https://beech.hbs.edu/eventCalendar/user/eventDetail.do?masterEventId=NNNNN`. Never show the reader a `safelinks.protection.outlook.com` URL.
- **Infer the missing meridiem.** Start times omit AM/PM: `10:00 - 3:00 PM` is 10:00 AM to 3:00 PM. Parse the end time, which always carries the meridiem, then pick the start meridiem giving the shortest non-negative duration.
- **All times are Eastern.** The digest is always America/New_York wall-clock, regardless of the reader's mailbox timezone.
- **Dedup by `masterEventId` within the digest, then drop anything dated before today.** New Events and Upcoming Events repeat events listed elsewhere, and recurring events are listed under Upcoming Events with a series-start date that is frequently in the past. Keep the soonest occurrence that has not already happened.
- **An empty sidebar block is not an absent one.** Cancelled Events renders `There are no new cancelled student events.` with an empty list. Check for list items, and omit the section rather than echoing that sentence.

## 4. Dedup against the calendar

```
outlook_calendar_search(query: "*", afterDateTime: <earliest digest date>, beforeDateTime: <latest digest date + 1 day>, order: "oldest", limit: 25)
```

Page through with `nextOffset` if there are more results. An event counts as already on the calendar if either:

- an existing event body contains `masterEventId=NNNNN` for that event (added by this skill before), or
- an existing event has a matching title and the same start time (added by hand, by Copilot, or by an organizer invite).

Mark these as already present. Do not hide them and do not offer them for adding.

## 5. Render the brief

Lead with a one-line summary of the day, then these sections. Number events continuously across sections 1 and 2 so the reader can refer to them.

1. **Today** and **New events**, filtered to relevant audiences.
2. **Coming up**, filtered to relevant audiences.
3. **RSVP deadlines**, from the Upcoming to Do sidebar, with the cutoff called out.
4. **Cancelled**, from the Cancelled Events sidebar. For each, check whether it is on the reader's calendar and say so, since those need removing.
5. **Other audiences**, one compact line per event that the audience filter dropped (EC-only, Partners). Demote, never discard.

Format each event as:

```
3. Club Fair
   Wed Sep 2, 4:30 - 6:00 PM | Shad Hall Basketball Courts | All Students; Partners
   https://beech.hbs.edu/eventCalendar/user/eventDetail.do?masterEventId=205351
```

Mark already-present events with a leading checkmark and no number, so they are visible but not selectable.

Skip empty sections rather than printing an empty heading. If the digest says there are no student events, say that in one line.

End by telling the reader they can add events by number.

## 6. Add the events the reader picks

Accept `add 2, 5, 7`, ranges like `add 2-4`, and `add all`. `add all` means every numbered event, not the demoted ones.

For each pick:

```
outlook_create_event(
  subject: <title>,
  start: { dateTime: "YYYY-MM-DDTHH:MM:00", timeZone: "Eastern Standard Time" },
  end:   { dateTime: "YYYY-MM-DDTHH:MM:00", timeZone: "Eastern Standard Time" },
  location: <location>,
  body: "<detailUrl>\n\nAudience: <audience>\nAdded from the HBS Student Event Calendar digest.\nmasterEventId=<NNNNN>",
  bodyType: "text",
  showAs: "free",
  responseRequested: false
)
```

Non-negotiable details:

- **Always pass `timeZone: "Eastern Standard Time"`.** Never omit it and never use the mailbox default. The Windows zone name carries the DST rules, so this is correct year round.
- **Never add attendees.** These are informational holds, not invitations. Adding attendees emails real people.
- **`showAs: "free"`** so campus events do not make the reader look busy to classmates checking availability.
- Keep the `masterEventId=` line in the body verbatim. It is what makes future runs dedup correctly.

Never create an event the reader did not explicitly pick.

Confirm each one created, with its `webLink`. If a create fails, report which one and keep going with the rest.

## Timezone warning

If the mailbox timezone is not Eastern (visible in the `timeZone` field returned by `outlook_calendar_search`), mention once per session that events will be stored correctly but will *display* shifted in Outlook until the reader changes their Outlook timezone setting. Do not change the setting for them; it is an account-level setting.
