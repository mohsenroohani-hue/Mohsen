# Trajectories of Point-Based, Line-Based, and Polygon-Based Spatial Analysis

A systematic review of the methodological evolution of point-, line-, and
polygon-based spatial analysis in GIScience, following PRISMA 2020
reporting principles adapted for a methodological (non-clinical) review.

- **Deliverable:** `Trajectories_of_Spatial_Analysis_Systematic_Review.docx`
- **Scope:** General GIScience / spatial statistics; "trajectories" here
  means the evolution of methods over time, not (only) movement-trajectory
  data mining, though that literature is covered under the line-based
  section.
- **Search:** 9 structured queries (2 rate-limited/failed) against the
  Consensus academic search engine (Semantic Scholar-backed corpus),
  run 28 July 2026. 140 records identified, 68 included after
  de-duplication and relevance screening. Full search strategy and
  PRISMA-adapted record-flow table are in the Methods section of the
  document itself.
- **Known limitation:** single information source (no direct Scopus/Web of
  Science/PubMed/IEEE Xplore access in this environment), single-reviewer
  screening, abstract-level (not full-text) eligibility assessment. Stated
  explicitly in the document's Limitations section — treat this as a solid
  first-pass draft to extend with a multi-database search, not a
  publication-ready final systematic review.

## Regenerating the document

The `.docx` is generated programmatically from `src/` using the `docx`
npm package (not committed; run `npm install` inside `src/` first):

```bash
cd systematic-review/src
npm install
node main.js
```

This writes `Trajectories_of_Spatial_Analysis_Systematic_Review.docx` into
`src/`; move it up to `systematic-review/` to replace the committed copy.

- `refs.js` — the 68-entry reference list (label, citation text, source URL)
- `build.js` — title block, abstract, introduction, methods (incl. the two
  summary tables)
- `build2.js` — results, discussion, limitations, conclusion
- `main.js` — assembles all sections into the final `Document` and writes
  the `.docx`
