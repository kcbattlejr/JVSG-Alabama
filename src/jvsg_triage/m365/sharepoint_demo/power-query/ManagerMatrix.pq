// Query name: ManagerMatrix   (load to a table named ManagerMatrix on the Dashboard sheet, A9)
// LWIA rows by follow-up band, built from the Manager query. The three known
// bands always appear (zero when absent) so the layout and chart stay stable;
// any other band found in the data is added after them.
let
    Keyed = Table.AddColumn(
        Manager, "LWIA",
        each if [LWIA_NAME] = null or [LWIA_NAME] = "" then [INDIVIDUAL_RECORD_LWIA] else [LWIA_NAME],
        type text
    ),
    Slim = Table.SelectColumns(Keyed, {"LWIA", "FOLLOW_UP_BAND", "INDIVIDUALS"}),
    Known = {"Overdue", "Due soon", "Current"},
    Found = List.Distinct(Slim[FOLLOW_UP_BAND]),
    Bands = Known & List.Sort(List.Difference(Found, Known)),
    Pivoted = if Table.RowCount(Slim) = 0
        then #table({"LWIA"}, {})
        else Table.Pivot(Slim, Found, "FOLLOW_UP_BAND", "INDIVIDUALS", List.Sum),
    Complete = List.Accumulate(
        Known, Pivoted,
        (state, band) => if Table.HasColumns(state, band) then state else Table.AddColumn(state, band, each null)
    ),
    Ordered = Table.SelectColumns(Complete, {"LWIA"} & Bands),
    Zeroed = Table.ReplaceValue(Ordered, null, 0, Replacer.ReplaceValue, Bands),
    Total = Table.AddColumn(
        Zeroed, "Total", each List.Sum(Record.ToList(Record.SelectFields(_, Bands))), Int64.Type
    )
in
    Table.Sort(Total, {{"LWIA", Order.Ascending}})
