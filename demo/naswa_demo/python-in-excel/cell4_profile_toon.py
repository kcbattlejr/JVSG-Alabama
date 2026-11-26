# Cell 4 of 4 - TOON export of the rule-based profile classification (Python in Excel).
# Paste into a FOURTH Python cell, after cells 1-3 (uses _cell, CHUNK_LIMIT). Stdlib + pandas.
# Input: the Classification table (Power Query, rules profile-rules-v1) and the Profile
# table. Output matches jvsg_triage.toon.codec: "[N]{fields}:" then 2-space rows.
# Rows carry a profile row key (P0001...) only: no name, State ID or contact detail.
CLASS_FIELDS = ("profile_id", "domain", "state", "rule_id", "evidence_field", "evidence_value",
                "evidence_as_of", "freshness", "partner_category", "rules_version",
                "verification_status", "reviewer_action", "reviewer_role", "reviewed_on")
SUMMARY_FIELDS = ("profile_id", "office", "as_of", "days_since_contact",
                  "contact_info_age_days", "contact_freshness", "domains_flagged")


def _clean(value):
    if value is None or value != value:  # None or NaN/NaT
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()[:10]
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value if isinstance(value, int) else str(value)


def _table(fields, rows):
    if not rows:
        return "[0]:\n"
    lines = [f"[{len(rows)}]{{{','.join(fields)}}}:"]
    lines.extend("  " + ",".join(_cell(row[f]) for f in fields) for row in rows)
    return "\n".join(lines) + "\n"


def _chunks(fields, rows):
    chunks, current, size = [], [], 0
    for row in rows:
        length = len(_table(fields, [row]))
        if current and size + length > CHUNK_LIMIT:
            chunks.append(_table(fields, current))
            current, size = [], 0
        current.append(row)
        size += length
    chunks.append(_table(fields, current))
    return chunks


def classification_rows(df):
    """Rows for the barrier_classifications table; reviewer columns stay null."""
    rows = []
    for rec in df.to_dict("records"):
        row = {f: _clean(rec.get(f)) for f in CLASS_FIELDS}
        row["reviewer_action"] = row["reviewer_role"] = row["reviewed_on"] = None
        rows.append(row)
    return rows


def summary_rows(profile_df, class_df):
    """One row per profile: contact freshness and the count of CRT/ACT domains."""
    flagged = class_df[class_df["state"].isin(["CRT", "ACT"])].groupby("profile_id").size()
    rows = []
    for i, rec in enumerate(profile_df.to_dict("records"), start=1):
        pid = f"P{i:04d}"
        as_of = rec["AS_OF_DATE"]
        updated = rec.get("CONTACT_INFO_UPDATED_DATE")
        age = None if _clean(updated) is None else (as_of - updated).days
        fresh = "unknown" if age is None else ("stale" if age > 180 else "current")
        rows.append({
            "profile_id": pid, "office": rec["OFFICE_NAME"], "as_of": _clean(as_of),
            "days_since_contact": _clean(rec["DAYS_SINCE_CONTACT"]),
            "contact_info_age_days": age,
            "contact_freshness": fresh,
            "domains_flagged": int(flagged.get(pid, 0)),
        })
    return rows


def profile_toon(profile_df, class_df):
    """Returns (classification_chunks, summary_chunks): valid TOON tables per Excel cell."""
    return (_chunks(CLASS_FIELDS, classification_rows(class_df)),
            _chunks(SUMMARY_FIELDS, summary_rows(profile_df, class_df)))
