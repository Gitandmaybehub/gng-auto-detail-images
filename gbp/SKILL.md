---
name: gng-gbp-autopost
description: Every-2-days GNG Auto Detail Google Business Profile post, through the Google API only, no browser and no screen control. Picks the next town from gngautodetail.com and the next real job photo, writes one short post in Christian's style, runs safety checks, and sends it to his Telegram bot (GNGVABot) as a card with Send, Edit, Skip. Nothing posts without his tap. Use when asked about the auto post, the every-2-days Google post, the town-rotation post, or the Google post cards in Telegram.
---

# GNG automatic Google post (API, cloud safe)

## The goal

Every 2 days, one short post goes up on the GNG Auto Detail Google Business Profile:
- one real job photo,
- one town from gngautodetail.com, a new town each time,
- written like Christian writes, and honest.

**Every post waits for Christian's tap.** The draft shows up in his Telegram bot GNGVABot (his phone calls it "Booking Bot") as a card with the photo and three buttons: Send, Edit, Skip. Send posts it. (His ask, 2026-09-28.)

It runs through the Google API. It never opens a browser and never controls a computer.

## How it runs

- The inbox robot on the Mac mini (`com.gng.inbox`) makes the card. Code: `~/GNG/gng-assistant/gv-bridge/gbp_post.py`, called from the loop's chores.
- Once 40 hours have passed since the last post, it drafts at a different time each day between 9:00 am and 1:30 pm.
- Its AI (the bot's own model) looks at the photo and writes the post with the rules below, then this folder's checks run on it.
- Send: posts with that town and photo, then the card changes to "Sent" with the post link.
- Send too soon (under 40 hours since the last post): his approved text waits and posts itself at the next draft time. The card says when. He gets a Telegram message with the link once it is live.
- Edit: he fixes the words and sends them back; his text is what posts.
- Every Edit teaches it: the bot saves a one-line lesson from his change in `~/GNG/gng-assistant/references/google-posts/LESSONS.md` (separate from the texting lessons) and reads all of them, plus his before and after examples, before every new draft. Any agent writing a GNG post should read that file too.
- Skip, or no tap for a day: nothing posts. A fresh draft comes the next day.
- Make a card right now: `cd ~/GNG/gng-assistant/gv-bridge && ../.venv/bin/python gbp_post.py now`. Add `--force` for a preview when it is too soon (Send will then be refused by the 40 hour rule).

## Where things are

Everything lives in the public repo `Gitandmaybehub/gng-auto-detail-images`, folder `gbp/`:

| File | What it is |
|---|---|
| `SKILL.md` | This file |
| `autopost.py` | Plain Python 3, no installs. `plan`, `post`, `list` |
| `towns.json` | The 62 towns that have a live page on gngautodetail.com, closest to Cedar Knolls first |
| `photos/` | 23 approved job photos, sized for Google, location data removed |

On the Mac mini the same folder is `~/GNG/gng-auto-detail-images/gbp`. There, run it with `/usr/bin/python3` (the other Python on that Mac has a certificate problem).

Google login: the script reads `GBP_CLIENT_ID`, `GBP_CLIENT_SECRET`, `GBP_REFRESH_TOKEN` from the environment. On the Mac mini it falls back to `~/GNG/gng-gbp-auto2/token.json`. Never print, echo, or save these values.

## The steps

1. `python3 gbp/autopost.py plan`
2. If `"due": false`, stop. Report "Not due yet, last post was X hours ago." Do not post.
3. Open the photo at `photo_local_path` and look at it. Note what is really in it: the car, the area (front seats, back seats, trunk, carpet, mats, wheel), and the result.
4. Read `last_10_posts`. Do not reuse their first line, their service, or their wording.
5. Write the post using the wording rules below. Use the `town` from the plan.
6. Dry run: `python3 gbp/autopost.py post --town "<town>" --photo "<photo>" --text "<text>" --dry-run`
7. If it says NOT POSTED, fix what it lists and dry run again.
8. Never post without Christian's yes. On the Mac mini, run `gbp_post.py now` (above) so he gets the card. Anywhere else, show him the exact text and photo and wait for a yes, then run the command without `--dry-run`.
9. It waits 20 seconds and prints the post state. `LIVE` or `PROCESSING` is success. On `REJECTED`, cut the likely trigger (a number, a word that could look spammy) and try once more. If it fails again, stop and report it.
10. Report in 3 lines: the exact text, the town, the photo, and the post link.

No standing permission. Every post needs his tap or his yes (2026-09-28).

## The wording

His own post from 2026-09-28 is the model:

```
Inside Freshened Up For One Of Our Regulars 👍  Top Rated Detailing In Morris County! Salt Removal, Stain Extraction, And Paint Correction At Your Location! ✅
```

The shape:
1. A short line about what the photo really shows, then one emoji (👍 😄 🔥 💯).
2. The town, in the first 100 characters, said as where we serve. For example "Mobile Detailing In Whippany And All Of Morris County!"
3. One or two real services from the website that fit the photo.
4. End with ✅.

Rules:
- 150 to 300 characters. One topic per post.
- Title Case Every Word.
- He likes ! over periods. One ! at a time, never !!.
- Casual North Jersey shop guy. Short. No AI filler words ("elevate", "look no further", "it means the world").
- Write it fresh from the photo each time. Never fill in a template where only the town changes. Google says auto-generated posts break its rules.

Good (honest service area):
`Back Seats Looking Brand New Again 👍 Mobile Interior Detailing In Whippany And All Of Morris County! Pet Hair And Stains Pulled Right Out At Your Driveway ✅`

Bad (makes up where the job was):
`Just Finished This Car In Whippany!` The photos are not tagged by town. Never say a pictured job happened in the post's town.

## Honest facts only

Services you may name (all on gngautodetail.com): interior detailing, exterior detailing, full detail, hand wash, paint correction, paint polishing, ceramic coatings, headlight restoration, leather conditioning, pet hair removal, stain removal or stain extraction, carpet shampoo, steam cleaning, odor removal, salt removal, water spot removal, trim restoration, surface protection, mold remediation, lease return detailing, Tesla and EV detailing, the maintenance plan, apartment and condo detailing, drop off detailing in Cedar Knolls.

Never:
- a phone number, email, website, link, handle, or street address in the text. Google started removing posts with contact info on 2026-09-25. The button carries the link.
- a dollar price. The only money offer is the $20 / $20 referral.
- a long dash of any kind.
- made-up customers, reviews, stories, offers, events, awards, or numbers.
- more than one town in a post.
- a car make or model you cannot see in the photo.

## The button

`autopost.py` sets it. Default `LEARN_MORE` to that town's page, for example `gngautodetail.com/whippany`, with tracking tags (`utm_source=google&utm_medium=organic&utm_campaign=gbp_post&utm_content=<date>-<town>`). Tracking tags are extra words on a link that tell Google Analytics the click came from this post.

Why the town page and not the homepage: AI answer engines read web pages, not posts. Sending the click to the matching town page ties the post, the town, and the page together.

`--cta BOOK` sends the button to `gngautodetail.com/book` instead. Use it when the post is about booking.

## What the research says (2026-09-28)

Short version: posts do not raise his Maps rank. They win clicks and trust from people who already see him.

- **Tested: no direct ranking boost.** Sterling Sky posted weekly on 3 profiles for 9 weeks, tracked 441 keywords each, saw no change. Whitespark's 2026 survey ranks post factors near the bottom (#155 to #168 of about 187). https://www.sterlingsky.ca/do-google-posts-impact-ranking/ , https://whitespark.ca/local-search-ranking-factors/
- **Tested: posts feed "justifications".** Those are the small quote lines under a listing in the map results. They pull from posts made in the last 60 days, show up within minutes, and favor short one-topic posts. They can raise clicks. This is why a steady rhythm with the service and town words in the text matters. https://www.brightlocal.com/learn/google-business-profile-justifications/
- **Town names: unproven for rank.** Distance still wins. A town name can show as a justification when he already ranks there.
- **AI answers (GEO, AEO): posts are not a proven source.** GEO means showing up in AI answers. AEO means writing so an AI can lift your answer. ChatGPT has no link to Google profiles. Google's AI answers cite web pages. So the button goes to the town page, where the real AI value is. https://www.localfalcon.com/blog/chatgpt-local-search-data-sources-where-does-business-info-come-from
- **Myth: photo GPS tags.** Tested with no gain, and Google strips them. Our photos have them removed for customer privacy. https://www.sterlingsky.ca/geotagging-photos-impact-ranking/
- **Rejections:** phone numbers, links, addresses, and some words get posts removed. https://www.sterlingsky.ca/rejected-google-posts/ , https://www.seroundtable.com/unverified-contact-information-google-posts-42159.html
- **API limits:** photo only (no video through the API), one photo per post, 1,500 characters max, posts older than 6 months get archived.
- **What really moves rank and AI answers:** reviews, a page for each service and town, and matching listings on Bing Places, Apple, and Yelp. See skill `gng-seo-geo-aeo`.

## Photos

Only files in `gbp/photos/`. Rotation: every photo gets used once before any repeat. `plan` picks it; do not swap it unless the photo clearly does not match any service you can name.

Adding a new photo: a real GNG job photo, after shot, no license plate, no faces of former crew (never Nick or Justin), no AI edits. Resize to 1600 pixels on the long side, strip location data, add it to `gbp/photos/`, commit, push. The file must be on GitHub before Google can fetch it.

## If something breaks

| Message | What it means | What to do |
|---|---|---|
| `NO GOOGLE LOGIN` | The 3 GBP_ env values are missing | Christian adds them to the cloud environment (see below) |
| `GOOGLE LOGIN FAILED` | The saved Google login died | Stop. Christian re-authorizes, see `gng-gbp-posting/references/oauth-recovery.md` |
| `GOOGLE ERROR 403` | Network or permission block | In the cloud: set network access to Full, or allow `oauth2.googleapis.com`, `mybusiness.googleapis.com`, `raw.githubusercontent.com` |
| `NOT POSTED. Last post was N hours ago` | Too soon | Normal. Stop |

Never fall back to a browser from a cloud routine. The browser way is skill `gng-gbp-autopost-browser`, for Grok Bot and OpenMausBot on the Mac only.

## Cloud routines (paused)

- Three Claude Code cloud routines were made on 2026-09-28 ("GNG Google post A, B, C") and switched off the same day, because he wants to approve every post and only the Mac mini's bot can show him a card. They are safe to delete at claude.ai/code/routines.
- A cloud run would need `GBP_CLIENT_ID`, `GBP_CLIENT_SECRET`, `GBP_REFRESH_TOKEN` in its environment. None are set.

- Codex or any other agent can use the same steps, but must still get his yes before posting.
