// Offline harness: runs BarrierFindings.ts against an in-memory fake of the Excel
// Office Scripts API. Reads {sheets, calls} JSON from stdin, writes results to stdout.
import { readFileSync } from "node:fs";
import { stripTypeScriptTypes } from "node:module";
import vm from "node:vm";

const here = new URL(".", import.meta.url);
const source = readFileSync(new URL("../office-scripts/BarrierFindings.ts", here), "utf8");
const code = stripTypeScriptTypes(source, { mode: "strip" });
const context = vm.createContext({ console });
vm.runInContext(`${code}\nthis.__main = main;`, context);

class FakeRange {
  constructor(sheet, r, c, h, w) {
    Object.assign(this, { sheet, r, c, h, w });
  }
  getValues() {
    return Array.from({ length: this.h }, (_, i) =>
      Array.from({ length: this.w }, (_, j) => this.sheet.rows[this.r + i]?.[this.c + j] ?? ""));
  }
  setValues(values) {
    values.forEach((row, i) => {
      this.sheet.rows[this.r + i] ??= [];
      row.forEach((value, j) => { this.sheet.rows[this.r + i][this.c + j] = value; });
    });
  }
  getDataValidation() { return { setRule: () => {} }; }
}

class FakeSheet {
  constructor(name, rows) { this.name = name; this.rows = rows; }
  getUsedRange() {
    const width = Math.max(0, ...this.rows.map((r) => r.length));
    return { getRowCount: () => this.rows.length, getColumnCount: () => width };
  }
  getRangeByIndexes(r, c, h, w) { return new FakeRange(this, r, c, h, w); }
}

class FakeWorkbook {
  constructor(sheets) {
    this.sheets = Object.entries(sheets).map(([n, rows]) => new FakeSheet(n, rows));
  }
  getWorksheets() { return this.sheets; }
  getWorksheet(name) { return this.sheets.find((s) => s.name === name); }
  addWorksheet(name) {
    const sheet = new FakeSheet(name, []);
    this.sheets.push(sheet);
    return sheet;
  }
}

const input = JSON.parse(readFileSync(0, "utf8"));
const workbook = new FakeWorkbook(input.sheets);
const results = input.calls.map((call) => context.__main(
  workbook, call.mode, call.startRow, call.maxRows, call.sourceSheet ?? "",
  call.findingsJson ?? "",
));
const findings = workbook.getWorksheet("Barrier Findings (Draft)");
console.log(JSON.stringify({ results, findings: findings ? findings.rows : null }));
