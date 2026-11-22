// Run: node --test src/jvsg_triage/m365/sharepoint_demo/tests/importer.test.mjs
// Loads the Office Script as text (types stripped), then drives it with a small
// in-memory fake of the ExcelScript objects it uses. Synthetic data only.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { stripTypeScriptTypes } from "node:module";
import test from "node:test";
import { fileURLToPath } from "node:url";

const here = (p) => fileURLToPath(new URL(p, import.meta.url));

function loadScript() {
  const source = stripTypeScriptTypes(
    readFileSync(here("../office-scripts/ImportJvsgCsv.ts"), "utf8")
  );
  const enums = {
    ChartType: { columnStacked: "columnStacked" },
    ChartSeriesBy: { columns: "columns" },
    HorizontalAlignment: { center: "center", left: "left" },
    ConditionalFormatType: { containsText: "containsText" },
    ConditionalTextOperator: { contains: "contains" },
  };
  return new Function(
    "ExcelScript",
    `${source}\nreturn { main, parseCsv, toDateSerial, toCell, columnLetter };`
  )(enums);
}

const colIndex = (letters) =>
  [...letters].reduce((n, ch) => n * 26 + ch.charCodeAt(0) - 64, 0) - 1;

function parseAddress(address) {
  const [a, b = a] = address.split(":");
  const split = (x) => {
    const m = /^([A-Z]+)(\d+)$/.exec(x);
    return m ? { c: colIndex(m[1]), r: Number(m[2]) - 1 } : null;
  };
  const p = split(a);
  const q = split(b);
  return p && q ? { r: p.r, c: p.c, rows: q.r - p.r + 1, cols: q.c - p.c + 1 } : null;
}

function makeWorkbook() {
  const sheets = new Map();
  const tables = new Map();
  const noop = () => proxy;
  const proxy = new Proxy(function () {}, {
    get: (_t, prop) => (prop === "then" ? undefined : noop),
    apply: noop,
  });

  function makeSheet(name) {
    const sheet = {
      name,
      cells: new Map(),
      formats: new Map(),
      charts: [],
      cf: 0,
    };
    const key = (r, c) => `${r},${c}`;
    const rangeAt = (r, c, rows, cols) => ({
      setValues: (v) => v.forEach((row, i) => row.forEach((x, j) => sheet.cells.set(key(r + i, c + j), x))),
      setValue: (x) => sheet.cells.set(key(r, c), x),
      setFormulas: (v) => v.forEach((row, i) => row.forEach((x, j) => sheet.cells.set(key(r + i, c + j), x))),
      setFormula: (x) => sheet.cells.set(key(r, c), x),
      setNumberFormat: (f) => {
        for (let i = 0; i < rows; i++) for (let j = 0; j < cols; j++) sheet.formats.set(key(r + i, c + j), f);
      },
      addConditionalFormat: () => {
        sheet.cf += 1;
        return proxy;
      },
      clear: () => {
        sheet.cells.clear();
        sheet.formats.clear();
      },
      getFormat: () => proxy,
    });
    Object.assign(sheet, {
      getRange: (address) => {
        const p = address ? parseAddress(address) : null;
        return p ? rangeAt(p.r, p.c, p.rows, p.cols) : rangeAt(0, 0, 1, 1);
      },
      getRangeByIndexes: rangeAt,
      addTable: (range, hasHeaders) => {
        const table = { name: "", hasHeaders, setName: (n) => ((table.name = n), tables.set(n, table)), setPredefinedTableStyle: noop, delete: () => tables.delete(table.name) };
        return table;
      },
      getFreezePanes: () => proxy,
      getCharts: () => sheet.charts,
      addChart: (type, range) => {
        const chart = { type, setName: noop, getTitle: noop, setPosition: noop, getSeries: () => [], delete: () => sheet.charts.splice(sheet.charts.indexOf(chart), 1) };
        sheet.charts.push(chart);
        return chart;
      },
      setShowGridlines: noop,
      setPosition: noop,
      activate: noop,
      get: (r, c) => sheet.cells.get(key(r, c)),
    });
    return sheet;
  }

  return {
    sheets,
    tables,
    getWorksheet: (n) => sheets.get(n),
    addWorksheet: (n) => {
      const s = makeSheet(n);
      sheets.set(n, s);
      return s;
    },
    getTable: (n) => tables.get(n),
  };
}

