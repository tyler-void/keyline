// Adapted from audit 02's stress-corpus/src/pgx_slop.js: output paths, test photo and the Tyler author only (see _stress.py).
// D20: pptxgenjs, the kind of deck an AI generator emits.
// 1 cover
// 2 title + short accent bar 0.12 in under it (title-underline expected)
// 3 four equal cards, text in separate text boxes centred over them (equal-card-row expected)
// 4 three equal cards joined by right-arrow shapes (not connectors)
// 5 three equal cards joined by pptxgenjs line shapes
// 6 a table that runs 2 in off the right edge, and a chart that runs 1 in off the bottom
// 7 title underline drawn as a 3 pt line (not a filled shape)
const pptxgen = require("pptxgenjs");
const out = process.argv[2] || require("path").join(__dirname, "..", "d20_pgx_slop.pptx");
const pptx = new pptxgen();
pptx.author = "Tyler"; // then run: python _stress.py retag <out> (sets lastModifiedBy too)
pptx.layout = "LAYOUT_WIDE";
const T = (s, t) => s.addText(t, { x: 0.6, y: 0.6, w: 12.1, h: 0.9, fontSize: 36, bold: true, color: "111111", margin: 0 });
const body = (s, t, y) => s.addText(t, { x: 0.6, y: y || 5.9, w: 12.1, h: 0.9, fontSize: 20, color: "333333" });

let s = pptx.addSlide();
s.addText("Generated deck", { x: 1, y: 2.8, w: 11.3, h: 1.2, fontSize: 44, bold: true });
s.addNotes("cover");

s = pptx.addSlide(); T(s, "Accent bar under the title");
s.addShape(pptx.ShapeType.rect, { x: 0.6, y: 1.6, w: 1.2, h: 0.12, fill: { color: "E8422E" }, line: { color: "E8422E" } });
body(s, "Body text sits below the accent bar and fills the slide area", 2.2);
s.addText("A second block of text keeps the lower part of the slide in use", { x: 0.6, y: 4.2, w: 12.1, h: 2.4, fontSize: 20 });
s.addNotes("bar");

s = pptx.addSlide(); T(s, "Four pillars");
for (let i = 0; i < 4; i++) {
  const x = 0.6 + i * 3.1;
  s.addShape(pptx.ShapeType.roundRect, { x, y: 1.9, w: 2.8, h: 3.6, fill: { color: "EEF2FF" }, line: { color: "C7D2FE" }, rectRadius: 0.1 });
  s.addText(["Speed", "Cost", "Quality", "Trust"][i], { x, y: 1.9, w: 2.8, h: 3.6, fontSize: 24, bold: true, align: "center", valign: "middle", color: "1E1B4B" });
}
body(s, "Each pillar has one owner and one measurable target for the year");
s.addNotes("cards");

s = pptx.addSlide(); T(s, "Three steps with arrows");
for (let i = 0; i < 3; i++) {
  const x = 0.6 + i * 4.3;
  s.addText(["Plan", "Build", "Ship"][i], { shape: pptx.ShapeType.rect, x, y: 1.9, w: 3.3, h: 3.6, fill: { color: "1F4E79" }, color: "FFFFFF", fontSize: 28, align: "center" });
  if (i < 2) s.addShape(pptx.ShapeType.rightArrow, { x: x + 3.4, y: 3.4, w: 0.8, h: 0.6, fill: { color: "999999" } });
}
body(s, "Work moves from left to right through three stages every sprint");
s.addNotes("arrows");

s = pptx.addSlide(); T(s, "Three steps with lines");
for (let i = 0; i < 3; i++) {
  const x = 0.6 + i * 4.3;
  s.addText(["Plan", "Build", "Ship"][i], { shape: pptx.ShapeType.rect, x, y: 1.9, w: 3.3, h: 3.6, fill: { color: "1F4E79" }, color: "FFFFFF", fontSize: 28, align: "center" });
  if (i < 2) s.addShape(pptx.ShapeType.line, { x: x + 3.3, y: 3.7, w: 1.0, h: 0, line: { color: "333333", width: 2, endArrowType: "triangle" } });
}
body(s, "Work moves from left to right through three stages every sprint");
s.addNotes("lines");

s = pptx.addSlide(); T(s, "Overflowing table and chart");
s.addTable([["Region", "Q1", "Q2", "Q3", "Q4"], ["North", "12", "14", "15", "18"], ["South", "9", "11", "10", "12"]],
  { x: 0.6, y: 1.8, w: 8.0 + 6.7, h: 2.0, fontSize: 18 }); // right edge 15.3 in on a 13.333 in slide
s.addChart(pptx.ChartType.bar, [{ name: "Units", labels: ["A", "B", "C"], values: [3, 5, 4] }],
  { x: 0.6, y: 4.1, w: 6.0, h: 4.4 }); // bottom 8.5 in on a 7.5 in slide
s.addNotes("overflow");

s = pptx.addSlide(); T(s, "Line under the title");
s.addShape(pptx.ShapeType.line, { x: 0.6, y: 1.65, w: 1.5, h: 0, line: { color: "E8422E", width: 3 } });
body(s, "Body text sits below the accent line and fills the slide area", 2.2);
s.addText("A second block of text keeps the lower part of the slide in use", { x: 0.6, y: 4.2, w: 12.1, h: 2.4, fontSize: 20 });
s.addNotes("line");

pptx.writeFile({ fileName: out }).then((f) => console.log("wrote " + f));
