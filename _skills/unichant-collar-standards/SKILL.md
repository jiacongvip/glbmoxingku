---
name: Unichant collar standards
description: >-
  Use when generating or fixing Unichant jersey FRONT 01 collars: crew rib (kits
  18/26 geometry class) or half-zip stand collar (kit 73 geometry class);
  paint-on-geometry merges; reject wrong collar templates.
---
# Unichant collar standards

Reusable geometry + paint rules for Unichant flat 2D FRONT `01` generation. Read this before any collar merge or regen.

## Core rule

**Separate geometry from paint.**

| Layer | What to lock | What NOT to copy |
|-------|----------------|------------------|
| **Geometry** | Silhouette, proportions, sleeve construction, collar *shape* (thickness, opening, rim continuity, zipper recess / garage) | Body colors, sleeve prints, collar *band color* from the geometry kit |
| **Paint** | Body/sleeve colors + pattern, collar *band fabric color*, cuff paint | Wrong collar shape from an old/tall/thin paint kit |

Always say explicitly in the prompt: geometry from IMAGE N, paint from IMAGE M, collar band color from the paint kit.

## Output defaults

- Flat 2D technical fashion flat (not soft 3D, not mannequin)
- Transparent RGBA PNG, typically **1024×1024**
- Clean chest: **no logos, text, numbers, crests, watermarks**
- Model in current pipeline: `gpt-image-2.5-sunburst` (Duomi)
- One kit / one view at a time when the user asks one-by-one; await review before the next

## Collar classes (pick one)

### A — Crew rib / short-sleeve unify (geometry masters: **18 or 26**)

**Use for:** kits in the ~17–27 short-sleeve crew line (and any crew that should match that size class).

**Geometry masters (same collar class):**

- `18-Unichant-DarkGeo` — primary template used in practice
- `26-Unichant-BlueDrip` — same class; either is OK

**Lock from 18/26:**

- Overall jersey height/width, torso length, hem
- Raglan sleeve curves, short-sleeve length
- Crew-neck collar **construction**: thickness, height, circular opening, rib band proportions
- Light **gray inner / back-of-collar** cue
- Cuff/hem edge proportions (geometry only)

**Paint from the target kit:**

- Body + sleeve colors/pattern
- Collar **band color** from that kit’s design (white, beige, yellow, etc. — whatever the paint kit has)
- Cuff paint colors

**Do NOT use as geometry for this line:**

- Kit **11** white rib — Jamie rejected (“领子不对”); wrong collar class for this unify
- Kit **18’s yellow paint** when only using 18 as geometry — discard charcoal/yellow geo paint; keep shape only

**Prompt skeleton (crew unify):**

```text
Rebuild a clean flat-front football jersey (01 product style).

IMAGE 1 = GEOMETRY MASTER (kit 18 or 26).
Copy ONLY: silhouette, torso length, raglan, short sleeves, crew collar
CONSTRUCTION (thickness, opening, rib proportions), gray inner cue,
cuff/hem proportions. Do NOT keep IMAGE 1 body/sleeve/collar paint.

IMAGE 2 = PAINT MASTER (target kit current or pre-wrong-merge 01).
Copy ALL paint onto IMAGE 1 shape: body, sleeves, pattern, collar BAND
color, cuff paint. Clean chest — no logos/text/numbers.
Ignore IMAGE 2 overall size if different; use IMAGE 1 proportions.

IMAGE 3 = design sheet (optional color/pattern check only).
Do NOT copy logos, numbers, shorts, or typography.

Critical:
1) Geometry = IMAGE 1 (18/26 class).
2) Paint = IMAGE 2 (target kit).
3) Collar band color = paint kit — never force white from kit 11,
   never keep geometry kit’s collar color if paint differs.
4) Transparent flat front, no mannequin, no text.
```

**Proven examples:**

