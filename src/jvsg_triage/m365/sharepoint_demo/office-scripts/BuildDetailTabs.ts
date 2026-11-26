/**
 * Builds the restricted detail tabs over the "Worklist" and "WorklistByOffice"
 * Power Query tables: Offices and Age, Watchlist, Drilldown, Definitions.
 *
 * Run it manually from Automate > New Script after both queries are loaded and
 * refreshed. It deletes and recreates only those four sheets, never touches
 * queries or other sheets, and writes live formulas (no values copied).
 * These tabs list veterans: keep the workbook restricted.
 * Output is a candidate list for qualified human review, not a decision.
 *
 * Layout is the one RepairDetailFormulas.ts expects:
 *   Watchlist  K5:K54   (top 50 overdue, helper column K hidden)
 *   Drilldown  K10:K109 (up to 100 rows; filters in B4:B6)
 */
const NAVY = "#16324F";
const INK = "#243746";
const MUTED = "#587080";
const RED = "#C94C4C";
const AMBER = "#D28B16";
const GREEN = "#2E8B57";
const SHEETS = ["Offices and Age", "Watchlist", "Drilldown", "Definitions"];

function main(workbook: ExcelScript.Workbook): void {
  const worklist = workbook.getTable("Worklist");
  const byOffice = workbook.getTable("WorklistByOffice");
  if (!worklist || !byOffice) {
    throw new Error('Load the "Worklist" and "WorklistByOffice" queries to tables with those names first.');
  }
  SHEETS.forEach((name) => workbook.getWorksheet(name)?.delete());

  buildOffices(workbook, byOffice);
  buildWatchlist(workbook);
  buildDrilldown(workbook);
  buildDefinitions(workbook);
  workbook.getApplication().calculate(ExcelScript.CalculationType.full);
}

function banner(sheet: ExcelScript.Worksheet, title: string, subtitle: string, lastCol: string): void {
  const band = sheet.getRange("A1:" + lastCol + "1");
  band.getFormat().getFill().setColor(NAVY);
  band.getFormat().setRowHeight(30);
  const titleCell = sheet.getRange("A1");
  titleCell.setValue(title);
  titleCell.getFormat().getFont().setBold(true);
  titleCell.getFormat().getFont().setSize(16);
  titleCell.getFormat().getFont().setColor("#FFFFFF");
  titleCell.getFormat().setVerticalAlignment(ExcelScript.VerticalAlignment.center);
  const sub = sheet.getRange("A2");
  sub.setValue(subtitle);
  sub.getFormat().getFont().setColor(MUTED);
  sub.getFormat().getFont().setItalic(true);
}

function header(range: ExcelScript.Range): void {
  range.getFormat().getFill().setColor(NAVY);
  range.getFormat().getFont().setColor("#FFFFFF");
  range.getFormat().getFont().setBold(true);
  range.getFormat().setWrapText(true);
}

function tile(sheet: ExcelScript.Worksheet, first: string, last: string, row: number, label: string, formula: string, caption: string, color: string): void {
  const labelRange = sheet.getRange(first + row + ":" + last + row);
  labelRange.merge(false);
  labelRange.setValue(label);
  const valueRange = sheet.getRange(first + (row + 1) + ":" + last + (row + 1));
  valueRange.merge(false);
  valueRange.setFormula(formula);
  valueRange.setNumberFormat("#,##0");
  valueRange.getFormat().getFont().setSize(24);
  valueRange.getFormat().getFont().setBold(true);
  const captionRange = sheet.getRange(first + (row + 2) + ":" + last + (row + 2));
  captionRange.merge(false);
  captionRange.setFormula(caption);
  const all = sheet.getRange(first + row + ":" + last + (row + 2));
  all.getFormat().getFill().setColor(color);
  all.getFormat().getFont().setColor("#FFFFFF");
  all.getFormat().setHorizontalAlignment(ExcelScript.HorizontalAlignment.center);
  all.getFormat().setVerticalAlignment(ExcelScript.VerticalAlignment.center);
  sheet.getRange(first + (row + 1)).getFormat().setRowHeight(38);
}

