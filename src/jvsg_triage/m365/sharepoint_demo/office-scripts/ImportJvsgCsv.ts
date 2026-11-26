/**
 * ImportJvsgCsv: loads one MIS CSV dump into the open workbook and rebuilds
 * its sheets. Run it from Power Automate ("Run script from SharePoint library")
 * with the CSV file's text as csvText.
 *
 * Two report types are detected from the CSV header row:
 *   - manager: aggregate counts by LWIA and follow-up band (no identifiers).
 *       Writes Manager_Data and rebuilds the Dashboard sheet.
 *   - worklist: one row per veteran (identifiers). Writes Worklist and
 *       rebuilds the Summary sheet. Refuses to run in a workbook that has a
 *       Dashboard sheet, so identifiers never land in the dashboard workbook.
 *
 * Output is a candidate list for qualified human review, not a decision.
 */

type Cell = string | number | boolean;
type ColType = "text" | "int" | "date";

interface ColumnSpec {
  [header: string]: ColType;
}

const MANAGER_COLUMNS: ColumnSpec = {
  REPORT_ID: "text",
  RESULT_STATUS: "text",
  FY_START: "date",
  FY_END: "date",
  AS_OF_DATE: "date",
  INDIVIDUAL_RECORD_LWIA: "text",
  LWIA_NAME: "text",
  FOLLOW_UP_BAND: "text",
  INDIVIDUALS: "int",
};

const WORKLIST_COLUMNS: ColumnSpec = {
  RESULT_STATUS: "text",
  FY_START: "date",
  FY_END: "date",
  AS_OF_DATE: "date",
  INDIVIDUAL_USERNAME: "text",
  STATE_ID: "text",
  STATE_ID_STATUS: "text",
  OFFICE: "text",
  OFFICE_NAME: "text",
  LWIA: "text",
  JVSG_NOTE_COUNT: "int",
  FIRST_JVSG_NOTE_DATE: "date",
  LAST_JVSG_NOTE_DATE: "date",
  LATEST_FY_203_DATE: "date",
  LAST_CONTACT_DATE: "date",
  LAST_CONTACT_STAFF: "text",
  LAST_CONTACT_STAFF_NAME: "text",
  DAYS_SINCE_CONTACT: "int",
  FOLLOW_UP_BAND: "text",
  UNCERTAIN_FY205_EXISTS: "text",
  UNDATED_WP205_EXISTS: "text",
};

const KNOWN_BANDS = ["Overdue", "Due soon", "Current"];
const BAND_COLORS = ["#C0392B", "#E6A23C", "#2E8B57"];
const NAVY = "#1F3864";

function main(workbook: ExcelScript.Workbook, csvText: string): string {
  const rows = parseCsv(csvText);
  if (rows.length === 0) {
    throw new Error("The CSV is empty.");
  }
  const headers = rows[0].map((h) => h.trim().toUpperCase());
  const body = rows.slice(1);

  if (isManagerReport(headers)) {
    // A no_visible_groups result is a single row with blank counts.
    const countCol = headers.indexOf("INDIVIDUALS");
    const groups = body.filter((r) => (r[countCol] || "").trim() !== "");
    const loaded = writeDataTable(
      workbook, "Manager_Data", "tblManager", headers, groups, MANAGER_COLUMNS
    );
    buildDashboard(workbook, headers, loaded);
    return "manager report: " + loaded.length + " group rows loaded; Dashboard rebuilt.";
  }
  if (isWorklistReport(headers)) {
    if (workbook.getWorksheet("Dashboard")) {
      throw new Error(
        "This workbook has a Dashboard sheet. Run the worklist CSV in the restricted worklist workbook."
      );
    }
    const loaded = writeDataTable(
      workbook, "Worklist", "tblWorklist", headers, body, WORKLIST_COLUMNS
    );
    buildWorklistSummary(workbook, headers, loaded);
    return "worklist report: " + loaded.length + " rows loaded; Summary rebuilt.";
  }
  throw new Error("Unrecognized CSV header. Expected the manager or worklist report.");
}

