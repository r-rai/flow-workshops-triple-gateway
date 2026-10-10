# Flo Bank workshop presentations

Four editable 16:9 PowerPoint decks, matching PDF handouts, and presenter notes.
The decks follow the repository's current workshop stories and participant worksheets.
All bank scenarios are fictional. Expected outcomes are teaching targets, not new lab measurements.

| Workshop | Duration | PowerPoint | PDF | Presenter notes |
|---|---:|---|---|---|
| 1 — Give Flo the right tools | 45 min | [Deck](flo-bank-workshop-1.pptx) | [Handout](flo-bank-workshop-1.pdf) | [Notes](flo-bank-workshop-1-notes.md) |
| 2 — The ticket that tried to give orders | 45 min | [Deck](flo-bank-workshop-2.pptx) | [Handout](flo-bank-workshop-2.pdf) | [Notes](flo-bank-workshop-2-notes.md) |
| 3 — The resolver that remembered | 45 min | [Deck](flo-bank-workshop-3.pptx) | [Handout](flo-bank-workshop-3.pdf) | [Notes](flo-bank-workshop-3-notes.md) |
| 4 — Gateways + The day the agent broke the bank | 15 min primer + 135 min lab | [Deck](flo-bank-workshop-4.pptx) | [Handout](flo-bank-workshop-4.pdf) | [Notes](flo-bank-workshop-4-notes.md) |

[Download all four decks, PDFs, notes and editable generation sources](flo-bank-all-workshops.zip).

Speaker notes are embedded in every PowerPoint slide and supplied as Markdown.
They include demo cues, segment timings, limitations, and repository source paths.
The final slide in each deck is a preparation/reference appendix outside the timed agenda.
W4 includes the seven-minute break within its 135 minutes.

W4 now begins with API, AI, and MCP gateway capabilities and request lifecycles,
then an editable Triple-Gate architecture diagram and audience QR slide before
the incident-response lab. The repository deck shows **Provided live by
facilitator** instead of a live access code. Download its
[QR image](w4-audience-qr.png) or [W4 package](flo-bank-workshop-4-package.zip).
The QR encodes only the audience URL; observers enter their event code separately.
Phones inspect curated recorded evidence and cannot approve or execute payments.

Install/build the lab before the session. Run only one workshop profile at a time.
Use the worksheets for setup and copyable commands. Creating these decks does not run,
reset, rehearse, or modify the workshop services. Preserve prior evidence before any
reset and use the workshop answer keys for potentially destructive rehearsal setup.

PowerPoint text and diagrams are editable. DejaVu Sans and DejaVu Sans Mono are
used; install those fonts for the closest appearance. PDFs embed their fonts.
The PDF handouts use the same content and geometry but are rendered independently;
they are not exports from PowerPoint. This environment has no PowerPoint/LibreOffice
renderer, so check the PPTX in your presentation app before delivery, especially
if fonts are substituted or slides are edited.

## Regenerate

Use Python 3.12 with the dependencies in [requirements.txt](requirements.txt).
The generator expects DejaVu fonts under `/usr/share/fonts/truetype/dejavu/`;
adjust `FONTDIR` in `build.py` for another platform.

```bash
python3 -m venv /tmp/flo-presentation-env
/tmp/flo-presentation-env/bin/pip install -r docs/workshops/presentations/requirements.txt
/tmp/flo-presentation-env/bin/python docs/workshops/presentations/build.py
```

Edit [content.py](content.py) for slide copy and notes; edit [build.py](build.py)
for layout. W4's primer and additional guidance are in [w4_primer.py](w4_primer.py).
Rebuilding replaces generated outputs in this directory.
The generator reopens PPTX files, checks package integrity, checks source paths
and notes, checks text/shape bounds, verifies PDF page counts, and creates
[validation.json](validation.json) plus contact sheets in `previews/`.
These checks validate presentation artifacts, not live lab execution.

### Workshop 4 only

```bash
/tmp/flo-presentation-env/bin/python docs/workshops/presentations/build.py --workshop 4
```

### Event copy with the audience access code

The hosting operator prepares the audience-code file separately. It is distinct
from `W4_REVIEWER_PASSWORD`; never put the reviewer or sandbox secret on a slide.
Generate a keyed event deck outside the repository so the active code is not
committed or included in the reusable all-workshops bundle:

```bash
/tmp/flo-presentation-env/bin/python docs/workshops/presentations/build.py \
  --workshop 4 \
  --output-dir /tmp/flo-w4-event/presentation \
  --audience-key-file /tmp/flo-w4-event/access-code.txt \
  --audience-expiry '12:00 IST · 10 October 2026'
```

Use the actual configured event expiry. This command generates slides only; it
does not rotate the hosting key or change the server cutoff. The event output
includes PPTX, PDF, notes, a package ZIP, and previews. Store the event copy
somewhere durable before `/tmp` is cleaned. The repository copy remains reusable.

The presentation regressions use the slide requirements plus optional OpenCV for
decoding the QR image:

```bash
/tmp/flo-presentation-env/bin/python -m pip install opencv-python-headless==4.12.0.88
/tmp/flo-presentation-env/bin/python -m unittest discover -s tests -p test_w4_presentation.py
```