function styleChart(chart: ExcelScript.Chart, title: string, categoryTitle: string, valueTitle: string): void {
  chart.getTitle().setText(title);
  chart.getTitle().getFormat().getFont().setBold(true);
  chart.getTitle().getFormat().getFont().setColor(NAVY);
  const categoryAxis = chart.getAxes().getCategoryAxis();
  categoryAxis.getTitle().setVisible(true);
  categoryAxis.getTitle().setText(categoryTitle);
  const valueAxis = chart.getAxes().getValueAxis();
  valueAxis.getTitle().setVisible(true);
  valueAxis.getTitle().setText(valueTitle);
}

function buildOffices(workbook: ExcelScript.Workbook, byOffice: ExcelScript.Table): void {
  const sheet = workbook.addWorksheet("Offices and Age");
  sheet.setShowGridlines(false);
  sheet.getRange("A:P").getFormat().setColumnWidth(80);
  banner(sheet, "Offices and age of last contact", "Restricted: unsuppressed office counts. Candidates for qualified human review, not decisions.", "P");

  // Summary tiles over the office table.
  const share = (band: string) => '=IFERROR(TEXT(SUM(WorklistByOffice[' + band + "])/SUM(WorklistByOffice[Total]),\"0%\")&\" of the worklist\",\"\")";
  tile(sheet, "A", "D", 4, "VETERANS ON THE WORKLIST", "=SUM(WorklistByOffice[Total])", '="across "&ROWS(WorklistByOffice[OFFICE_NAME])&" offices"', NAVY);
  tile(sheet, "E", "H", 4, "OVERDUE", "=SUM(WorklistByOffice[Overdue])", share("Overdue"), RED);
  tile(sheet, "I", "L", 4, "DUE SOON", "=SUM(WorklistByOffice[Due soon])", share("Due soon"), AMBER);
  tile(sheet, "M", "P", 4, "CURRENT", "=SUM(WorklistByOffice[Current])", share("Current"), GREEN);

  // 1. Office by band, horizontal so long office names read down the left side.
  placeSection(
    sheet, "A", "P", 8, "1. Where are veterans waiting longest?",
    "Each bar is one office. Its length is the number of veterans on the worklist at that office, split by how long it has been since the last JVSG staff note: " +
    "red = Overdue (30 or more days), amber = Due soon (15 to 29 days), green = Current (under 15 days). " +
    "Look for offices with long red segments: those are the best places to focus outreach first. Day thresholds are examples pending program-owner confirmation."
  );
  const chart = sheet.addChart(ExcelScript.ChartType.barStacked, byOffice.getRange(), ExcelScript.ChartSeriesBy.columns);
  chart.setPosition("A11", "P50");
  chart.getLegend().setPosition(ExcelScript.ChartLegendPosition.bottom);
  styleChart(chart, "Veterans by office and follow-up band", "Office", "Number of veterans");
  chart.getAxes().getCategoryAxis().setReversePlotOrder(true);
  chart.getAxes().getCategoryAxis().getFormat().getFont().setSize(9);
  chart.getSeries().forEach((series) => {
    const name = series.getName();
    if (name === "Total") {
      series.delete();
    } else if (name === "Overdue") {
      series.getFormat().getFill().setSolidColor(RED);
    } else if (name === "Due soon") {
      series.getFormat().getFill().setSolidColor(AMBER);
    } else if (name === "Current") {
      series.getFormat().getFill().setSolidColor(GREEN);
    }
  });

  // 2 and 3. Distribution charts with their data underneath.
  placeSection(sheet, "A", "H", 52, "2. How long since the last contact?",
    "Each column counts veterans by the number of days since their most recent JVSG staff note this fiscal year. A tall column at the right (181 days or more) means many veterans have gone a long time without contact.");
  placeSection(sheet, "I", "P", 52, "3. How much contact have they had?",
    "Each column counts veterans by how many JVSG staff notes they have this fiscal year. A tall column at 1 means most veterans have had only one touch, so they may be the easiest to lose.");

  // Visible data tables under the charts; the charts read these (hidden cells are not plotted).
  const days = "Worklist[DAYS_SINCE_CONTACT]";
  const dayRows: string[][] = [
    ["0-90", "=COUNTIFS(" + days + ',">=0",' + days + ',"<=90")'],
    ["91-180", "=COUNTIFS(" + days + ',">=91",' + days + ',"<=180")'],
    ["181-270", "=COUNTIFS(" + days + ',">=181",' + days + ',"<=270")'],
    ["271-365", "=COUNTIFS(" + days + ',">=271",' + days + ',"<=365")'],
    ["Over 365", "=COUNTIFS(" + days + ',">365")'],
  ];
  sheet.getRange("A74:B74").setValues([["Days since contact", "Veterans"]]);
  header(sheet.getRange("A74:B74"));
  sheet.getRange("A75:A79").setNumberFormat("@");
  sheet.getRange("A75:B79").setFormulas(dayRows);
  const daysChart = sheet.addChart(ExcelScript.ChartType.columnClustered, sheet.getRange("A74:B79"), ExcelScript.ChartSeriesBy.columns);
  daysChart.setPosition("A55", "H72");
  daysChart.getLegend().setVisible(false);
  styleChart(daysChart, "Veterans by days since last contact", "Days since last contact", "Number of veterans");
  daysChart.getSeries().forEach((series) => {
    series.getFormat().getFill().setSolidColor(NAVY);
    series.setHasDataLabels(true);
  });

  const notes = "Worklist[JVSG_NOTE_COUNT]";
  const noteRows: string[][] = [
    ["1", "=COUNTIFS(" + notes + ",1)"],
    ["2", "=COUNTIFS(" + notes + ",2)"],
    ["3", "=COUNTIFS(" + notes + ",3)"],
    ["4", "=COUNTIFS(" + notes + ",4)"],
    ["5 or more", "=COUNTIFS(" + notes + ',">=5")'],
  ];
  sheet.getRange("I74:J74").setValues([["JVSG notes this FY", "Veterans"]]);
  header(sheet.getRange("I74:J74"));
  sheet.getRange("I75:I79").setNumberFormat("@");
  sheet.getRange("I75:J79").setFormulas(noteRows);
  const notesChart = sheet.addChart(ExcelScript.ChartType.columnClustered, sheet.getRange("I74:J79"), ExcelScript.ChartSeriesBy.columns);
  notesChart.setPosition("I55", "P72");
  notesChart.getLegend().setVisible(false);
  styleChart(notesChart, "Veterans by number of JVSG notes", "JVSG notes this fiscal year", "Number of veterans");
  notesChart.getSeries().forEach((series) => {
    series.getFormat().getFill().setSolidColor(NAVY);
    series.setHasDataLabels(true);
  });
}