- Kit 19 on 18: beige/tan collar band + beige body + red→orange vertical stripes
- Kit 17 on 18: white collar band + navy body + mustard center stripe
- Kit 20 on 18: white collar/cuffs + navy body + teal/pink triangle confetti

**Reference files (skill assets):** `refs/crew-18-collar.png`, `refs/crew-26-collar.png`, `refs/crew-montage-17-27.png`

---

### B — Half-zip stand collar (geometry master: **kit 73**)

**Use for:** long-sleeve half-zip kits (70+, 72–75, etc.).

**Geometry master:** `73-Unichant-TealNavySwoosh` (Jamie-approved collar/zip).

**Lock construction:**

1. Continuous **unbroken** stand-collar **TOP rim** (no center V-split, no notch, zip never cuts the rim)
2. **White** half-zip recessed under that rim to mid-chest
3. Small **triangular zipper garage/flap** at top of zip covering the pull
4. Closed flat product (collar closed; don’t draw sketch “open wing”)

**Paint from the target kit:**

- Body/sleeve colors + graphics
- Collar **fabric color** from that kit (black on 73, white on 74, magenta on 75, …)
- Zipper tape/teeth usually stay **white**; garage usually white (or matching rules stated for that kit)

**Reject (half-zip):**

- Zip cutting / splitting the top rim
- Garage flush with or only ~1 cm under the top rim when the standard needs a deeper recess
- Soft 3D / wrinkles / studio lighting when flat 2D is required
- Copying geometry kit’s body paint (e.g. teal from 73 onto 74/75)

**Prompt skeleton (half-zip):**

```text
FLAT 2D Unichant apparel FRONT only. Transparent RGBA. No soft 3D.

IMAGE 1 = PAINT (target kit sheet or current front). Keep colors/pattern;
omit logos/text/numbers.

IMAGE 2 = GEOMETRY (kit 73 full or collar crop).
Copy ONLY: continuous unbroken stand-collar TOP rim, white zip recessed
under rim to mid-chest, small triangular garage. Ignore IMAGE 2 body paint.

IMAGE 3 = kit 73 collar close-up (optional reinforce).

Output collar fabric color = from IMAGE 1 / target kit.
Zip + garage geometry = IMAGE 2/3; zipper stays white unless told otherwise.
```

**Reference files:** `refs/halfzip-73-collar.png`, `refs/halfzip-73-front.png`

---

### C — Older F-013 crew line (historical)

Earlier kits (~48–68 era) used **F-013** / kit **55** as collar geometry for teal-skeleton / collar-size fixes. Prefer class A (18/26) for the new unify-size work unless the user points back at F-013/55.

Reference: `refs/f013-front.png`, `refs/kit55-collar.png`

---

## Workflow checklist

1. Identify collar **class** (A crew 18/26, B half-zip 73, or C F-013/55).
2. Copy geometry PNG + paint PNG (+ optional sheet) into a kit work dir.
3. Write prompt with explicit IMAGE roles and “band color from paint kit”.
4. Generate → force transparent RGBA → checker preview + collar crop QA.
5. Sync Mac via OSS upload + `curl --noproxy '*'` overwrite of `01-上衣正面-2D.png`; backup old file into kit `_过程稿/`.
6. Show FRONT (+ collar crop) for review; **do not batch the next kit** until OK.

## Mac layout (example)

`/Users/jiacong/Desktop/球衣套装拆图/<NN>-Unichant-<Name>/01-上衣正面-2D.png`

## Box work dirs (example)

- Unify crew: `/workspace/kit-unify-18or26/`, `/workspace/kitNN-work/`
- Half-zip: `/workspace/halfzip-e01-e03/`
- Shared helpers: `/workspace/kit-batch-scripts/batch_lib.py`

## QA reject list

- Wrong geometry class (e.g. kit 11 white rib on 17–27 unify)
- Geometry kit’s collar color leaking when paint kit differs
- Logos / UNICHANT / numbers left on clean 01
- Opaque / checker baked into pixels (need true alpha)
- Half-zip with split rim or zip on the top edge
