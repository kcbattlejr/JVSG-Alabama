// Query name: Worklist   (load to a worksheet table named Worklist, sheet "Worklist")
// Reads the newest CSV in .../restricted/csv/worklist/ (step 17 output).
// Contains veteran identifiers: use only in the restricted workbook.
// DEMO COPY: reads a local folder. Needs a text parameter DemoFolder = the full path
// of the demo's Demo folder (for example C:\JVSG\Demo). Synthetic data only.
let
    Files = Folder.Files(DemoFolder),
    InFolder = Table.SelectRows(
        Files,
        each Text.Contains(Text.Replace([Folder Path], "\", "/"), "/restricted/csv/worklist/") and Text.Lower([Extension]) = ".csv"
    ),
    Latest = Table.FirstN(Table.Sort(InFolder, {{"Date modified", Order.Descending}}), 1),
    Content = if Table.RowCount(Latest) = 0
        then error "No CSV found in restricted/csv/worklist."
        else Latest{0}[Content],
    Raw = Csv.Document(Content, [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Raw, [PromoteAllScalars = true]),
    Named = Table.TransformColumnNames(Promoted, each Text.Upper(Text.Trim(_))),
    Required = {
        "INDIVIDUAL_USERNAME", "STATE_ID", "OFFICE_NAME", "LWIA", "JVSG_NOTE_COUNT",
        "LATEST_FY_203_DATE", "LAST_CONTACT_DATE", "DAYS_SINCE_CONTACT", "FOLLOW_UP_BAND"
    },
    Checked = if Table.HasColumns(Named, Required)
        then Named
        else error "This is not the step 17 worklist CSV (expected columns are missing).",
    ToDate = (t as nullable text) as nullable date =>
        try Date.FromText(Text.Trim(t), [Culture = "en-US"]) otherwise null,
    ToInt = (t as nullable text) as nullable number =>
        try Number.FromText(Text.Trim(t)) otherwise null,
    // State ID, office, and LWIA stay text so leading zeros survive.
    Typed = Table.TransformColumns(
        Checked,
        {
            {"FY_START", ToDate, type nullable date},
            {"FY_END", ToDate, type nullable date},
            {"AS_OF_DATE", ToDate, type nullable date},
            {"FIRST_JVSG_NOTE_DATE", ToDate, type nullable date},
            {"LAST_JVSG_NOTE_DATE", ToDate, type nullable date},
            {"LATEST_FY_203_DATE", ToDate, type nullable date},
            {"LAST_CONTACT_DATE", ToDate, type nullable date},
            {"JVSG_NOTE_COUNT", ToInt, Int64.Type},
            {"DAYS_SINCE_CONTACT", ToInt, Int64.Type}
        },
        null,
        MissingField.Ignore
    )
in
    Typed
