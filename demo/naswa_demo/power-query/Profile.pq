// Query name: Profile   (load to a worksheet table named Profile, sheet "Profile")
// Reads the newest CSV in .../restricted/csv/profile/ (profile report: structured fields).
// Contains veteran identifiers: use only in the restricted workbook.
// DEMO COPY: reads a local folder. Needs a text parameter DemoFolder = the full path
// of the demo's Demo folder (for example C:\JVSG\Demo). Synthetic data only.
let
    Files = Folder.Files(DemoFolder),
    InFolder = Table.SelectRows(
        Files,
        each Text.Contains(Text.Replace([Folder Path], "\", "/"), "/restricted/csv/profile/") and Text.Lower([Extension]) = ".csv"
    ),
    Latest = Table.FirstN(Table.Sort(InFolder, {{"Date modified", Order.Descending}}), 1),
    Content = if Table.RowCount(Latest) = 0
        then error "No CSV found in restricted/csv/profile."
        else Latest{0}[Content],
    Raw = Csv.Document(Content, [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Raw, [PromoteAllScalars = true]),
    Named = Table.TransformColumnNames(Promoted, each Text.Upper(Text.Trim(_))),
    Required = {
        "INDIVIDUAL_USERNAME", "STATE_ID", "AS_OF_DATE", "OFFICE_NAME", "LAST_CONTACT_DATE",
        "DAYS_SINCE_CONTACT", "CONTACT_INFO_UPDATED_DATE", "LAST_EMPLOYMENT_END_DATE",
        "LAST_OUTCOME_TYPE", "LAST_OUTCOME_DATE", "HOMELESS_FLAG", "HOUSING_UNSTABLE_FLAG",
        "DISABILITY_FLAG", "LAST_MEDICAL_SERVICE_DATE", "TRAINING_ENROLLED_FLAG", "JUSTICE_FLAG"
    },
    Checked = if Table.HasColumns(Named, Required)
        then Named
        else error "This is not the profile CSV (expected columns are missing).",
    ToDate = (t as nullable text) as nullable date =>
        try Date.FromText(Text.Trim(t), [Culture = "en-US"]) otherwise null,
    ToInt = (t as nullable text) as nullable number =>
        try Number.FromText(Text.Trim(t)) otherwise null,
    // State ID and the 0/1 flags stay text so leading zeros and exact "1" matches survive.
    Typed = Table.TransformColumns(
        Checked,
        {
            {"AS_OF_DATE", ToDate, type nullable date},
            {"LAST_CONTACT_DATE", ToDate, type nullable date},
            {"CONTACT_INFO_UPDATED_DATE", ToDate, type nullable date},
            {"LAST_EMPLOYMENT_END_DATE", ToDate, type nullable date},
            {"LAST_OUTCOME_DATE", ToDate, type nullable date},
            {"LAST_MEDICAL_SERVICE_DATE", ToDate, type nullable date},
            {"DAYS_SINCE_CONTACT", ToInt, Int64.Type}
        },
        null,
        MissingField.Ignore
    )
in
    Typed
