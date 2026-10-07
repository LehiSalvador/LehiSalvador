# Maintaining the Salva Systems profile

The README places three self-contained animated SVGs: a branded ASCII logo,
a contribution calendar, and a statistics card. They use no JavaScript,
external fonts, tracking or hosted statistics services.

## Refresh calendar and statistics

Python 3.12 or newer is sufficient; no pip packages are required.

```sh
python -m unittest discover -s tests -v
python scripts/update_profile.py
```

The `Refresh animated profile` action also runs daily at approximately 02:23
in America/Mexico_City and can be run from the Actions tab. GitHub schedules
can be delayed. Scheduled workflows in inactive public repositories can be
disabled after 60 days; re-enable from Actions if necessary.

The workflow uses the repository's automatic `GITHUB_TOKEN` with
`contents: write`. No personal access token is needed. A rejected request,
unexpected HTML, incomplete calendar or unrecognized tooltip fails the run;
the last committed artwork remains visible. A valid response must cover
365–373 consecutive days, start at the annual calendar's Sunday boundary
and end today or yesterday in UTC. Results are generated before
files are replaced. The source snapshot records its UTC generation time.

Data is the public calendar GitHub exposes for LehiSalvador. Its counts can
include anonymized private activity if the account publicly shares that
activity. This code never accesses private repositories. Numbers update
when the workflow runs; they are not a real-time dashboard.

Current streak tolerates a zero-count unfinished day. The longest streak,
best day and monthly bars cover the displayed calendar period, not the
account's entire history. Partial first and last months remain partial.
All three SVGs show their final content when reduced motion is preferred.

## Change the logo

`assets/salva-source.png` is the original Salva Systems image from the account
avatar. Only regeneration of the logo requires Pillow:

```sh
python -m pip install Pillow
python scripts/make_logo.py
```

The logo generator converts luminance to monochrome ASCII. Dark background
pixels become spaces. It reveals the rows over 5.8 seconds and settles into
a static final frame. Replacing the avatar in GitHub does not automatically
replace this committed source image.

## Edit profile content

Update `README.md` for role, stack, project links and contact information.
SVG labels and palette live in `scripts/render_profile.py`. Changing that
file triggers regeneration on the next push to `main`. Changes to the logo
generator require running `python scripts/make_logo.py` locally and committing
the resulting SVG as well.

The logo and statistics have matching 840 × 880 viewboxes and display at
420px each. Inline images sit side by side on desktop and wrap into separate
rows when the available width is smaller. The full-width calendar displays at 860px.
The SVG backgrounds retain contrast in light and dark GitHub themes. For
mobile viewers, the prose below the artwork repeats the role, stack, projects
and links in selectable, readable text.

## Labels and counter animation

Public labels and profile prose use Spanish. Only the ASCII logo uses a
monospaced font; card labels use a readable sans-serif family.

Each metric uses a single clipped column of values, advanced by one CSS
stepped translation. The clip is shorter than the distance between rows,
so two numbers cannot occupy the visible window at the same time. Integer
metrics keep integer intermediate values; only the daily average uses one
decimal. Units remain at a fixed position outside the counter column.
Both SVG transform attributes and reduced-motion styles retain final values.

## Project presentations

The profile links to public presentations for Salva Systems, Aplomo, ATENOR,
Careertrackly, UFlex, SalvaOps, RUNIIS and Archivo STEAM. Public documentation
does not imply that a repository contains the entire product implementation.
Private implementation repositories remain private. Product descriptions and
development stages reflect the owner's October 2026 inventory.

The GitHub-native contribution activity section is controlled by account
settings, not the README. The owner chose to keep the account profile public;
private contribution counts are not publicly shared.
