import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = "/Users/edy/Documents/my_finance/launch-kit/ai-resume-100";
const outputDir = path.join(root, "outputs");
await fs.mkdir(outputDir, { recursive: true });

const workbook = Workbook.create();
const dashboard = workbook.worksheets.add("Dashboard");
const leads = workbook.worksheets.add("Leads");
const daily = workbook.worksheets.add("Daily Review");
const pricing = workbook.worksheets.add("Pricing");

for (const sheet of [dashboard, leads, daily, pricing]) {
  sheet.showGridLines = false;
}

const colors = {
  ink: "#111827",
  muted: "#6B7280",
  line: "#D1D5DB",
  header: "#0F766E",
  headerSoft: "#CCFBF1",
  panel: "#F8FAFC",
  input: "#FFF7ED",
  success: "#DCFCE7",
  warn: "#FEF3C7",
  danger: "#FEE2E2",
};

function title(sheet, range, text) {
  const r = sheet.getRange(range);
  r.merge();
  r.values = [[text]];
  r.format.fill.color = colors.header;
  r.format.font.color = "#FFFFFF";
  r.format.font.bold = true;
  r.format.font.size = 16;
  r.format.rowHeight = 30;
  r.format.horizontalAlignment = "left";
}

function styleHeader(range) {
  range.format.fill.color = colors.headerSoft;
  range.format.font.bold = true;
  range.format.font.color = colors.ink;
  range.format.borders = { preset: "outside", style: "thin", color: colors.line };
  range.format.wrapText = true;
}

function styleBlock(range) {
  range.format.fill.color = colors.panel;
  range.format.borders = { preset: "outside", style: "thin", color: colors.line };
}

title(dashboard, "A1:H1", "AI 简历优化 7 天验证 Dashboard");
dashboard.getRange("A3:B8").values = [
  ["目标", "每天净收入 100 元+"],
  ["验证周期", "7 天"],
  ["主推套餐", "69 元单页优化 / 129 元岗位定制"],
  ["成功标准", "7 天内至少 2 天收入 100 元+"],
  ["服务边界", "不伪造经历，不承诺 offer"],
  ["下一步", "每天晚上填写 Daily Review"],
];
styleBlock(dashboard.getRange("A3:B8"));
dashboard.getRange("A3:A8").format.font.bold = true;

dashboard.getRange("D3:H3").values = [["Metric", "Formula", "Target", "Current", "Status"]];
styleHeader(dashboard.getRange("D3:H3"));
dashboard.getRange("D4:H10").values = [
  ["Total Leads", "咨询总数", 35, null, null],
  ["Total Orders", "成交总数", 7, null, null],
  ["Total Revenue", "成交收入", 700, null, null],
  ["Days >=100", "日收入达标天数", 2, null, null],
  ["Avg Delivery Minutes", "平均交付分钟", 60, null, null],
  ["Close Rate", "成交率", 0.2, null, null],
  ["Next Action", "按指标判断优化方向", null, null, null],
];
dashboard.getRange("G4:G9").formulas = [
  ["=COUNTA(Leads!A2:A501)"],
  ['=COUNTIF(Leads!I2:I501,"成交")'],
  ["=SUM(Leads!H2:H501)"],
  ['=COUNTIF(\'Daily Review\'!G2:G8,"达标")'],
  ["=IFERROR(AVERAGEIF(Leads!I2:I501,\"成交\",Leads!J2:J501),0)"],
  ["=IFERROR(G5/G4,0)"],
];
dashboard.getRange("H4:H9").formulas = [
  ['=IF(G4>=F4,"OK","Need leads")'],
  ['=IF(G5>=F5,"OK","Need orders")'],
  ['=IF(G6>=F6,"OK","Need revenue")'],
  ['=IF(G7>=F7,"OK","Need 100+ days")'],
  ['=IF(G8<=F8,"OK","Too slow")'],
  ['=IF(G9>=F9,"OK","Improve close")'],
];
dashboard.getRange("G10").formulas = [['=IF(G4<5,"换标题/封面/关键词",IF(G9<0.2,"调整报价和案例",IF(G8>60,"砍掉复杂服务","继续加码发布")))']];
dashboard.getRange("F6:G6").setNumberFormat('"¥"#,##0');
dashboard.getRange("F9:G9").setNumberFormat("0%");
dashboard.getRange("D4:H10").format.borders = { preset: "all", style: "thin", color: colors.line };
dashboard.getRange("D4:D10").format.font.bold = true;