function placeSection(sheet: ExcelScript.Worksheet, first: string, last: string, row: number, title: string, text: string): void {
  const head = sheet.getRange(first + row + ":" + last + row);
  head.getFormat().getFill().setColor(NAVY);
  head.getFormat().getFont().setColor("#FFFFFF");
  head.getFormat().getFont().setBold(true);
  sheet.getRange(first + row).setValue(title);
  const body = sheet.getRange(first + (row + 1) + ":" + last + (row + 1));
  body.merge(false);
  body.setValue(text);
  body.getFormat().setWrapText(true);
  body.getFormat().setVerticalAlignment(ExcelScript.VerticalAlignment.top);
  body.getFormat().getFill().setColor("#F4F7F9");
  body.getFormat().getFont().setColor(INK);
  sheet.getRange("A" + (row + 1)).getFormat().setRowHeight(60);
}

function buildWatchlist(workbook: ExcelScript.Workbook): void {
  const sheet = workbook.addWorksheet("Watchlist");
  sheet.setShowGridlines(false);
  banner(sheet, "Watchlist: longest wait first", "Top 50 overdue veterans by days since last contact. Restricted. Candidates for review.", "I");
  sheet.getRange("A4:I4").setValues([[
    "Rank", "State ID", "Office", "Last contact", "Days since contact", "Band", "JVSG notes", "FY 203 date", "Staff",
  ]]);
  header(sheet.getRange("A4:I4"));
  sheet.getRange("K4").setValue("helper");

  const rows: (string | number)[][] = [];
  const helper: string[][] = [];
  for (let row = 5; row <= 54; row++) {
    helper.push([
      '=IFERROR(AGGREGATE(14,6,(Worklist[DAYS_SINCE_CONTACT]+ROW(Worklist[STATE_ID])/1000000)' +
      '/(Worklist[FOLLOW_UP_BAND]="Overdue"),$A' + row + '),"")',
    ]);
    const src = "ROUND(MOD($K" + row + ",1)*1000000,0)-ROW(Worklist[#Headers])";
    const pick = (col: string) => '=IF($K' + row + '="","",INDEX(Worklist[' + col + "]," + src + "))";
    rows.push([
      row - 4, pick("STATE_ID"), pick("OFFICE_NAME"), pick("LAST_CONTACT_DATE"), pick("DAYS_SINCE_CONTACT"),
      pick("FOLLOW_UP_BAND"), pick("JVSG_NOTE_COUNT"), pick("LATEST_FY_203_DATE"), pick("LAST_CONTACT_STAFF_NAME"),
    ]);
  }
  sheet.getRange("A5:I54").setFormulas(rows);
  sheet.getRange("K5:K54").setFormulas(helper);
  sheet.getRange("D5:D54").setNumberFormat("mm/dd/yyyy");
  sheet.getRange("H5:H54").setNumberFormat("mm/dd/yyyy");
  sheet.getRange("B5:B54").setNumberFormat("@");
  sheet.getRange("A4:I54").getFormat().autofitColumns();
  sheet.getRange("K:K").setColumnHidden(true);
  sheet.getFreezePanes().freezeRows(4);
}

