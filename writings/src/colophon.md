---
title: colophon.
date: 2026-09-09
standfirst: how this site is set.
---

It is all static files: no build server, no framework, and nothing running on
the page except the spread viewers, which have to size a book to whatever window
it lands in.

## the faces

Titles are set in [Redaction 35](https://www.redaction.us/), drawn by Forest
Young and Jeremy Mickel for an exhibition at MoMA PS1. It is released under the
Open Font License, so it is served from this domain rather than borrowed from a
CDN.

Body text is Plantin MT Pro Light, and no file for it is served from here.
Plantin is licensed for the desktop, so it appears only for readers who already
have it installed. Everyone else gets Times New Roman, which is a closer
relative than it sounds: Times was drawn from Plantin in 1932, so the fallback
is the original's own descendant rather than a substitute.[^1]

[^1]: Stanley Morison's brief to Victor Lardent at *The Times* used Plantin as
the starting point, narrowed and sharpened for newsprint.

Sizes come from six steps and nothing sits between them: 22, 16, 14, 12.5, 11
and 10.5 pixels. Spacing runs on a single rhythm. Both are variables, so a
change is one edit rather than forty.

## the pages

The two link colours are the browser defaults, `#0000ee` and `#551a8b`, and they
carry fixed meanings: blue is something you can open, purple something you have.
Interface chrome is exempt, because a back link points at a page you have by
definition already seen.

> Hairlines do the separating. Nothing has a shadow, a gradient, or a rounded
> corner except an image.

The portfolios are PDFs rendered to WebP at three resolutions, one to read, one
to zoom into, one for the index, and their hyperlinks are lifted out of the PDF
and laid back over the page, so a reference printed in blue is still a reference
you can follow.

## writing

Pieces like this one are markdown files. They support what an essay needs:

- headings, emphasis, and inline links
- footnotes, which collect under a rule at the end
- block quotes, lists, and tables
- images with captions

