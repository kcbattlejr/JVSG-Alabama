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

function buildOffices(workbook: ExcelScript.Workbook, byOffice: ExcelScript.Table): void {
  const sheet = workbook.addWorksheet("Offices and Age");
  sheet.setShowGridlines(false);
  banner(sheet, "Offices and age of last contact", "Restricted: unsuppressed office counts. Candidates for review, not decisions.", "P");

  // Office by band chart straight from the query table; Total is dropped from the chart.
  const chart = sheet.addChart(ExcelScript.ChartType.columnStacked, byOffice.getRange(), ExcelScript.ChartSeriesBy.columns);
  chart.getTitle().setText("Veterans by office and follow-up band");
  chart.setPosition("A4", "H24");
  chart.getLegend().setPosition(ExcelScript.ChartLegendPosition.bottom);
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

  // Days since last contact buckets.
  sheet.getRange("J4:K4").setValues([["Days since contact", "Veterans"]]);
  header(sheet.getRange("J4:K4"));
  const days = "Worklist[DAYS_SINCE_CONTACT]";
  sheet.getRange("J5:K9").setFormulas([
    ["0-90", "=COUNTIFS(" + days + ',">=0",' + days + ',"<=90")'],
    ["91-180", "=COUNTIFS(" + days + ',">=91",' + days + ',"<=180")'],
    ["181-270", "=COUNTIFS(" + days + ',">=181",' + days + ',"<=270")'],
    ["271-365", "=COUNTIFS(" + days + ',">=271",' + days + ',"<=365")'],
    ["Over 365", "=COUNTIFS(" + days + ',">365")'],
  ]);
  sheet.getRange("J5:J9").setNumberFormat("@");
  const daysChart = sheet.addChart(ExcelScript.ChartType.columnClustered, sheet.getRange("J4:K9"), ExcelScript.ChartSeriesBy.columns);
  daysChart.getTitle().setText("Days since last contact");
  daysChart.getLegend().setVisible(false);
  daysChart.setPosition("J11", "P24");

  // Note count buckets.
  sheet.getRange("A27:B27").setValues([["JVSG notes this FY", "Veterans"]]);
  header(sheet.getRange("A27:B27"));
  const notes = "Worklist[JVSG_NOTE_COUNT]";
  sheet.getRange("A28:B32").setFormulas([
    ["1", "=COUNTIFS(" + notes + ",1)"],
    ["2", "=COUNTIFS(" + notes + ",2)"],
    ["3", "=COUNTIFS(" + notes + ",3)"],
    ["4", "=COUNTIFS(" + notes + ",4)"],
    ["5 or more", "=COUNTIFS(" + notes + ',">=5")'],
  ]);
  sheet.getRange("A28:A32").setNumberFormat("@");
  const notesChart = sheet.addChart(ExcelScript.ChartType.columnClustered, sheet.getRange("A27:B32"), ExcelScript.ChartSeriesBy.columns);
  notesChart.getTitle().setText("JVSG note count");
  notesChart.getLegend().setVisible(false);
  notesChart.setPosition("D26", "H40");

  sheet.getRange("A:A").getFormat().setColumnWidth(120);
  sheet.getRange("J:J").getFormat().setColumnWidth(120);
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
