# Serve an unlimited number of models

## Problem
`cmd_serve` JSON-encodes every model path into the viewer URL query string
(`?files=...`). With 2620 models that URL is ~500KB, which blows past both the
browser URL cap and Python `http.server`'s 65536-byte request-line limit, so the
page never loads.

## Fix (Approach A)
Stop passing the list through the URL. Serve it as a JSON endpoint the viewer
fetches at load time.

- **Server** (`gltf_catalog.py`): `Handler` gains a `/_files.json` route that
  returns the paths list (held in memory). The launch URL keeps only
  `?page_size=N`, so it stays tiny regardless of model count.
- **Viewer** (`viewers/grid_viewer.html`): replace the `?files=` parse with
  `await fetch('/_files.json')`. Paging logic is unchanged.

## Result
URL length is constant. Model count is bounded only by browser memory for the
path list (fine for hundreds of thousands). No new dependencies.

## Out of scope
Server-side pagination (only needed at ~100k+ models).
