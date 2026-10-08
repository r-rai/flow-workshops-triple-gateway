# Flo Bank workshop presentations

Four editable 16:9 PowerPoint decks, matching PDF handouts, and presenter notes.
The decks follow the repository's current workshop stories and participant worksheets.
All bank scenarios are fictional. Expected outcomes are teaching targets, not new lab measurements.

| Workshop | Duration | PowerPoint | PDF | Presenter notes |
|---|---:|---|---|---|
| 1 — Give Flo the right tools | 45 min | [Deck](flo-bank-workshop-1.pptx) | [Handout](flo-bank-workshop-1.pdf) | [Notes](flo-bank-workshop-1-notes.md) |
| 2 — The ticket that tried to give orders | 45 min | [Deck](flo-bank-workshop-2.pptx) | [Handout](flo-bank-workshop-2.pdf) | [Notes](flo-bank-workshop-2-notes.md) |
| 3 — The resolver that remembered | 45 min | [Deck](flo-bank-workshop-3.pptx) | [Handout](flo-bank-workshop-3.pdf) | [Notes](flo-bank-workshop-3-notes.md) |
| 4 — The day the agent broke the bank | 135 min | [Deck](flo-bank-workshop-4.pptx) | [Handout](flo-bank-workshop-4.pdf) | [Notes](flo-bank-workshop-4-notes.md) |

[Download all four decks, PDFs, notes and editable generation sources](flo-bank-all-workshops.zip).

Speaker notes are embedded in every PowerPoint slide and supplied as Markdown.
They include demo cues, segment timings, limitations, and repository source paths.
The final slide in each deck is a preparation/reference appendix outside the timed agenda.
W4 includes the seven-minute break within its 135 minutes.

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
for layout. Rebuilding replaces generated outputs in this directory.
The generator reopens PPTX files, checks package integrity, checks source paths
and notes, checks text/shape bounds, verifies PDF page counts, and creates
[validation.json](validation.json) plus contact sheets in `previews/`.
These checks validate presentation artifacts, not live lab execution.