function isManagerReport(headers: string[]): boolean {
  return headers.indexOf("INDIVIDUALS") >= 0 && headers.indexOf("INDIVIDUAL_RECORD_LWIA") >= 0;
}

function isWorklistReport(headers: string[]): boolean {
  return headers.indexOf("INDIVIDUAL_USERNAME") >= 0 && headers.indexOf("FOLLOW_UP_BAND") >= 0;
}

/** RFC 4180 style parser: quoted fields, doubled quotes, CRLF, optional BOM. */
function parseCsv(text: string): string[][] {
  const s = text.charCodeAt(0) === 0xfeff ? text.slice(1) : text;
  const rows: string[][] = [];
  let row: string[] = [];
  let field = "";
  let quoted = false;
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    if (quoted) {
      if (ch === '"') {
        if (s[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          quoted = false;
        }
      } else {
        field += ch;
      }
    } else if (ch === '"') {
      quoted = true;
    } else if (ch === ",") {
      row.push(field);
      field = "";
    } else if (ch === "\n" || ch === "\r") {
      if (ch === "\r" && s[i + 1] === "\n") {
        i++;
      }
      row.push(field);
      field = "";
      if (!(row.length === 1 && row[0] === "")) {
        rows.push(row);
      }
      row = [];
    } else {
      field += ch;
    }
  }
  if (field !== "" || row.length > 0) {
    row.push(field);
    rows.push(row);
  }
  return rows;
}

/** Converts MM/DD/YYYY or YYYY-MM-DD to an Excel date serial; otherwise returns the raw text. */
function toDateSerial(value: string): Cell {
  const v = value.trim();
  if (v === "") {
    return "";
  }
  let y = 0;
  let m = 0;
  let d = 0;
  let match = /^(\d{1,2})\/(\d{1,2})\/(\d{4})/.exec(v);
  if (match) {
    m = Number(match[1]);
    d = Number(match[2]);
    y = Number(match[3]);
  } else {
    match = /^(\d{4})-(\d{2})-(\d{2})/.exec(v);
    if (!match) {
      return v;
    }
    y = Number(match[1]);
    m = Number(match[2]);
    d = Number(match[3]);
  }
  return Date.UTC(y, m - 1, d) / 86400000 + 25569;
}

function toCell(value: string, type: ColType): Cell {
  const v = value.trim();
  if (type === "int") {
    if (v === "") {
      return "";
    }
    const n = Number(v);
    return isNaN(n) ? v : n;
  }
  if (type === "date") {
    return toDateSerial(v);
  }
  // A leading apostrophe stops Excel from treating text as a formula.
  return /^[=+@]/.test(v) ? "'" + v : v;
}

function columnLetter(index: number): string {
  let n = index + 1;
  let letters = "";
  while (n > 0) {
    const rem = (n - 1) % 26;
    letters = String.fromCharCode(65 + rem) + letters;
    n = Math.floor((n - 1) / 26);
  }
  return letters;
}

function numberFormatFor(type: ColType): string {
  return type === "date" ? "mm/dd/yyyy" : type === "int" ? "0" : "@";
}

/** Replaces the sheet's contents with the CSV as an Excel table. Returns the typed data rows. */
function writeDataTable(
  workbook: ExcelScript.Workbook,
  sheetName: string,
  tableName: string,
  headers: string[],
  body: string[][],
  spec: ColumnSpec
): Cell[][] {
  const existing = workbook.getTable(tableName);
  if (existing) {
    existing.delete();
  }
  let sheet = workbook.getWorksheet(sheetName);
  if (!sheet) {
    sheet = workbook.addWorksheet(sheetName);
  }
  sheet.getRange().clear();

  const types: ColType[] = headers.map((h) => spec[h] || "text");
  const data: Cell[][] = [];
  for (const row of body) {
    if (row.every((c) => c.trim() === "")) {
      continue;
    }
    data.push(headers.map((_, c) => toCell(row[c] === undefined ? "" : row[c], types[c])));
  }

  const headerRange = sheet.getRangeByIndexes(0, 0, 1, headers.length);
  headerRange.setNumberFormat("@");
  headerRange.setValues([headers]);
  if (data.length === 0) {
    return data;
  }
  headers.forEach((_, c) => {
    sheet.getRangeByIndexes(1, c, data.length, 1).setNumberFormat(numberFormatFor(types[c]));
  });
  sheet.getRangeByIndexes(1, 0, data.length, headers.length).setValues(data);

  const table = sheet.addTable(
    sheet.getRangeByIndexes(0, 0, data.length + 1, headers.length), true
  );
  table.setName(tableName);
  table.setPredefinedTableStyle("TableStyleMedium2");
  sheet.getFreezePanes().freezeRows(1);
  sheet.getRange().getFormat().autofitColumns();
  return data;
}