dashboard.getRange("A11:H11").values = [["今晚执行清单", "", "", "", "", "", "", ""]];
dashboard.getRange("A11:H11").merge();
styleHeader(dashboard.getRange("A11:H11"));
dashboard.getRange("A12:H17").values = [
  ["1", "闲鱼上架 3 个标题", "用 day1-assets/xianyu-listing.md", "", "", "", "", ""],
  ["2", "小红书发 2 篇笔记", "先发避坑和前后对比", "", "", "", "", ""],
  ["3", "保存客服话术", "复制 scripts/chat-replies.md", "", "", "", "", ""],
  ["4", "记录每个咨询", "填 Leads 表", "", "", "", "", ""],
  ["5", "晚上复盘", "填 Daily Review 表", "", "", "", "", ""],
  ["6", "按 Dashboard Next Action 调整", "只改一个变量", "", "", "", "", ""],
];
styleBlock(dashboard.getRange("A12:H17"));

leads.getRange("A1:L1").values = [[
  "Date", "Platform", "Lead Name", "Need", "Package", "Quoted Price", "Discount", "Paid Amount", "Status", "Delivery Minutes", "Reject Reason", "Next Follow-up"
]];
styleHeader(leads.getRange("A1:L1"));
leads.getRange("A2:L8").values = Array.from({ length: 7 }, () => [
  null, "", "", "", "", null, null, null, "", null, "", "",
]);
leads.getRange("A2:A501").setNumberFormat("yyyy-mm-dd");
leads.getRange("F2:H501").setNumberFormat('"¥"#,##0');
leads.getRange("J2:J501").setNumberFormat("0");
leads.getRange("A1:L501").format.borders = { preset: "all", style: "thin", color: colors.line };
leads.getRange("D2:E501").format.wrapText = true;
leads.freezePanes.freezeRows(1);
leads.tables.add("A1:L501", true, "LeadsTable");
leads.getRange("B2:B501").dataValidation = { rule: { type: "list", values: ["闲鱼", "小红书", "朋友转介绍", "其他"] } };
leads.getRange("E2:E501").dataValidation = { rule: { type: "list", values: ["诊断", "单页优化", "岗位定制", "急单加价"] } };
leads.getRange("I2:I501").dataValidation = { rule: { type: "list", values: ["沟通中", "成交", "未成交", "已交付", "复购"] } };

daily.getRange("A1:I1").values = [[
  "Day", "Date", "Xianyu Posts/Refresh", "XHS Posts", "Leads", "Orders", "Revenue", "Status", "Action"
]];
styleHeader(daily.getRange("A1:I1"));
daily.getRange("A2:I8").values = [
  ["Day 1", new Date("2026-06-22"), 3, 2, null, null, null, null, "上架3个闲鱼商品，发2篇小红书"],
  ["Day 2", new Date("2026-06-23"), 3, 2, null, null, null, null, "测关键词：应届生/急单/岗位定制"],
  ["Day 3", new Date("2026-06-24"), 3, 1, null, null, null, null, "加入匿名案例和适合人群"],
  ["Day 4", new Date("2026-06-25"), 3, 1, null, null, null, null, "咨询多无成交则改49/69首单"],
  ["Day 5", new Date("2026-06-26"), 3, 1, null, null, null, null, "交付超60分钟则只接单页"],
  ["Day 6", new Date("2026-06-27"), 3, 1, null, null, null, null, "做复购和转介绍"],
  ["Day 7", new Date("2026-06-28"), 3, 1, null, null, null, null, "复盘是否继续加码"],
];
daily.getRange("E2:E8").formulas = [
  ['=COUNTIF(Leads!A:A,B2)'],
  ['=COUNTIF(Leads!A:A,B3)'],
  ['=COUNTIF(Leads!A:A,B4)'],
  ['=COUNTIF(Leads!A:A,B5)'],
  ['=COUNTIF(Leads!A:A,B6)'],
  ['=COUNTIF(Leads!A:A,B7)'],
  ['=COUNTIF(Leads!A:A,B8)'],
];
daily.getRange("F2:F8").formulas = [
  ['=COUNTIFS(Leads!A:A,B2,Leads!I:I,"成交")'],
  ['=COUNTIFS(Leads!A:A,B3,Leads!I:I,"成交")'],
  ['=COUNTIFS(Leads!A:A,B4,Leads!I:I,"成交")'],
  ['=COUNTIFS(Leads!A:A,B5,Leads!I:I,"成交")'],
  ['=COUNTIFS(Leads!A:A,B6,Leads!I:I,"成交")'],
  ['=COUNTIFS(Leads!A:A,B7,Leads!I:I,"成交")'],
  ['=COUNTIFS(Leads!A:A,B8,Leads!I:I,"成交")'],
];
daily.getRange("G2:G8").formulas = [
  ["=SUMIF(Leads!A:A,B2,Leads!H:H)"],
  ["=SUMIF(Leads!A:A,B3,Leads!H:H)"],
  ["=SUMIF(Leads!A:A,B4,Leads!H:H)"],
  ["=SUMIF(Leads!A:A,B5,Leads!H:H)"],
  ["=SUMIF(Leads!A:A,B6,Leads!H:H)"],
  ["=SUMIF(Leads!A:A,B7,Leads!H:H)"],
  ["=SUMIF(Leads!A:A,B8,Leads!H:H)"],
];
daily.getRange("H2:H8").formulas = [
  ['=IF(G2>=100,"达标","未达标")'],
  ['=IF(G3>=100,"达标","未达标")'],
  ['=IF(G4>=100,"达标","未达标")'],
  ['=IF(G5>=100,"达标","未达标")'],
  ['=IF(G6>=100,"达标","未达标")'],
  ['=IF(G7>=100,"达标","未达标")'],
  ['=IF(G8>=100,"达标","未达标")'],
];
daily.getRange("B2:B8").setNumberFormat("yyyy-mm-dd");
daily.getRange("G2:G8").setNumberFormat('"¥"#,##0');
daily.getRange("A1:I8").format.borders = { preset: "all", style: "thin", color: colors.line };
daily.freezePanes.freezeRows(1);
daily.tables.add("A1:I8", true, "DailyReviewTable");

