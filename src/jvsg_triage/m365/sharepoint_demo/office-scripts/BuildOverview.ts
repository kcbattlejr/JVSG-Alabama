/**
 * Builds the "Overview" sheet that matches the original demo dashboard layout:
 * navy banner, four colour tiles (total / current / due soon / overdue),
 * status line, two charts, and a "how to read" block.
 *
 * Run it manually from the Automate tab; it needs no Power Automate flow.
 * It reads the Power Query tables "Manager" and "ManagerMatrix" and writes
 * only live formulas and charts, so it can be re-run safely (it replaces
 * "Overview"). Refresh the queries first. Keep the query tables on a data
 * sheet (for example the old "Dashboard" sheet renamed "Data").
 */
const NAVY = "#16324F";
const INK = "#243746";
const MUTED = "#587080";
const GREEN = "#2E8B57";
const AMBER = "#D28B16";
const RED = "#C94C4C";
const SERIES_COLORS: { [band: string]: string } = {
  "Overdue": RED,
  "Due soon": AMBER,
  "Current": GREEN,
};

function main(workbook: ExcelScript.Workbook) {
  const matrix = workbook.getTable("ManagerMatrix");
  if (!workbook.getTable("Manager") || !matrix) {
    throw new Error('Load the "Manager" and "ManagerMatrix" queries to tables with those names first.');
  }

  const existing = workbook.getWorksheet("Overview");
  if (existing) {
    existing.delete();
  }
  const sheet = workbook.addWorksheet("Overview");
  sheet.setShowGridlines(false);
  sheet.getRange("A1:Q60").getFormat().getFont().setName("Aptos");
  sheet.getRange("A1:Q60").getFormat().getFont().setColor(INK);
  sheet.getRange("A:Q").getFormat().setColumnWidth(72);
  sheet.getRange("I:I").getFormat().setColumnWidth(24);

  // Banner
  const title = sheet.getRange("A1:Q1");
  title.merge(false);
  title.setValue("JVSG FY2026 non-case-managed veteran follow-up");
  title.getFormat().getFill().setColor(NAVY);
  title.getFormat().getFont().setColor("#FFFFFF");
  title.getFormat().getFont().setBold(true);
  title.getFormat().getFont().setSize(24);
  title.getFormat().setRowHeight(42);
  title.getFormat().setVerticalAlignment(ExcelScript.VerticalAlignment.center);
  title.getFormat().setIndentLevel(1);

  const sub = sheet.getRange("A2:Q2");
  sub.merge(false);
  sub.setValue("Candidates for qualified human review. Not a decision, assignment, or referral.");
  sub.getFormat().getFill().setColor(NAVY);
  sub.getFormat().getFont().setColor("#FFFFFF");
  sub.getFormat().getFont().setSize(11);
  sub.getFormat().setRowHeight(24);
  sub.getFormat().setIndentLevel(1);

  // Tiles: label row 4, value rows 5-6
  const counts = "Manager[INDIVIDUALS]";
  const band = "Manager[FOLLOW_UP_BAND]";
  // A band with no visible group would read as a true zero, but small groups are omitted
  // from the aggregate report, so say so instead of showing 0.
  const bandTotal = (name: string): string =>
    '=IF(COUNTIFS(' + band + ',"' + name + '")=0,"Suppressed",SUMIFS(' + counts + "," + band + ',"' + name + '"))';
  const tiles: { area: string; label: string; formula: string; fill: string; color: string }[] = [
    { area: "A", label: "VETERANS IN REPORT (VISIBLE GROUPS)", formula: "=SUM(" + counts + ")", fill: "#F4F7F9", color: NAVY },
    { area: "E", label: "CURRENT (UNDER 15 DAYS)", formula: bandTotal("Current"), fill: "#DDF2E5", color: GREEN },
    { area: "J", label: "DUE SOON (15-29 DAYS)", formula: bandTotal("Due soon"), fill: "#FFF0CC", color: AMBER },
    { area: "N", label: "OVERDUE (30+ DAYS)", formula: bandTotal("Overdue"), fill: "#FCE1E1", color: RED },
  ];
  const ends: { [start: string]: string } = { A: "D", E: "H", J: "M", N: "Q" };
  sheet.getRange("A4:Q4").getFormat().setRowHeight(22);
  sheet.getRange("A5:Q6").getFormat().setRowHeight(25);
  tiles.forEach((t) => {
    const end = ends[t.area];
    const label = sheet.getRange(t.area + "4:" + end + "4");
    label.merge(false);
    label.setValue(t.label);
    label.getFormat().getFont().setBold(true);
    label.getFormat().getFont().setSize(9);
    label.getFormat().getFont().setColor(MUTED);
    label.getFormat().getFill().setColor(t.fill);
    label.getFormat().setIndentLevel(1);
    const value = sheet.getRange(t.area + "5:" + end + "6");
    value.merge(false);
    value.setFormula(t.formula);
    value.setNumberFormat("#,##0");
    value.getFormat().getFill().setColor(t.fill);
    value.getFormat().getFont().setBold(true);
    value.getFormat().getFont().setSize(26);
    value.getFormat().getFont().setColor(t.color);
    value.getFormat().setHorizontalAlignment(ExcelScript.HorizontalAlignment.left);
    value.getFormat().setVerticalAlignment(ExcelScript.VerticalAlignment.center);
    value.getFormat().setIndentLevel(1);
  });

  // Status line
  const status = sheet.getRange("A7:Q7");
  status.merge(false);
  status.setFormula(
    '="As of "&TEXT(MAX(Manager[AS_OF_DATE]),"mm/dd/yyyy")&"  |  "&' +
    'TEXT(IF(SUM(' + counts + ')=0,0,SUMIFS(' + counts + "," + band + ',"Overdue")/SUM(' + counts + ')),"0%")' +
    '&" of visible veterans overdue  |  Visible groups only: small groups are suppressed, so band counts here can be lower than office-level counts"'
  );
  status.getFormat().getFont().setBold(true);
  status.getFormat().getFont().setColor(NAVY);
  status.getFormat().setRowHeight(24);
  status.getFormat().setIndentLevel(1);

  // Charts use the matrix without its Total column.
  const source = matrix.getRange().getResizedRange(0, -1);
  addChart(sheet, source, ExcelScript.ChartType.columnStacked, "Veterans by LWIA and follow-up band", "A9", "H27", "LWIA", "Number of veterans");
  addChart(sheet, source, ExcelScript.ChartType.columnStacked100, "Share of each LWIA by follow-up band", "J9", "Q27", "LWIA", "Share of veterans");

  sheet.getRange("A28:Q28").merge(false);
  sheet.getRange("A28").setValue("Each veteran is counted once, by the oldest-first follow-up band assigned in the report.");
  sheet.getRange("A28").getFormat().getFont().setItalic(true);
  sheet.getRange("A28").getFormat().getFont().setColor(MUTED);
  sheet.getRange("A28").getFormat().setIndentLevel(1);

  // How to read
  const how = sheet.getRange("A30:Q30");
  how.merge(false);
  how.setValue("HOW TO READ THIS DASHBOARD");
  how.getFormat().getFill().setColor(NAVY);
  how.getFormat().getFont().setColor("#FFFFFF");
  how.getFormat().getFont().setBold(true);
  how.getFormat().setIndentLevel(1);
  const rows: string[][] = [
    ["Current", "Under 15 days since the veteran's most recent JVSG staff note this fiscal year."],
    ["Due soon", "15-29 days since the most recent note."],
    ["Overdue", "30 or more days since the most recent note. Thresholds are examples pending owner confirmation."],
    ["Scope", "Veterans with a JVSG staff note in FY2026 and no active case-management (WP 205) plan."],
    ["Suppression", "Groups below the privacy threshold are omitted, so totals cover visible groups only. A band showing Suppressed has no visible group; it is not a confirmed zero, and office-level (restricted) counts can be higher."],
  ];
  rows.forEach((r, i) => {
    const n = 31 + i;
    const key = sheet.getRange("A" + n + ":D" + n);
    key.merge(false);
    key.setValue(r[0]);
    key.getFormat().getFont().setBold(true);
    key.getFormat().getFont().setColor(NAVY);
    key.getFormat().setIndentLevel(1);
    const text = sheet.getRange("E" + n + ":Q" + n);
    text.merge(false);
    text.setValue(r[1]);
    sheet.getRange("A" + n + ":Q" + n).getFormat().setRowHeight(24);
    sheet.getRange("A" + n + ":Q" + n).getFormat().getFill().setColor(i % 2 === 0 ? "#F4F7F9" : "#FFFFFF");
  });

  sheet.setPosition(0);
  sheet.activate();
  sheet.getRange("A1").select();
}

function addChart(
  sheet: ExcelScript.Worksheet,
  source: ExcelScript.Range,
  type: ExcelScript.ChartType,
  title: string,
  from: string,
  to: string,
  categoryTitle: string,
  valueTitle: string
): void {
  const chart = sheet.addChart(type, source, ExcelScript.ChartSeriesBy.columns);
  chart.getTitle().setText(title);
  chart.getTitle().getFormat().getFont().setBold(true);
  chart.getTitle().getFormat().getFont().setColor(NAVY);
  chart.getLegend().setPosition(ExcelScript.ChartLegendPosition.bottom);
  chart.setPosition(from, to);
  const categoryAxis = chart.getAxes().getCategoryAxis();
  categoryAxis.getTitle().setText(categoryTitle);
  categoryAxis.getTitle().setVisible(true);
  const valueAxis = chart.getAxes().getValueAxis();
  valueAxis.getTitle().setText(valueTitle);
  valueAxis.getTitle().setVisible(true);
  valueAxis.getMajorGridlines().setVisible(false);
  chart.getSeries().forEach((series) => {
    const color = SERIES_COLORS[series.getName()];
    series.getFormat().getFill().setSolidColor(color ? color : "#7F8FA9");
  });
}
