# Data schemas

Store versioned schemas for synthetic GeoSol extracts and TOON payloads here.
Do not add real exported records or schemas containing live personal data.

`mis_reports.v1.json` is the native MIS download contract (contract version 1.1):
a 46-column anti-join CSV and a 12-column case-notes XLSX. Every column carries
a PII class and handling rule; the file contains no sample values. Generate it
with `python -m jvsg_triage.etl schema`; the tests assert exact agreement with
the typed contracts.

See [native MIS intake](../../docs/mis_intake_contract.md) and the
[PII protocol](../../docs/pii_protocol.md) for field handling, title-row and
footer validation, and privacy boundaries.