function buildDrilldown(workbook: ExcelScript.Workbook): void {
  const sheet = workbook.addWorksheet("Drilldown");
  sheet.setShowGridlines(false);
  banner(sheet, "Drilldown", "Filter the worklist. Up to 100 rows, in report order. Restricted. Candidates for review.", "I");

  sheet.getRange("A4:A7").setValues([["Office (blank = all)"], ["Band (blank = all)"], ["Minimum days since contact"], ["Matching veterans"]]);
  sheet.getRange("A4:A7").getFormat().getFont().setBold(true);
  sheet.getRange("B6").setValue(0);
  const inputs = sheet.getRange("B4:B6");
  inputs.getFormat().getFill().setColor("#FFF4D6");
  sheet.getRange("B4").getDataValidation().setRule({
    list: { inCellDropDown: true, source: '=INDIRECT("WorklistByOffice[OFFICE_NAME]")' },
  });
  sheet.getRange("B5").getDataValidation().setRule({
    list: { inCellDropDown: true, source: "Overdue,Due soon,Current" },
  });
  sheet.getRange("B6").getDataValidation().setRule({
    wholeNumber: { formula1: 0, operator: ExcelScript.DataValidationOperator.greaterThanOrEqualTo },
  });
  sheet.getRange("B7").setFormula(
    '=SUMPRODUCT(((Worklist[OFFICE_NAME]=$B$4)+($B$4="")>0)*((Worklist[FOLLOW_UP_BAND]=$B$5)+($B$5="")>0)' +
    "*(Worklist[DAYS_SINCE_CONTACT]>=$B$6))"
  );
  sheet.getRange("C7").setFormula('=IF($B$7>100,"Showing the first 100 of "&$B$7&"; narrow the filters.","")');

  sheet.getRange("A9:I9").setValues([[
    "#", "State ID", "Office", "Last contact", "Days since contact", "Band", "JVSG notes", "FY 203 date", "Staff",
  ]]);
  header(sheet.getRange("A9:I9"));
  sheet.getRange("K9").setValue("helper");

  const rows: (string | number)[][] = [];
  const helper: string[][] = [];
  for (let row = 10; row <= 109; row++) {
    helper.push([
      '=IFERROR(AGGREGATE(15,6,ROW(Worklist[STATE_ID])' +
      '/((Worklist[OFFICE_NAME]=$B$4)+($B$4="")>0)' +
      '/((Worklist[FOLLOW_UP_BAND]=$B$5)+($B$5="")>0)' +
      '/(Worklist[DAYS_SINCE_CONTACT]>=$B$6),$A' + row + '),"")',
    ]);
    const src = "$K" + row + "-ROW(Worklist[#Headers])";
    const pick = (col: string) => '=IF($K' + row + '="","",INDEX(Worklist[' + col + "]," + src + "))";
    rows.push([
      row - 9, pick("STATE_ID"), pick("OFFICE_NAME"), pick("LAST_CONTACT_DATE"), pick("DAYS_SINCE_CONTACT"),
      pick("FOLLOW_UP_BAND"), pick("JVSG_NOTE_COUNT"), pick("LATEST_FY_203_DATE"), pick("LAST_CONTACT_STAFF_NAME"),
    ]);
  }
  sheet.getRange("A10:I109").setFormulas(rows);
  sheet.getRange("K10:K109").setFormulas(helper);
  sheet.getRange("D10:D109").setNumberFormat("mm/dd/yyyy");
  sheet.getRange("H10:H109").setNumberFormat("mm/dd/yyyy");
  sheet.getRange("B10:B109").setNumberFormat("@");
  sheet.getRange("A9:I109").getFormat().autofitColumns();
  sheet.getRange("A:A").getFormat().setColumnWidth(170);
  sheet.getRange("K:K").setColumnHidden(true);
  addReferralProfile(sheet);
  sheet.getFreezePanes().freezeRows(9);
}