function styleTitle(sheet: ExcelScript.Worksheet, title: string, subtitle: string): void {
  const t = sheet.getRange("A1");
  t.setValue(title);
  t.getFormat().getFont().setBold(true);
  t.getFormat().getFont().setSize(18);
  t.getFormat().getFont().setColor(NAVY);
  const s = sheet.getRange("A2");
  s.setValue(subtitle);
  s.getFormat().getFont().setItalic(true);
  s.getFormat().getFont().setColor("#595959");
}

function styleHeaderRow(range: ExcelScript.Range): void {
  range.getFormat().getFill().setColor(NAVY);
  range.getFormat().getFont().setColor("#FFFFFF");
  range.getFormat().getFont().setBold(true);
  range.getFormat().setHorizontalAlignment(ExcelScript.HorizontalAlignment.center);
}

function freshSheet(workbook: ExcelScript.Workbook, name: string): ExcelScript.Worksheet {
  let sheet = workbook.getWorksheet(name);
  if (sheet) {
    sheet.getCharts().forEach((c) => c.delete());
    sheet.getRange().clear();
  } else {
    sheet = workbook.addWorksheet(name);
  }
  sheet.setShowGridlines(false);
  return sheet;
}

function bandOrder(found: string[]): string[] {
  const extras = found.filter((b) => KNOWN_BANDS.indexOf(b) < 0).sort();
  return KNOWN_BANDS.filter((b) => found.indexOf(b) >= 0).concat(extras);
}

function kpiBlock(
  sheet: ExcelScript.Worksheet,
  labels: string[],
  formulas: string[],
  formats: string[]
): void {
  labels.forEach((label, i) => {
    const l = sheet.getRangeByIndexes(4, i, 1, 1);
    l.setValue(label);
    l.getFormat().getFont().setColor("#595959");
    l.getFormat().getFont().setSize(10);
    const v = sheet.getRangeByIndexes(5, i, 1, 1);
    v.setFormula(formulas[i]);
    v.setNumberFormat(formats[i]);
    v.getFormat().getFont().setSize(20);
    v.getFormat().getFont().setBold(true);
    v.getFormat().getFont().setColor(NAVY);
    v.getFormat().setHorizontalAlignment(ExcelScript.HorizontalAlignment.left);
  });
}

