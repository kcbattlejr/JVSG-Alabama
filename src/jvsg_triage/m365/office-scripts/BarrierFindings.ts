/**
 * JVSG barrier findings (draft) - Office Script for Excel on the web.
 *
 * Reads the case-notes report sheet, scrubs each note, and writes barrier
 * SUGGESTIONS to the "Barrier Findings (Draft)" sheet. Every finding is written
 * as "Unverified" with a verbatim evidence quote from the scrubbed note. Nothing
 * here is a decision: a qualified person must Confirm, Correct or Reject each row,
 * and only Confirmed/Corrected rows may feed dashboard counts.
 *
 * Modes (parameter `mode`):
 *   extract - rules-based extractor (rules-v1); no model needed.
 *   scrub   - return scrubbed notes as JSON so an approved tenant model can label them.
 *   append  - validate model findings (JSON) against the contract, then append them.
 *
 * Keep this file self-contained: Office Scripts cannot import modules. The scrub
 * rules mirror src/jvsg_triage/privacy/scrubber.py and must be kept in step with it.
 */

interface Finding {
  note_row: number;
  domain: string;
  state: string;
  evidence_quote: string;
  source: string;
}

interface NoteRow {
  noteRow: number;
  stateId: string;
  contactDate: string;
  caseSubject: string;
  scrubbed: string;
}

interface Result {
  status: string;
  message: string;
  processed: number;
  added: number;
  skipped: number;
  rejected: number;
  nextRow: number;
  done: boolean;
  notesJson: string;
}

const FINDINGS_SHEET = "Barrier Findings (Draft)";
const FINDINGS_HEADER = [
  "finding_id", "note_row", "state_id", "contact_date", "case_subject", "domain",
  "state", "evidence_quote", "source", "verification_status", "reviewer_action",
  "corrected_domain", "corrected_state", "reviewer_role", "reviewed_on",
];
const DOMAINS = ["TRN", "HSG", "MED", "LEG"];
const STATES = ["CRT", "ACT", "MIT", "RES", "UNK"];
const ACTIONS = ["Confirm", "Correct", "Reject"];
const MAX_QUOTE = 400;
const MAX_BATCH = 100;
const EXTRACTOR = "rules-v1";

/* ---------------------------------------------------------------- scrubbing */

const MONTHS =
  "January|February|March|April|May|June|July|August|September|October|November|December|" +
  "Jan\\.?|Feb\\.?|Mar\\.?|Apr\\.?|Jun\\.?|Jul\\.?|Aug\\.?|Sept?\\.?|Oct\\.?|Nov\\.?|Dec\\.?";
const STREET =
  "Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd|Lane|Ln|Court|Ct|Highway|Hwy|" +
  "Way|Parkway|Pkwy|Circle|Cir|Place|Pl|Terrace|Trail|Loop|Plaza";
const HONORIFIC =
  "\\b(?:Mr|Mrs|Ms|Miss|Mx|Dr|Sgt|SGT|SSgt|SFC|MSG|CPT|Capt|LT|Lt|Col|COL|Maj|MAJ)\\.?";

const PLACEHOLDER_ORDER = [
  "EMAIL", "URL", "SSN", "PHONE", "DATE", "ADDRESS", "ZIP", "ID", "NAME", "STAFF",
];