// Draft community-partner referral profile for the State ID in M4, in L:P.
// Reads the Profile and Classification tables (profile_id is "P" plus the
// Profile row number, the same key Classification.pq assigns). Fixed template
// text only; no model. Every line is an unverified draft for staff review.
function addReferralProfile(sheet: ExcelScript.Worksheet): void {
  const hasId = '$M$5<>""';
  const row = 'MATCH(TRIM($M$4&""),Profile[STATE_ID],0)';
  const field = (col: string) => '=IF(' + hasId + ',INDEX(Profile[' + col + "]," + row + '),"")';

  const title = sheet.getRange("L3");
  title.setValue("Community partner referral profile (draft for staff review)");
  title.getFormat().getFont().setBold(true);
  title.getFormat().getFont().setSize(13);
  title.getFormat().getFont().setColor(NAVY);

  sheet.getRange("L4").setValue("Select a State ID");
  sheet.getRange("L4").getFormat().getFont().setBold(true);
  sheet.getRange("M4").getFormat().getFill().setColor("#FFF4D6");
  sheet.getRange("M4").getDataValidation().setRule({
    list: { inCellDropDown: true, source: "=$B$10:$B$109" },
  });
  sheet.getRange("M4").setNumberFormat("@");
  sheet.getRange("N4").setValue("Pick from the list or type a State ID from the Profile table.");
  sheet.getRange("N4").getFormat().getFont().setColor(MUTED);

  sheet.getRange("L5:L10").setValues([
    ["Profile ID"], ["Office"], ["Last JVSG contact"], ["Contact info updated"], ["Profile as of"], ["Status"],
  ]);
  sheet.getRange("L5:L10").getFormat().getFont().setBold(true);
  sheet.getRange("M5:M10").setFormulas([
    ['=IFERROR("P"&TEXT(' + row + ',"0000"),"")'],
    [field("OFFICE_NAME")],
    ['=IF(' + hasId + ',TEXT(INDEX(Profile[LAST_CONTACT_DATE],' + row + '),"mm/dd/yyyy")&" ("&INDEX(Profile[DAYS_SINCE_CONTACT],' + row + ')&" days ago)","")'],
    ['=IF(' + hasId + ',TEXT(INDEX(Profile[CONTACT_INFO_UPDATED_DATE],' + row + '),"mm/dd/yyyy"),"")'],
    ['=IF(' + hasId + ',TEXT(INDEX(Profile[AS_OF_DATE],' + row + '),"mm/dd/yyyy"),"")'],
    ['=IF($M$4="","Select a State ID in M4",IF(' + hasId + ',"Unverified draft - staff must confirm","State ID not found in the Profile table"))'],
  ]);
  sheet.getRange("M5:M10").getFormat().setHorizontalAlignment(ExcelScript.HorizontalAlignment.left);

  sheet.getRange("L12:P12").setValues([[
    "Barrier area", "Suggested level", "Why (last known data)", "Data freshness", "Suggested partner category",
  ]]);
  header(sheet.getRange("L12:P12"));

  const areas: [string, string][] = [
    ["TRN", "Training and employment"], ["HSG", "Housing"], ["MED", "Health and VA benefits"], ["LEG", "Legal"],
  ];
  const why =
    '"TRN-1","Credential or training completed within the last year","TRN-2","Enrolled in training",' +
    '"TRN-3","No employment end date on file, or last job ended 180 or more days ago","TRN-0","No training or employment need indicated",' +
    '"HSG-1","Recorded as homeless","HSG-2","Housing instability recorded","HSG-0","No housing indicator recorded",' +
    '"MED-2","Disability recorded; medical service in the last year","MED-1","Disability recorded; no recent medical service",' +
    '"MED-0","No disability recorded","LEG-1","Justice involvement recorded","LEG-0","None recorded"';
  const body: string[][] = [];
  areas.forEach(([code, label], i) => {
    const r = 13 + i;
    const pick = (col: string) =>
      "XLOOKUP(1,(Classification[profile_id]=$M$5)*(Classification[domain]=\"" + code + "\"),Classification[" + col + '],"")';
    body.push([
      label,
      '=IF(' + hasId + ',SWITCH(' + pick("state") + ',"CRT","Critical need","ACT","Active need","MIT","Being addressed","RES","Resolved","Unknown - verify with veteran"),"")',
      '=IF(' + hasId + ",SWITCH(" + pick("rule_id") + "," + why + ',"")&IF(' + pick("evidence_as_of") + '="","","; as of "&TEXT(' + pick("evidence_as_of") + ',"mm/dd/yyyy")),"")',
      '=IF(' + hasId + ',SWITCH(' + pick("freshness") + ',"current","Current","stale","Stale - verify","Date unknown - verify"),"")',
      '=IF(' + hasId + ',IF(' + pick("partner_category") + '="","-",' + pick("partner_category") + '),"")',
    ]);
  });
  sheet.getRange("L13:P16").setFormulas(body);
  sheet.getRange("L13:P16").getFormat().setWrapText(true);
  sheet.getRange("L13:P16").getFormat().setVerticalAlignment(ExcelScript.VerticalAlignment.top);

  sheet.getRange("L18:L20").setValues([["Referral priority"], ["Suggested partner categories"], ["Handoff note"]]);
  sheet.getRange("L18:L20").getFormat().getFont().setBold(true);
  sheet.getRange("M18:M20").setFormulas([
    ['=IF(' + hasId + ',IF(COUNTIF($M$13:$M$16,"Critical need")>0,"Critical need present - prioritize outreach",IF(COUNTIF($M$13:$M$16,"Active need")>0,"Active need(s) indicated - offer referral","No active need indicated from structured data; confirm with veteran")),"")'],
    ['=IF(' + hasId + ',IFERROR(TEXTJOIN("; ",TRUE,IF(($M$13:$M$16="Critical need")+($M$13:$M$16="Active need")>0,$P$13:$P$16,"")),""),"")'],
    ['="Built from structured MIS fields only (last known data, not current). Staff confirm each item with the veteran, obtain consent before sharing with any partner, and decide the referral. Not an eligibility or service decision."'],
  ]);
  sheet.getRange("M18:P20").getFormat().setWrapText(false);

  sheet.getRange("L:L").getFormat().setColumnWidth(170);
  sheet.getRange("M:M").getFormat().setColumnWidth(150);
  sheet.getRange("N:N").getFormat().setColumnWidth(330);
  sheet.getRange("O:O").getFormat().setColumnWidth(120);
  sheet.getRange("P:P").getFormat().setColumnWidth(210);
}

