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
When reduced motion is preferred, entrance effects, scaling, logo translation
and particle translation stop. Opacity changes continue: the logo glows,
the gold frame breathes, active calendar cells pulse, and the calendar
wave runs through a sequence of stationary column outlines. This
keeps the owner's requested ambient animation without spatial movement.
Final content remains visible when CSS animation is unavailable.

## Change the logo

`assets/salva-source.png` is the original Salva Systems image from the account
avatar. Rebuilding the ASCII logo requires Pillow:

```sh
python -m pip install Pillow
python scripts/make_logo.py
```

The logo generator converts luminance to monochrome ASCII. Dark background
pixels become spaces. It reveals the rows over 5.8 seconds, then floats gently
in a nine-second loop. A separate opacity loop keeps running, including on
cached images after the entrance finishes. Replacing the avatar in GitHub does not automatically
replace this committed source image.

## Edit profile content

Update `README.md` for role, stack, project links and contact information.
SVG labels and palette live in `scripts/render_profile.py`. Changing that
file triggers regeneration on the next push to `main`. Changes to the logo
generator require running `python scripts/make_logo.py` locally and committing
the resulting SVG as well.

The logo and statistics retain 840 × 880 content rectangles inside matching
904 × 944 viewboxes. The 32px gutter on every side contains the gold particles without
covering content. Both display at 420px each. Inline images sit side by side on desktop and wrap into separate
rows when the available width is smaller. The full-width calendar displays at 860px.
The SVG backgrounds retain contrast in light and dark GitHub themes. For
mobile viewers, the prose below the artwork repeats the role, stack, projects
and links in selectable, readable text.

## Continuous motion and readable metrics

Public labels and profile prose use Spanish. Only the ASCII logo uses a
monospaced font; card labels use a readable sans-serif family.

Each metric displays one final value. Numbers do not cycle, scroll or overlap;
only the outer border loops continuously. Integer metrics remain integers;
the daily average uses one decimal. Calendar pulses affect only days with
real public activity, retaining their original color levels and counts.
The six-second gold scan outlines calendar columns without changing their
fills. The wave remains conspicuous with reduced motion because its stationary
outlines animate only opacity. It also runs for a calendar with no activity;
it is decorative, not an indication of contributions.

`gold_border()` draws the same vector frame around all three graphics.
A solid gold base remains fully visible at all times. Layered halo strokes
and a fine highlight slowly brighten and dim over six seconds; no keyframe
hides the base outline. Small gold particles emerge from all four edges and
travel outward over seven to ten seconds. Negative delays stagger their
cycles so ambient motion is visible without reloading the page. Particle
positions and travel stay within the 32px gutter, clear of content.

All frame artwork is inline SVG: no raster textures, external images,
JavaScript or filters. With reduced motion, particles are hidden and the
frame keeps its soft opacity cycle. To change the frame, edit
`scripts/render_profile.py`, regenerate the logo locally with `make_logo.py`,
and regenerate data graphics with `update_profile.py`. Commit all three SVGs.
The daily data workflow remains dependency-free.

Published assets are `salva-gold-aura.svg`, `github-gold-aura.svg`, and
`contributions-gold-aura.svg`. README, generators and the daily workflow must keep
these paths aligned. These distinct paths replace older cached artwork.
Reloading an image is not guaranteed to restart its entrance sequence; ambient
loops provide visible motion after the entrance has completed.

## Project presentations

The profile links to public presentations for Salva Systems, Aplomo, ATENOR,
Careertrackly, UFlex, SalvaOps, RUNIIS and Archivo STEAM. Public documentation
does not imply that a repository contains the entire product implementation.
Private implementation repositories remain private. Product descriptions and
development stages reflect the owner's October 2026 inventory.

The GitHub-native contribution activity section is controlled by account
settings, not the README. The owner chose to keep the account profile public;
private contribution counts are not publicly shared.
