# Security and public-release requirements

This repository is a synthetic demonstration under public review, not an
approved production system or an open-source release. Apache-2.0 is proposed
but has not been granted; legal must confirm ownership and licensing first.

## Reporting sensitive material

Do not post secrets, personal records, infrastructure details, or reproductions
of sensitive historical content in public issues or pull requests. Use GitHub's
private vulnerability reporting feature when available. Otherwise, use an
existing approved private channel to the repository owner or agency security
team; do not attach sensitive files to a public report.

## Publication boundaries

- Publish invented fixtures and distributions only. Real-data validation
  metrics, manifests, cohort profiles, and individual governance assignments
  require explicit publication approval.
- Never commit credentials, private host/network/storage inventories, local
  backup mappings, or live case notes. Scrubbed output remains private.
- Keep third-party documents out until redistribution rights are confirmed.
- Require passing CI and review for changes to protected branches.

## Administrator release checklist

- Enable secret scanning, push protection, and private vulnerability reporting
  in repository settings, then review any alerts. An unavailable scan or an
  empty alert list is not proof of no disclosure.
- Protect `main` and `presentation/2026-11-19` with required pull requests, at
  least one approving review, the `quality` CI check, resolved conversations,
  and blocked force pushes/deletions. Coordinate any temporary exception for
  an approved history cleanup.
- Review Actions permissions, logs/artifacts, Codespaces, and collaborator
  access. Keep workflow token permissions read-only unless explicitly needed.
- Complete the historical-disclosure support request below and confirm
  publication rights before declaring the repository release-ready.
- Obtain legal approval before replacing the proprietary package metadata
  with Apache-2.0 and adding the approved license/notice material.

The cleanup session could not administer these security settings because the
GitHub App token returned HTTP 403. The repository owner must complete and
verify them using an authorized account; they are not claimed complete.

## Historical disclosure response

Deleting a file from a branch tip does not remove its history. After an
authorized rewrite, the repository owner must contact GitHub Support through
https://support.github.com/ to request removal of sensitive cached views and
retained pull-request references. Supply affected paths, old commit IDs, and
the rewrite's first changed commits privately. PR #1 needs this review.

Review Actions logs/artifacts and Codespaces for retained copies. Collaborators
must preserve uncommitted work privately, then use a fresh clone of the
rewritten repository; merging or pushing old history can restore the exposure.
Do not create public backup tags or branches pointing to pre-cleanup commits.
Review affected systems' access controls and access logs. Rotate any credentials
found exposed; a disclosed topology alone does not establish credential leakage.

History rewriting and GitHub cache removal cannot recall existing external
clones or copies. Do not claim that all historical public copies were erased.