pricing.getRange("A1:F1").values = [["Package", "Price", "Delivery", "Included Revision", "Best For", "Boundary"]];
styleHeader(pricing.getRange("A1:F1"));
pricing.getRange("A2:F5").values = [
  ["诊断", 29, "8-12个问题 + 3个建议 + 1个示例改写", 0, "预算低/先判断问题", "不重写全文"],
  ["单页优化", 69, "1页Word/PDF + 修改说明", 1, "马上投递", "不换岗位重做"],
  ["岗位定制", 129, "按JD改个人优势/经历/关键词", 2, "有明确JD", "不伪造经历和数据"],
  ["急单加价", 30, "2小时内交付", 0, "今晚投递", "需资料齐全"],
];
pricing.getRange("B2:B5").setNumberFormat('"¥"#,##0');
pricing.getRange("A1:F5").format.borders = { preset: "all", style: "thin", color: colors.line };
pricing.getRange("C2:F5").format.wrapText = true;
pricing.tables.add("A1:F5", true, "PricingTable");

leads.getRange("N1:O4").values = [
  ["填写示例", ""],
  ["Date", "2026-06-22"],
  ["Platform", "闲鱼 / 小红书"],
  ["Status", "沟通中 / 成交 / 未成交 / 已交付 / 复购"],
];
styleHeader(leads.getRange("N1:O1"));
styleBlock(leads.getRange("N2:O4"));
leads.getRange("N:O").format.columnWidth = 20;

for (const sheet of [dashboard, leads, daily, pricing]) {
  const used = sheet.getUsedRange();
  used.format.font.name = "Arial";
  used.format.font.size = 10;
  used.format.verticalAlignment = "top";
  used.format.autofitColumns();
  used.format.autofitRows();
}

dashboard.getRange("A:A").format.columnWidth = 16;
dashboard.getRange("B:B").format.columnWidth = 38;
dashboard.getRange("D:H").format.columnWidth = 18;
leads.getRange("A:A").format.columnWidth = 12;
leads.getRange("D:D").format.columnWidth = 28;
leads.getRange("K:L").format.columnWidth = 24;
daily.getRange("I:I").format.columnWidth = 34;
pricing.getRange("C:F").format.columnWidth = 28;

const inspection = await workbook.inspect({
  kind: "workbook,sheet,table",
  maxChars: 5000,
  tableMaxRows: 5,
  tableMaxCols: 8,
});
console.log(inspection.ndjson);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  maxChars: 2000,
});
console.log(errors.ndjson);

for (const sheetName of ["Dashboard", "Leads", "Daily Review", "Pricing"]) {
  const preview = await workbook.render({ sheetName, autoCrop: "all", scale: 1, format: "png" });
  const bytes = new Uint8Array(await preview.arrayBuffer());
  await fs.writeFile(path.join(outputDir, `${sheetName.replaceAll(" ", "_").toLowerCase()}_preview.png`), bytes);
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(path.join(outputDir, "ai_resume_validation_tracker.xlsx"));
console.log(`saved ${path.join(outputDir, "ai_resume_validation_tracker.xlsx")}`);
