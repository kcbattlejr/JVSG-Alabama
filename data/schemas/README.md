# Data schemas

Store versioned schemas for synthetic GeoSol extracts and TOON payloads here.
Do not add real exported records or schemas containing live personal data.

`mis_reports.v1.json` is the header-only native MIS download contract: a
46-column anti-join CSV and a 12-column case-notes XLSX. It contains no sample
values. Generate it from `python -m jvsg_triage.etl schema`; the synthetic
tests assert exact agreement with the typed contracts.

See [native MIS intake](../../docs/mis_intake_contract.md) for field mappings,
title-row discovery, privacy boundaries and deliberately unmapped fields.