const PATTERNS: [string, RegExp][] = [
  ["EMAIL", /[\w.+'-]+@[\w-]+(?:\.[\w-]+)+/g],
  ["URL", /\b(?:https?:\/\/|www\.)\S+/gi],
  ["SSN", /\b\d{3}-\d{2}-\d{4}\b/g],
  ["PHONE", new RegExp(
    "(?:(?:\\+?1[\\s.-]?)?(?:\\(\\d{3}\\)\\s?|\\b\\d{3}[\\s.-])\\d{3}[\\s.-]\\d{4}\\b" +
    "|\\b\\d{10}\\b|\\b\\d{3}-\\d{4}\\b)(?:\\s*(?:x|ext\\.?)\\s*\\d{1,5})?", "gi")],
  ["DATE", new RegExp(
    "\\b\\d{1,2}[/-]\\d{1,2}[/-](?:\\d{4}|\\d{2})\\b|\\b\\d{4}-\\d{2}-\\d{2}\\b" +
    "|\\b(?:" + MONTHS + ")\\s+\\d{1,2}(?:st|nd|rd|th)?(?:,?\\s+\\d{4})?\\b" +
    "|\\b\\d{1,2}(?:st|nd|rd|th)?\\s+(?:" + MONTHS + ")(?:,?\\s+\\d{4})?\\b", "g")],
  ["ADDRESS", new RegExp(
    "\\b(?:P\\.?\\s?O\\.?\\s+Box\\s+\\d+|\\d{1,6}(?:\\s+[A-Z0-9][\\w.'-]*){1,4}\\s+(?:" +
    STREET + ")\\b\\.?(?:,?\\s+(?:Apt|Apartment|Unit|Suite|Ste|Lot|#)\\.?\\s*[\\w-]+)?)", "g")],
  ["ZIP", /(?<=\b[A-Z]{2}\s|\b[A-Z]{2},\s|\bAl\s|Alabama\s)\d{5}(?:-\d{4})?\b/g],
  ["ID", /\b\d{5,}\b/g],
];
const HONORIFIC_NAME = new RegExp(HONORIFIC + "\\s+([A-Z][A-Za-z'\\-]+(?:\\s+[A-Z][A-Za-z'\\-]+)?)", "g");
// Extra guard beyond the Python scrubber: a referral or contact target named without an
// honorific ("Referred to First Last, ...") is a third party and is removed too.
const REFERRAL_NAME =
  /\b(?:[Rr]eferred to|[Ss]poke with|[Cc]ontacted|[Cc]all(?:ed)?|[Mm]et with)\s+([A-Z][a-z'-]+\s+[A-Z][a-z'-]+)(?=[,.;\s])/g;
const PLACEHOLDER = /\[(?:EMAIL|URL|SSN|PHONE|DATE|ADDRESS|ZIP|ID|NAME|STAFF)\]/g;

const NAME_STOPWORDS = (
  "January February March April May June July August September October November " +
  "December Monday Tuesday Wednesday Thursday Friday Saturday Sunday " +
  "Will Can Hope Job Case Mark Bill Grant Chase Major Mobile Alabama Veteran " +
  "Veterans Army Navy Marine Marines Air Force Good Thank Thanks Please Dear Hello " +
  "Best Regards Sincerely Career Center Services Service Fair Employment Training " +
  "Contact Office Specialist Program Jr Sr II III IV"
).toLowerCase().split(" ");

interface Span {
  start: number;
  end: number;
  label: string;
}

function escapeRegex(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function nameTokens(names: string[]): string[] {
  const tokens: string[] = [];
  for (const name of names) {
    for (const part of name.split(/[^A-Za-z'-]+/)) {
      for (const piece of [part].concat(part.split("-"))) {
        const token = piece.replace(/^['-]+|['-]+$/g, "");
        if (token.length >= 3 && NAME_STOPWORDS.indexOf(token.toLowerCase()) < 0
          && tokens.indexOf(token) < 0) {
          tokens.push(token);
        }
      }
    }
  }
  return tokens.sort((a, b) => b.length - a.length);
}

function wordRegex(tokens: string[]): RegExp | null {
  if (tokens.length === 0) {
    return null;
  }
  return new RegExp("(?<![\\w'])(?:" + tokens.map(escapeRegex).join("|") + ")(?![\\w])", "gi");
}

function collect(text: string, pattern: RegExp | null, label: string, spans: Span[]): void {
  if (!pattern) {
    return;
  }
  pattern.lastIndex = 0;
  let match: RegExpExecArray | null = pattern.exec(text);
  while (match !== null) {
    if (match[0].length === 0) {
      pattern.lastIndex += 1;
    } else {
      spans.push({ start: match.index, end: match.index + match[0].length, label });
    }
    match = pattern.exec(text);
  }
}

/** Replace PII with placeholders. `names` and `ids` come from the note's own row. */
function scrub(text: string, names: string[], staff: string[], ids: string[]): string {
  const spans: Span[] = [];
  for (const [label, pattern] of PATTERNS) {
    collect(text, pattern, label, spans);
  }
  const knownIds = ids.filter((id) => id.length >= 4);
  if (knownIds.length > 0) {
    collect(text, new RegExp("(?<!\\w)(?:" + knownIds.map(escapeRegex).join("|") + ")(?!\\w)", "g"),
      "ID", spans);
  }
  collect(text, wordRegex(nameTokens(names)), "NAME", spans);
  collect(text, wordRegex(nameTokens(staff)), "STAFF", spans);
  HONORIFIC_NAME.lastIndex = 0;
  let honorific: RegExpExecArray | null = HONORIFIC_NAME.exec(text);
  while (honorific !== null) {
    const start = honorific.index + honorific[0].length - honorific[1].length;
    spans.push({ start, end: start + honorific[1].length, label: "NAME" });
    honorific = HONORIFIC_NAME.exec(text);
  }
  REFERRAL_NAME.lastIndex = 0;
  let referral: RegExpExecArray | null = REFERRAL_NAME.exec(text);
  while (referral !== null) {
    const start = referral.index + referral[0].length - referral[1].length;
    spans.push({ start, end: start + referral[1].length, label: "NAME" });
    referral = REFERRAL_NAME.exec(text);
  }
  spans.sort((a, b) => a.start - b.start || b.end - a.end);
  const merged: Span[] = [];
  for (const span of spans) {
    const last = merged[merged.length - 1];
    if (last && span.start < last.end) {
      last.end = Math.max(last.end, span.end);
      if (PLACEHOLDER_ORDER.indexOf(span.label) < PLACEHOLDER_ORDER.indexOf(last.label)) {
        last.label = span.label;
      }
    } else {
      merged.push({ start: span.start, end: span.end, label: span.label });
    }
  }
  let out = "";
  let cursor = 0;
  for (const span of merged) {
    out += text.slice(cursor, span.start) + "[" + span.label + "]";
    cursor = span.end;
  }
  return out + text.slice(cursor);
}

/** True when the text still contains anything the structured detectors recognise. */
function hasResidualPii(scrubbed: string): boolean {
  const bare = scrubbed.replace(PLACEHOLDER, " ");
  const spans: Span[] = [];
  for (const [label, pattern] of PATTERNS) {
    collect(bare, pattern, label, spans);
  }
  return spans.length > 0;
}

/* --------------------------------------------------------------- extraction */

interface Rule {
  domain: string;
  test: RegExp;
  critical?: RegExp;
  mitigated?: RegExp;
}

// Closed rules over the existing TRN/HSG/MED/LEG vocabulary. Deliberately simple:
// reviewers verify every finding, and anything ambiguous is left unlabelled.
const RULES: Rule[] = [
  {
    domain: "TRN",
    test: /lacks? (?:reliable )?transportation|no (?:reliable )?(?:transportation|vehicle|ride)|without (?:a )?(?:car|vehicle|ride)|transportation (?:barrier|issue|problem)/i,
    mitigated: /referred|voucher|bus pass|arranged|provided/i,
  },
  {
    domain: "HSG",
    test: /unstable housing|homeless|eviction|unsheltered|couch.?surf|at risk of losing (?:housing|home)|HUD-VASH|SSVF/i,
    critical: /homeless|eviction|unsheltered|no place to (?:stay|live)/i,
    mitigated: /referred|assessment|case manager|placed|enrolled/i,
  },
  {
    domain: "MED",
    test: /service-connected|disability rating|medical (?:condition|barrier|appointment)|health (?:condition|issue|care)|PTSD|treatment|VA (?:claim|Medical Center)|injur/i,
    critical: /suicid|crisis|hospitali[sz]ed/i,
    mitigated: /enrolled|scheduled|appointment|receiving|approved/i,
  },
  {
    domain: "LEG",
    test: /justice involvement|record.?sealing|fair-chance|legal services|probation|parole|felony|expunge|warrant/i,
    critical: /\bwarrant\b|incarcerat/i,
    mitigated: /legal services|referred|will contact|scheduled/i,
  },
];
const RESOLVED = /no longer|resolved|has (?:obtained|secured)|now (?:has|have|living)|problem solved/i;
const NEGATED = /\b(?:denies|denied|does not (?:have|report)|doesn't have|no (?:current )?(?:barrier|need)s?)\b/i;

function splitSentences(text: string): string[] {
  return text.split(/(?<=[.!?])\s+|\n+/).map((s) => s.trim()).filter((s) => s.length > 0);
}

function classify(sentence: string, rule: Rule): string {
  if (RESOLVED.test(sentence)) {
    return "RES";
  }
  if (rule.critical && rule.critical.test(sentence)) {
    return "CRT";
  }
  if (rule.mitigated && rule.mitigated.test(sentence)) {
    return "MIT";
  }
  return "ACT";
}

function extract(note: NoteRow): Finding[] {
  const findings: Finding[] = [];
  const sentences = splitSentences(note.scrubbed);
  for (const rule of RULES) {
    for (const sentence of sentences) {
      if (rule.test.test(sentence) && !NEGATED.test(sentence) && sentence.length <= MAX_QUOTE) {
        findings.push({
          note_row: note.noteRow,
          domain: rule.domain,
          state: classify(sentence, rule),
          evidence_quote: sentence,
          source: EXTRACTOR,
        });
        break;
      }
    }
  }
  return findings;
}

/** Contract check shared by the extractor and model findings. Returns a reason or "". */
function violation(finding: Finding, scrubbed: string): string {
  if (DOMAINS.indexOf(finding.domain) < 0) {
    return "domain outside vocabulary";
  }
  if (STATES.indexOf(finding.state) < 0) {
    return "state outside vocabulary";
  }
  const quote = typeof finding.evidence_quote === "string" ? finding.evidence_quote : "";
  if (quote.length === 0 || quote.length > MAX_QUOTE) {
    return "evidence quote missing or too long";
  }
  if (scrubbed.indexOf(quote) < 0) {
    return "evidence quote not found in scrubbed note";
  }
  if (hasResidualPii(quote)) {
    return "evidence quote contains unscrubbed identifiers";
  }
  return "";
}

/* ------------------------------------------------------------ sheet handling */

function text(value: string | number | boolean): string {
  return String(value === null || value === undefined ? "" : value).replace(/\s+/g, " ").trim();
}

function findColumns(header: (string | number | boolean)[]): { [key: string]: number } {
  const wanted: { [key: string]: string } = {
    userid: "userid", individual: "individual", createdBy: "created by",
    contactDate: "contact date", lastEditedBy: "last edited by", stateId: "state id",
    caseSubject: "case subject", notes: "case notes",
  };
  const columns: { [key: string]: number } = {};
  header.forEach((cell, index) => {
    const label = text(cell).toLowerCase();
    for (const key of Object.keys(wanted)) {
      if (wanted[key] === label) {
        columns[key] = index;
      }
    }
  });
  return columns;
}

function findHeaderRow(sheet: ExcelScript.Worksheet): number {
  const width = sheet.getUsedRange().getColumnCount();
  const rows = sheet.getRangeByIndexes(0, 0, 15, width).getValues();
  for (let i = 0; i < rows.length; i++) {
    if (text(rows[i][0]).toLowerCase() === "userid" && findColumns(rows[i]).notes !== undefined) {
      return i;
    }
  }
  return -1;
}

/** Every participant and staff name in the report, like the Python lexicon. */
function sheetNames(sheet: ExcelScript.Worksheet, headerIndex: number, total: number,
  width: number, columns: { [key: string]: number }): { people: string[]; staff: string[] } {
  const count = total - headerIndex - 1;
  const people: string[] = [];
  const staff: string[] = [];
  if (count <= 0) {
    return { people, staff };
  }
  const values = sheet.getRangeByIndexes(headerIndex + 1, 0, count, width).getValues();
  const add = (list: string[], value: string): void => {
    if (value.length > 0 && list.indexOf(value) < 0) {
      list.push(value);
    }
  };
  values.forEach((row) => {
    add(people, text(row[columns.individual]));
    add(staff, text(row[columns.createdBy]));
    add(staff, text(row[columns.lastEditedBy]));
  });
  return { people, staff };
}

function readNotes(sheet: ExcelScript.Worksheet, headerIndex: number, startRow: number,
  maxRows: number): { notes: NoteRow[]; nextRow: number; done: boolean } {
  const width = sheet.getUsedRange().getColumnCount();
  const total = sheet.getUsedRange().getRowCount();
  const columns = findColumns(sheet.getRangeByIndexes(headerIndex, 0, 1, width).getValues()[0]);
  const lexicon = sheetNames(sheet, headerIndex, total, width, columns);
  const first = Math.max(startRow, headerIndex + 2); // 1-based sheet row after the header
  const count = Math.max(0, Math.min(maxRows, total - first + 1));
  const notes: NoteRow[] = [];
  if (count > 0) {
    const values = sheet.getRangeByIndexes(first - 1, 0, count, width).getValues();
    values.forEach((row, offset) => {
      const body = text(row[columns.notes]);
      if (body.length === 0 || /^total rows:/i.test(text(row[0]))) {
        return;
      }
      const stateId = text(row[columns.stateId]);
      const ids = [stateId, text(row[columns.userid])];
      const people = [text(row[columns.individual])].concat(lexicon.people);
      const staff = [text(row[columns.createdBy]), text(row[columns.lastEditedBy])]
        .concat(lexicon.staff);
      const scrubbed = scrub(String(row[columns.notes]), people, staff, ids);
      notes.push({
        noteRow: first + offset,
        stateId,
        contactDate: text(row[columns.contactDate]),
        caseSubject: scrub(text(row[columns.caseSubject]), people, [], ids),
        scrubbed,
      });
    });
  }
  const nextRow = first + count;
  return { notes, nextRow, done: nextRow > total };
}

function getFindingsSheet(workbook: ExcelScript.Workbook): ExcelScript.Worksheet {
  let sheet = workbook.getWorksheet(FINDINGS_SHEET);
  if (!sheet) {
    sheet = workbook.addWorksheet(FINDINGS_SHEET);
    sheet.getRangeByIndexes(0, 0, 1, FINDINGS_HEADER.length).setValues([FINDINGS_HEADER]);
  }
  return sheet;
}

function existingIds(sheet: ExcelScript.Worksheet): string[] {
  const rows = sheet.getUsedRange().getRowCount();
  if (rows < 2) {
    return [];
  }
  return sheet.getRangeByIndexes(1, 0, rows - 1, 1).getValues().map((r) => text(r[0]));
}

function appendFindings(sheet: ExcelScript.Worksheet, findings: Finding[],
  notes: { [row: number]: NoteRow }): { added: number; skipped: number } {
  const known = existingIds(sheet);
  const rows: (string | number)[][] = [];
  let skipped = 0;
  for (const finding of findings) {
    const id = finding.note_row + "|" + finding.domain;
    if (known.indexOf(id) >= 0) {
      skipped += 1; // never overwrite a row a reviewer may already have touched
      continue;
    }
    known.push(id);
    const note = notes[finding.note_row];
    rows.push([
      id, finding.note_row, note.stateId, note.contactDate, note.caseSubject, finding.domain,
      finding.state, finding.evidence_quote, finding.source, "Unverified", "", "", "", "", "",
    ]);
  }
  if (rows.length > 0) {
    const start = sheet.getUsedRange().getRowCount();
    sheet.getRangeByIndexes(start, 0, rows.length, FINDINGS_HEADER.length).setValues(rows);
    const action = sheet.getRangeByIndexes(start, 10, rows.length, 1);
    action.getDataValidation().setRule({ list: { inCellDropDown: true, source: ACTIONS.join(",") } });
  }
  return { added: rows.length, skipped };
}

function parseFindings(json: string): Finding[] {
  try {
    const parsed: unknown = JSON.parse(json);
    return Array.isArray(parsed) ? (parsed as Finding[]) : [];
  } catch (error) {
    return [];
  }
}

function result(partial: Partial<Result>): Result {
  return {
    status: "ok", message: "", processed: 0, added: 0, skipped: 0, rejected: 0, nextRow: 0,
    done: true, notesJson: "", ...partial,
  };
}

function main(
  workbook: ExcelScript.Workbook,
  mode: string,
  startRow: number,
  maxRows: number,
  sourceSheet: string,
  findingsJson: string,
): Result {
  if (["extract", "scrub", "append"].indexOf(mode) < 0) {
    return result({ status: "error", message: "mode must be extract, scrub or append" });
  }
  const sheet = sourceSheet ? workbook.getWorksheet(sourceSheet) : workbook.getWorksheets()[0];
  if (!sheet) {
    return result({ status: "error", message: "source sheet not found" });
  }
  const headerIndex = findHeaderRow(sheet);
  if (headerIndex < 0) {
    return result({ status: "error", message: "case notes header row not found" });
  }
  const batch = Math.max(1, Math.min(maxRows || 50, MAX_BATCH));
  const { notes, nextRow, done } = readNotes(sheet, headerIndex, startRow || 1, batch);
  const byRow: { [row: number]: NoteRow } = {};
  notes.forEach((note) => { byRow[note.noteRow] = note; });

  if (mode === "scrub") {
    const payload = notes.map((n) => ({ note_row: n.noteRow, text: n.scrubbed }));
    return result({ processed: notes.length, nextRow, done, notesJson: JSON.stringify(payload) });
  }

  const candidates: Finding[] = [];
  if (mode === "extract") {
    notes.forEach((note) => candidates.push(...extract(note)));
  } else {
    candidates.push(...parseFindings(findingsJson));
  }
  const accepted: Finding[] = [];
  let rejected = 0;
  for (const finding of candidates) {
    const note = byRow[finding.note_row];
    if (note && violation(finding, note.scrubbed) === "") {
      accepted.push(finding);
    } else {
      rejected += 1;
    }
  }
  const outcome = appendFindings(getFindingsSheet(workbook), accepted, byRow);
  return result({
    processed: notes.length, added: outcome.added, skipped: outcome.skipped, rejected, nextRow,
    done: mode === "append" ? true : done,
    message: "Findings are suggestions only; every row starts Unverified and needs human review.",
  });
}