const { main, parseCsv, toDateSerial, toCell, columnLetter } = loadScript();
const sample = (p) => readFileSync(here(`../sample_csv/${p}`), "utf8");

test("parseCsv handles BOM, quotes, doubled quotes, CRLF and blank lines", () => {
  const rows = parseCsv('\ufeffA,B\r\n"x, y","say ""hi"""\r\n\r\nlast,');
  assert.deepEqual(rows, [["A", "B"], ["x, y", 'say "hi"'], ["last", ""]]);
});

test("dates become Excel serials; text keeps leading zeros and blocks formulas", () => {
  assert.equal(toDateSerial("11/20/2026"), 46346);
  assert.equal(toDateSerial("2026-11-20"), 46346);
  assert.equal(toDateSerial(""), "");
  assert.equal(toDateSerial("not a date"), "not a date");
  assert.equal(toCell("03", "text"), "03");
  assert.equal(toCell("=1+1", "text"), "'=1+1");
  assert.equal(toCell("12", "int"), 12);
  assert.equal(columnLetter(0), "A");
  assert.equal(columnLetter(27), "AB");
});

test("manager CSV loads a typed table and builds live dashboard formulas", () => {
  const wb = makeWorkbook();
  const message = main(wb, sample("manager/synthetic_manager_report.csv"));
  assert.match(message, /6 group rows/);

  const data = wb.sheets.get("Manager_Data");
  assert.ok(wb.tables.has("tblManager"));
  assert.equal(data.get(1, 5), "A1");
  assert.equal(data.get(5, 6), "Demo Area East, Central");
  assert.equal(data.get(1, 8), 41);
  assert.equal(data.get(1, 2), 45931);
  assert.equal(data.formats.get("1,5"), "@");

  const dash = wb.sheets.get("Dashboard");
  assert.equal(dash.charts.length, 1);
  assert.equal(dash.get(5, 1), "=SUM(tblManager[INDIVIDUALS])");
  assert.deepEqual([8, 1, 2, 3, 4].map((i) => dash.get(8, i === 8 ? 0 : i)), ["LWIA", "Overdue", "Due soon", "Current", "Total"]);
  assert.deepEqual([9, 10, 11].map((r) => dash.get(r, 0)), ["Demo Area East, Central", "Demo Area North", "Demo Area South"]);
  assert.equal(
    dash.get(9, 1),
    "=SUMIFS(tblManager[INDIVIDUALS],tblManager[LWIA_NAME],$A10,tblManager[FOLLOW_UP_BAND],B$9)"
  );
  assert.equal(dash.get(9, 4), "=SUM(B10:D10)");
  assert.equal(dash.get(12, 0), "All visible groups");
  assert.equal(dash.get(12, 1), "=SUM(B10:B12)");
});

test("rerunning replaces the table instead of duplicating it", () => {
  const wb = makeWorkbook();
  main(wb, sample("manager/synthetic_manager_report.csv"));
  main(wb, sample("manager/synthetic_manager_report.csv"));
  assert.equal(wb.tables.size, 1);
  assert.equal(wb.sheets.get("Dashboard").charts.length, 1);
});

test("manager report with no visible groups shows a message, not a zero chart", () => {
  const wb = makeWorkbook();
  const csv =
    "REPORT_ID,RESULT_STATUS,FY_START,FY_END,AS_OF_DATE,INDIVIDUAL_RECORD_LWIA,LWIA_NAME,FOLLOW_UP_BAND,INDIVIDUALS\n" +
    "DEMO,no_visible_groups,10/01/2025,09/30/2026,11/20/2026,,,,\n";
  main(wb, csv);
  const dash = wb.sheets.get("Dashboard");
  assert.match(String(dash.get(3, 0)), /No groups to display/);
  assert.equal(dash.charts.length, 0);
});