function buildDashboard(workbook: ExcelScript.Workbook, headers: string[], data: Cell[][]): void {
  const sheet = freshSheet(workbook, "Dashboard");
  styleTitle(
    sheet,
    "JVSG FY2026 Non-Case-Managed Veteran Follow-Up",
    "Candidates for qualified human review. Not a decision, assignment, or referral."
  );
  if (data.length === 0) {
    sheet.getRange("A4").setValue(
      "No groups to display: every group was below the suppression threshold or the report returned no rows."
    );
    return;
  }

  const lwiaCol = headers.indexOf("LWIA_NAME");
  const codeCol = headers.indexOf("INDIVIDUAL_RECORD_LWIA");
  const bandCol = headers.indexOf("FOLLOW_UP_BAND");
  const labels: string[] = [];
  const found: string[] = [];
  for (const row of data) {
    const name = String(row[lwiaCol]) || String(row[codeCol]);
    if (labels.indexOf(name) < 0) {
      labels.push(name);
    }
    const band = String(row[bandCol]);
    if (found.indexOf(band) < 0) {
      found.push(band);
    }
  }
  labels.sort();
  const bands = bandOrder(found);

  const counts = "tblManager[INDIVIDUALS]";
  // Small groups are omitted from the aggregate report, so a band with no visible group
  // is not a confirmed zero; show "Suppressed" instead of 0.
  const bandTotal = (name: string): string =>
    '=IF(COUNTIFS(tblManager[FOLLOW_UP_BAND],"' + name + '")=0,"Suppressed",SUMIFS(' + counts +
    ',tblManager[FOLLOW_UP_BAND],"' + name + '"))';
  kpiBlock(
    sheet,
    ["As of", "Visible veterans", "Overdue", "Due soon", "Current", "Percent of visible overdue"],
    [
      "=MAX(tblManager[AS_OF_DATE])",
      "=SUM(" + counts + ")",
      bandTotal("Overdue"),
      bandTotal("Due soon"),
      bandTotal("Current"),
      '=IF(OR(B6=0,NOT(ISNUMBER(C6))),0,C6/B6)',
    ],
    ["mm/dd/yyyy", "#,##0", "#,##0", "#,##0", "#,##0", "0%"]
  );

  // Matrix: LWIA rows by band columns, live SUMIFS over the data table.
  const top = 8;
  const header = ["LWIA"].concat(bands, ["Total"]);
  const headerRange = sheet.getRangeByIndexes(top, 0, 1, header.length);
  headerRange.setValues([header]);
  styleHeaderRow(headerRange);

  const formulas: string[][] = labels.map((name, r) => {
    const rowNum = top + 2 + r;
    const cells = bands.map((_, b) => {
      const col = columnLetter(b + 1);
      return (
        "=SUMIFS(" + counts + ",tblManager[LWIA_NAME],$A" + rowNum +
        ",tblManager[FOLLOW_UP_BAND]," + col + "$" + (top + 1) + ")"
      );
    });
    const first = columnLetter(1);
    const last = columnLetter(bands.length);
    return cells.concat(["=SUM(" + first + rowNum + ":" + last + rowNum + ")"]);
  });
  sheet.getRangeByIndexes(top + 1, 0, labels.length, 1).setValues(labels.map((l) => [l]));
  sheet.getRangeByIndexes(top + 1, 1, labels.length, bands.length + 1).setFormulas(formulas);

  const totalRow = top + 1 + labels.length;
  const totals: string[] = [];
  for (let c = 1; c <= bands.length + 1; c++) {
    const col = columnLetter(c);
    totals.push("=SUM(" + col + (top + 2) + ":" + col + (totalRow) + ")");
  }
  sheet.getRangeByIndexes(totalRow, 0, 1, 1).setValue("All visible groups");
  sheet.getRangeByIndexes(totalRow, 1, 1, bands.length + 1).setFormulas([totals]);
  const totalRange = sheet.getRangeByIndexes(totalRow, 0, 1, header.length);
  totalRange.getFormat().getFont().setBold(true);
  totalRange.getFormat().getFill().setColor("#E7ECF5");
  sheet.getRangeByIndexes(top + 1, 1, labels.length + 1, bands.length + 1).setNumberFormat("#,##0");

  const chart = sheet.addChart(
    ExcelScript.ChartType.columnStacked,
    sheet.getRangeByIndexes(top, 0, labels.length + 1, bands.length + 1),
    ExcelScript.ChartSeriesBy.columns
  );
  chart.setName("FollowUpByLwia");
  chart.getTitle().setText("Veterans by LWIA and follow-up band");
  chart.setPosition("H4", "R22");
  chart.getSeries().forEach((series) => {
    const known = KNOWN_BANDS.indexOf(series.getName());
    series.getFormat().getFill().setSolidColor(known >= 0 ? BAND_COLORS[known] : "#7F8FA9");
  });

  const note = sheet.getRangeByIndexes(totalRow + 2, 0, 1, 1);
  note.setValue(
    "Groups below the suppression threshold are omitted, so totals cover visible groups only; " +
    "a band showing Suppressed has no visible group and is not a confirmed zero. " +
    "Bands are examples pending owner confirmation. LWIA is the veteran's record field."
  );
  note.getFormat().getFont().setItalic(true);
  note.getFormat().getFont().setColor("#595959");
  sheet.getRange("A:A").getFormat().setColumnWidth(230);
  sheet.getRange("B:G").getFormat().setColumnWidth(95);
  sheet.setPosition(0);
  sheet.activate();
}

