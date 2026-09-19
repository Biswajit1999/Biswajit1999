# Profile evidence contract

This repository is a routing and communication layer. It does not create new
astrophysical measurements. Its research-quality obligation is to connect
profile claims to the strongest available versioned evidence without implying
that every linked repository has reached the same maturity.

## Completion rule

A project appears in the verified table only when the central Top-50 programme
records a scoped research question, generated result, explicit limitation,
automated validation, public release, and live-link verification. Other profile
links remain useful for discovery but are not upgraded by association.

## Evidence architecture

- `data/profile-evidence.json` is the human-reviewed source snapshot.
- `scripts/build_evidence_index.mjs` validates the schema and deterministically
  generates `EVIDENCE.md`, the maturity CSV, and the accessible SVG graph.
- `scripts/validate_repository.mjs` verifies README disclosure and release
  traceability.
- `tests/profile-evidence.test.mjs` checks schema, output freshness, release
  identity, uniqueness, boundaries, and discovery-versus-evidence language.
- CI runs the full validation on Node.js 24.

The snapshot is pinned to central evidence registry `v2026.09.19.3`. Updating
the registry does not silently change this profile: the source snapshot and all
generated artifacts must be reviewed, regenerated, tested, and committed.

## Maturity result

The documented rubric rises from **36/100 before to 95/100 after** across eight
equal-weight dimensions. The largest changes are release traceability,
automated verification, reproducibility, and claim boundaries. See
`docs/BASELINE_AUDIT_V1_1.md` for the scoring basis and
`data/profile-evidence-maturity.csv` for the machine-readable values.

## Boundaries

- Scores assess auditable research communication, not scientific merit,
  originality, correctness, peer review, citations, or applicant ranking.
- Routed findings inherit the assumptions and limitations of their source
  releases; the concise profile wording is not a substitute for those records.
- Education, internships, publications, skills, and collaboration status are
  biographical profile statements. This repository does not independently
  verify them.
- Contribution graphs, badges, animations, and repository activity are
  presentation or activity signals, not scientific evidence.

## Reproduce

```bash
npm install
npm run build:evidence
npm run check
```

`npm run build:evidence` is the only command that rewrites generated evidence.
`npm run check` is read-only and fails if any generated artifact is stale.