test("worklist CSV keeps ids as text and builds the restricted summary", () => {
  const wb = makeWorkbook();
  const message = main(wb, sample("worklist/synthetic_worklist_report.csv"));
  assert.match(message, /8 rows/);
  const list = wb.sheets.get("Worklist");
  assert.equal(list.get(1, 5), "000100001");
  assert.equal(list.get(1, 7), "0101");
  assert.equal(list.get(1, 13), "");
  assert.equal(list.get(2, 13), 46042);
  assert.equal(list.get(4, 16), "Demo Staff, Three");
  assert.equal(list.cf, 3);
  const summary = wb.sheets.get("Summary");
  assert.equal(summary.get(5, 2), '=COUNTIFS(tblWorklist[FOLLOW_UP_BAND],"Overdue")');
  assert.deepEqual([9, 10, 11].map((r) => summary.get(r, 0)), ["Demo Office East", "Demo Office North", "Demo Office South"]);
});

test("synthetic worklist notes and 203 dates fall within the fiscal year", () => {
  const [headers, ...rows] = parseCsv(sample("worklist/synthetic_worklist_report.csv"));
  const field = (row, name) => row[headers.indexOf(name)];
  for (const row of rows) {
    const start = toDateSerial(field(row, "FY_START"));
    const end = toDateSerial(field(row, "FY_END"));
    for (const name of ["FIRST_JVSG_NOTE_DATE", "LAST_JVSG_NOTE_DATE", "LATEST_FY_203_DATE"]) {
      const value = field(row, name);
      if (value) {
        const date = toDateSerial(value);
        assert.ok(typeof date === "number" && date >= start && date <= end, `${name} outside FY`);
      }
    }
  }
});

test("worklist identifiers are refused in the dashboard workbook", () => {
  const wb = makeWorkbook();
  main(wb, sample("manager/synthetic_manager_report.csv"));
  assert.throws(() => main(wb, sample("worklist/synthetic_worklist_report.csv")), /Dashboard sheet/);
  assert.equal(wb.sheets.has("Worklist"), false);
});

test("unknown and empty CSVs are rejected", () => {
  assert.throws(() => main(makeWorkbook(), "A,B\n1,2\n"), /Unrecognized/);
  assert.throws(() => main(makeWorkbook(), ""), /empty/);
});

test("detail formula repair targets only helper cells with full-column references", () => {
  const source = stripTypeScriptTypes(
    readFileSync(here("../office-scripts/RepairDetailFormulas.ts"), "utf8")
  );
  const repair = new Function("ExcelScript", `${source}\nreturn main;`)({
    CalculationType: { full: "full" },
  });
  const written = new Map();
  const sheet = (name) => ({
    getRange: (address) => ({ setFormulas: (formulas) => written.set(`${name}!${address}`, formulas) }),
  });
  let calculation;
  const workbook = {
    getWorksheet: (name) => sheet(name),
    getTable: (name) => name === "Worklist" ? {} : undefined,
    getApplication: () => ({ calculate: (type) => { calculation = type; } }),
  };
  repair(workbook);

  assert.deepEqual([...written.keys()], ["Watchlist!K5:K54", "Drilldown!K10:K109"]);
  const watchlist = written.get("Watchlist!K5:K54");
  const drilldown = written.get("Drilldown!K10:K109");
  assert.equal(watchlist.length, 50);
  assert.equal(drilldown.length, 100);
  assert.match(watchlist[0][0], /Worklist\[DAYS_SINCE_CONTACT\].*\$A5/);
  assert.match(watchlist[49][0], /\$A54/);
  assert.match(drilldown[0][0], /Worklist\[OFFICE_NAME\].*\$A10/);
  assert.match(drilldown[99][0], /\$A109/);
  for (const [formula] of [...watchlist, ...drilldown]) {
    assert.doesNotMatch(formula, /#This Row|_xlfn\.SINGLE|@/);
  }
  assert.equal(calculation, "full");
  assert.throws(() => repair({ ...workbook, getTable: () => undefined }), /requires/);
});