function buildDefinitions(workbook: ExcelScript.Workbook): void {
  const sheet = workbook.addWorksheet("Definitions");
  sheet.setShowGridlines(false);
  banner(sheet, "Definitions", "How to read the detail tabs.", "B");
  const lines: string[][] = [
    ["Worklist", "Veterans with a JVSG case note in the fiscal year and no active Wagner-Peyser 205 in the fiscal year (step 17)."],
    ["Days since contact", "Days from the last JVSG contact date to the report as-of date."],
    ["Follow-up band", "Overdue, Due soon or Current, set by the thresholds agreed with the program owner (confirm before use)."],
    ["Watchlist", "The 50 overdue veterans with the longest wait."],
    ["Drilldown", "Filter by office, band and minimum days; shows up to 100 matches."],
    ["Veterans with a 203", "Rows in the worklist with an active FY 203 date. It is not all veterans with a 203."],
    ["Use", "Candidate list for qualified human review. Not an eligibility, referral or service decision."],
    ["Restricted", "These tabs list veterans. Keep this workbook in the restricted folder only."],
  ];
  sheet.getRange("A4:B" + (3 + lines.length)).setValues(lines);
  sheet.getRange("A4:A" + (3 + lines.length)).getFormat().getFont().setBold(true);
  sheet.getRange("A4:A" + (3 + lines.length)).getFormat().getFont().setColor(INK);
  sheet.getRange("A:A").getFormat().setColumnWidth(150);
  sheet.getRange("B:B").getFormat().setColumnWidth(600);
  sheet.getRange("B4:B" + (3 + lines.length)).getFormat().setWrapText(true);
}
