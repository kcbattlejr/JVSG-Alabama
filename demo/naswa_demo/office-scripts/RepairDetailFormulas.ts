function main(workbook: ExcelScript.Workbook): void {
  const watchlist = workbook.getWorksheet("Watchlist");
  const drilldown = workbook.getWorksheet("Drilldown");
  if (!watchlist || !drilldown || !workbook.getTable("Worklist")) {
    throw new Error('This repair requires the Watchlist and Drilldown sheets and the Worklist table.');
  }

  const watchlistFormulas: string[][] = [];
  for (let row = 5; row <= 54; row++) {
    watchlistFormulas.push([
      '=IFERROR(AGGREGATE(14,6,(Worklist[DAYS_SINCE_CONTACT]+ROW(Worklist[STATE_ID])/1000000)' +
      '/(Worklist[FOLLOW_UP_BAND]="Overdue"),$A' + row + '),"")',
    ]);
  }

  const drilldownFormulas: string[][] = [];
  for (let row = 10; row <= 109; row++) {
    drilldownFormulas.push([
      '=IFERROR(AGGREGATE(15,6,ROW(Worklist[STATE_ID])' +
      '/((Worklist[OFFICE_NAME]=$B$4)+($B$4="")>0)' +
      '/((Worklist[FOLLOW_UP_BAND]=$B$5)+($B$5="")>0)' +
      '/(Worklist[DAYS_SINCE_CONTACT]>=$B$6),$A' + row + '),"")',
    ]);
  }

  watchlist.getRange("K5:K54").setFormulas(watchlistFormulas);
  drilldown.getRange("K10:K109").setFormulas(drilldownFormulas);
  workbook.getApplication().calculate(ExcelScript.CalculationType.full);
}