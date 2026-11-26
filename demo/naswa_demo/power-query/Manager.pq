// Query name: Manager   (load to a worksheet table named Manager, sheet "Manager_Data")
// Reads the newest CSV in .../csv/manager/ (step 21 output: counts, no identifiers).
// DEMO COPY: reads a local folder. Needs a text parameter DemoFolder = the full path
// of the demo's Demo folder (for example C:\JVSG\Demo). Synthetic data only.
let
    Files = Folder.Files(DemoFolder),
    InFolder = Table.SelectRows(
        Files,
        each Text.Contains(Text.Replace([Folder Path], "\", "/"), "/csv/manager/") and Text.Lower([Extension]) = ".csv"
    ),
    Latest = Table.FirstN(Table.Sort(InFolder, {{"Date modified", Order.Descending}}), 1),
    Content = if Table.RowCount(Latest) = 0
        then error "No CSV found in csv/manager."
        else Latest{0}[Content],
    Raw = Csv.Document(Content, [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Raw, [PromoteAllScalars = true]),
    Named = Table.TransformColumnNames(Promoted, each Text.Upper(Text.Trim(_))),
    Required = {
        "RESULT_STATUS", "FY_START", "FY_END", "AS_OF_DATE",
        "INDIVIDUAL_RECORD_LWIA", "LWIA_NAME", "FOLLOW_UP_BAND", "INDIVIDUALS"
    },
    Checked = if Table.HasColumns(Named, Required)
        then Named
        else error "This is not the step 21 manager CSV (expected columns are missing).",
    ToDate = (t as nullable text) as nullable date =>
        try Date.FromText(Text.Trim(t), [Culture = "en-US"]) otherwise null,
    // A no_visible_groups result has blank counts; those rows are dropped.
    WithCounts = Table.SelectRows(Checked, each [INDIVIDUALS] <> null and Text.Trim([INDIVIDUALS]) <> ""),
    Typed = Table.TransformColumns(
        WithCounts,
        {
            {"FY_START", ToDate, type nullable date},
            {"FY_END", ToDate, type nullable date},
            {"AS_OF_DATE", ToDate, type nullable date},
            {"INDIVIDUALS", each Number.FromText(Text.Trim(_)), Int64.Type},
            {"INDIVIDUAL_RECORD_LWIA", Text.Trim, type text},
            {"LWIA_NAME", Text.Trim, type text},
            {"FOLLOW_UP_BAND", Text.Trim, type text}
        }
    )
in
    Typed
