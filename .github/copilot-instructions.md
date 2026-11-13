# JVSG-Alabama contributor guidance

- Never add real veteran names, SSNs, raw SIDs, case notes, or live GeoSol
  exports to source control, tests, logs, prompts, or generated artifacts.
- Keep secrets out of code and tracked configuration. Read them from approved
  environment configuration or secret stores.
- Use synthetic fixtures for development and tests.
- Use invented demo distributions, not private cohort profiles or validation
  metrics. Do not publish local infrastructure inventories or named internal
  account assignments. Follow `SECURITY.md` before publishing artifacts.
- Keep case interpretation and referral decisions subject to qualified human
  review; model output is not an authoritative decision.
- Prefer typed, deterministic Python and vectorized Polars operations for
  tabular processing.
- Keep integrations optional and avoid network calls during import or tests.
- Add focused tests for behavior and boundary conditions when implementing a
  project module.
