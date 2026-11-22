// Query name: WorklistByOffice   (load to a table named WorklistByOffice on the Summary sheet)
// Office rows by follow-up band, built from the Worklist query.
let
    Slim = Table.SelectColumns(Worklist, {"OFFICE_NAME", "FOLLOW_UP_BAND"}),
    Known = {"Overdue", "Due soon", "Current"},
    Counted = Table.Group(
        Slim, {"OFFICE_NAME", "FOLLOW_UP_BAND"}, {{"N", each Table.RowCount(_), Int64.Type}}
    ),
    Pivoted = if Table.RowCount(Counted) = 0
        then #table({"OFFICE_NAME"}, {})
        else Table.Pivot(Counted, List.Distinct(Counted[FOLLOW_UP_BAND]), "FOLLOW_UP_BAND", "N", List.Sum),
    Complete = List.Accumulate(
        Known, Pivoted,
        (state, band) => if Table.HasColumns(state, band) then state else Table.AddColumn(state, band, each null)
    ),
    Ordered = Table.SelectColumns(Complete, {"OFFICE_NAME"} & Known),
    Zeroed = Table.ReplaceValue(Ordered, null, 0, Replacer.ReplaceValue, Known),
    Total = Table.AddColumn(Zeroed, "Total", each [Overdue] + [Due soon] + [Current], Int64.Type)
in
    Table.Sort(Total, {{"OFFICE_NAME", Order.Ascending}})
