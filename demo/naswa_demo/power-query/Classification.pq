// Query name: Classification   (load to a worksheet table named Classification, sheet "Classification")
// Rules profile-rules-v1, built from the Profile query: one row per profile and domain
// (TRN, HSG, MED, LEG). Structured fields only; never reads notes. Every row is an
// Unverified suggestion for staff review. No structured indicator means UNK (unknown),
// not "no barrier". Keep in step with src/jvsg_triage/dashboard_demo/profile.py.
let
    StaleDays = 180,
    Categories = [
        TRN = "Training and employment support",
        HSG = "Housing assistance",
        MED = "Health and VA benefits navigation",
        LEG = "Legal aid"
    ],
    Age = (d as nullable date, a as date) as nullable number =>
        if d = null then null else Duration.Days(a - d),
    Within = (d as nullable date, a as date, n as number) as logical =>
        d <> null and Age(d, a) >= 0 and Age(d, a) <= n,
    Iso = (d as nullable date) as text =>
        if d = null then "unknown" else Date.ToText(d, [Format = "yyyy-MM-dd", Culture = "en-US"]),
    Fresh = (d as nullable date, a as date) as text =>
        if d = null then "unknown" else if Age(d, a) > StaleDays then "stale" else "current",
    Make = (pid as text, a as date, domain as text, state as text, rule as text, field as text,
            value as text, d as nullable date) as record =>
        [
            profile_id = pid, domain = domain, state = state, rule_id = rule,
            evidence_field = field, evidence_value = value, evidence_as_of = d,
            freshness = Fresh(d, a),
            partner_category = if state = "CRT" or state = "ACT" then Record.Field(Categories, domain) else null,
            rules_version = "profile-rules-v1", verification_status = "Unverified"
        ],
    One = (r as record, i as number) as list =>
        let
            pid = "P" & Text.PadStart(Text.From(i + 1), 4, "0"),
            a = r[AS_OF_DATE],
            trn =
                if (r[LAST_OUTCOME_TYPE] = "credential" or r[LAST_OUTCOME_TYPE] = "training_completion")
                    and Within(r[LAST_OUTCOME_DATE], a, 365)
                    then Make(pid, a, "TRN", "RES", "TRN-1", "last_outcome_type", r[LAST_OUTCOME_TYPE], r[LAST_OUTCOME_DATE])
                else if r[TRAINING_ENROLLED_FLAG] = "1"
                    then Make(pid, a, "TRN", "MIT", "TRN-2", "training_enrolled_flag", "1", null)
                else if r[LAST_EMPLOYMENT_END_DATE] = null or Age(r[LAST_EMPLOYMENT_END_DATE], a) >= 180
                    then Make(pid, a, "TRN", "ACT", "TRN-3", "last_employment_end_date", Iso(r[LAST_EMPLOYMENT_END_DATE]), r[LAST_EMPLOYMENT_END_DATE])
                else Make(pid, a, "TRN", "UNK", "TRN-0", "last_employment_end_date", Iso(r[LAST_EMPLOYMENT_END_DATE]), r[LAST_EMPLOYMENT_END_DATE]),
            hsg =
                if r[HOMELESS_FLAG] = "1" then Make(pid, a, "HSG", "CRT", "HSG-1", "homeless_flag", "1", null)
                else if r[HOUSING_UNSTABLE_FLAG] = "1" then Make(pid, a, "HSG", "ACT", "HSG-2", "housing_unstable_flag", "1", null)
                else Make(pid, a, "HSG", "UNK", "HSG-0", "housing_flags", "none", null),
            med =
                if r[DISABILITY_FLAG] = "1" and Within(r[LAST_MEDICAL_SERVICE_DATE], a, 365)
                    then Make(pid, a, "MED", "MIT", "MED-2", "last_medical_service_date", Iso(r[LAST_MEDICAL_SERVICE_DATE]), r[LAST_MEDICAL_SERVICE_DATE])
                else if r[DISABILITY_FLAG] = "1" then Make(pid, a, "MED", "ACT", "MED-1", "disability_flag", "1", null)
                else Make(pid, a, "MED", "UNK", "MED-0", "disability_flag", "0", null),
            leg =
                if r[JUSTICE_FLAG] = "1" then Make(pid, a, "LEG", "ACT", "LEG-1", "justice_flag", "1", null)
                else Make(pid, a, "LEG", "UNK", "LEG-0", "justice_flag", "0", null)
        in
            {trn, hsg, med, leg},
    Rows = Table.ToRecords(Profile),
    Records = List.Combine(List.Transform(List.Positions(Rows), each One(Rows{_}, _))),
    Columns = {
        "profile_id", "domain", "state", "rule_id", "evidence_field", "evidence_value",
        "evidence_as_of", "freshness", "partner_category", "rules_version", "verification_status"
    }
in
    if List.IsEmpty(Records)
        then #table(Columns, {})
        else Table.TransformColumnTypes(Table.FromRecords(Records), {{"evidence_as_of", type date}})