function buildWorklistSummary(workbook: ExcelScript.Workbook, headers: string[], data: Cell[][]): void {
  const sheet = freshSheet(workbook, "Summary");
  styleTitle(
    sheet,
    "JVSG FY2026 Follow-Up Worklist",
    "Restricted: contains veteran identifiers. Candidates for qualified human review, not decisions."
  );
  const worklist = workbook.getWorksheet("Worklist");
  if (data.length === 0 || !worklist) {
    sheet.getRange("A4").setValue("The report returned no candidate rows.");
    return;
  }

  const bandCol = headers.indexOf("FOLLOW_UP_BAND");
  const officeCol = headers.indexOf("OFFICE_NAME");
  const bandRange = worklist.getRangeByIndexes(1, bandCol, data.length, 1);
  const colors = ["#F8D7DA", "#FFF3CD", "#D4EDDA"];
  KNOWN_BANDS.forEach((band, i) => {
    const cf = bandRange.addConditionalFormat(ExcelScript.ConditionalFormatType.containsText);
    cf.getTextComparison().getFormat().getFill().setColor(colors[i]);
    cf.getTextComparison().setRule({
      operator: ExcelScript.ConditionalTextOperator.contains,
      text: band,
    });
  });

  kpiBlock(
    sheet,
    ["As of", "Candidates", "Overdue", "Due soon", "Current", "No FY 203"],
    [
      "=MAX(tblWorklist[AS_OF_DATE])",
      "=ROWS(tblWorklist[INDIVIDUAL_USERNAME])",
      '=COUNTIFS(tblWorklist[FOLLOW_UP_BAND],"Overdue")',
      '=COUNTIFS(tblWorklist[FOLLOW_UP_BAND],"Due soon")',
      '=COUNTIFS(tblWorklist[FOLLOW_UP_BAND],"Current")',
      '=COUNTBLANK(tblWorklist[LATEST_FY_203_DATE])',
    ],
    ["mm/dd/yyyy", "#,##0", "#,##0", "#,##0", "#,##0", "#,##0"]
  );

  const offices: string[] = [];
  for (const row of data) {
    const name = String(row[officeCol]);
    if (offices.indexOf(name) < 0) {
      offices.push(name);
    }
  }
  offices.sort();
  const top = 8;
  const header = ["Office"].concat(KNOWN_BANDS, ["Total"]);
  const headerRange = sheet.getRangeByIndexes(top, 0, 1, header.length);
  headerRange.setValues([header]);
  styleHeaderRow(headerRange);
  sheet.getRangeByIndexes(top + 1, 0, offices.length, 1).setValues(offices.map((o) => [o]));
  const formulas: string[][] = offices.map((_, r) => {
    const rowNum = top + 2 + r;
    const cells = KNOWN_BANDS.map((__, b) => {
      const col = columnLetter(b + 1);
      return (
        "=COUNTIFS(tblWorklist[OFFICE_NAME],$A" + rowNum +
        ",tblWorklist[FOLLOW_UP_BAND]," + col + "$" + (top + 1) + ")"
      );
    });
    return cells.concat(["=SUM(B" + rowNum + ":D" + rowNum + ")"]);
  });
  sheet.getRangeByIndexes(top + 1, 1, offices.length, KNOWN_BANDS.length + 1).setFormulas(formulas);
  sheet.getRange("A:A").getFormat().setColumnWidth(260);
  sheet.getRange("B:G").getFormat().setColumnWidth(95);
  sheet.setPosition(0);
  sheet.activate();
}
