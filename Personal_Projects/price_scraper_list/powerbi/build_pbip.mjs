// Builds the client's local Power BI project (ADR-015) from the approved report spec:
//   semantic model (TMDL, Import over the Parquet tables written by `main.py client-report`),
//   custom theme, and the 3 report pages.
// Output goes to the git-ignored client folder; this script holds no client data.
//
//   node powerbi/build_pbip.mjs            (run from the project root)
//
// The .pbip shell (.pbip, .platform, definition.pbir, version.json) comes from
// `powerbi-report-author scaffold` and is kept; pages, theme and model are regenerated.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT = path.join(ROOT, "data", "client", "powerbi");
// Report name = the scaffolded .pbip in the client folder (kept out of this versioned file).
const NAME = (fs.existsSync(OUT) && fs.readdirSync(OUT).find((f) => f.endsWith(".pbip"))?.replace(/\.pbip$/, "")) || "";
if (!NAME) {
  console.error(`No .pbip in ${OUT}. Scaffold first: powerbi-report-author scaffold "${OUT}" --name <Tienda>_Rappi --model-path ../<Tienda>_Rappi.SemanticModel`);
  process.exit(1);
}
const REPORT = path.join(OUT, `${NAME}.Report`);
const MODEL = path.join(OUT, `${NAME}.SemanticModel`);
const DATA_DIR = path.join(OUT, "data") + path.sep;

const SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition";
const VISUAL_SCHEMA = `${SCHEMA}/visualContainer/2.9.0/schema.json`;
const PAGE_SCHEMA = `${SCHEMA}/page/2.1.0/schema.json`;



// ------------------------------------------------------------------ helpers
const hex = (n) => crypto.randomBytes(n).toString("hex");
const write = (file, data) => {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, typeof data === "string" ? data : JSON.stringify(data, null, 2) + "\n", "utf8");
};
const lit = (v) => ({ expr: { Literal: { Value: v } } });
const str = (s) => lit(`'${String(s).replace(/'/g, "''")}'`);
const num = (n) => lit(`${n}D`);
const bool = (b) => lit(b ? "true" : "false");
const color = (c) => ({ solid: { color: str(c) } });
const q = (s) => (/^[A-Za-z_][A-Za-z0-9_]*$/.test(s) ? s : `'${s.replace(/'/g, "''")}'`);   // TMDL name

const col = (entity, prop) => ({ Column: { Expression: { SourceRef: { Entity: entity } }, Property: prop } });
const msr = (prop) => ({ Measure: { Expression: { SourceRef: { Entity: "_Medidas" } }, Property: prop } });
const agg = (entity, prop, fn) => ({ Aggregation: { Expression: col(entity, prop), Function: fn } });
const AGG_NAME = { 0: "Sum", 1: "Avg", 3: "Min", 4: "Max" };
function proj(field, displayName) {
  let ref, native;
  if (field.Column) { ref = `${field.Column.Expression.SourceRef.Entity}.${field.Column.Property}`; native = field.Column.Property; }
  else if (field.Measure) { ref = `_Medidas.${field.Measure.Property}`; native = field.Measure.Property; }
  else { const c = field.Aggregation.Expression.Column; native = c.Property;
    ref = `${AGG_NAME[field.Aggregation.Function]}(${c.Expression.SourceRef.Entity}.${c.Property})`; }
  const p = { field, queryRef: ref, nativeQueryRef: native };
  if (displayName) p.displayName = displayName;
  return p;
}

// ------------------------------------------------------------------ design tokens (spec)
const C = {
  bg: "#F3F2F1", panel: "#FFFFFF", text: "#252423", grey: "#767676", line: "#E1DFDD",
  bajar: "#0072B2", subir: "#009E73", desactivar: "#D55E00", vincular: "#CC79A7",
  bajarTint: "#DEEFFF",
};
const W = 1920, H = 1080, MARGIN = 32, GUTTER = 24, SNAP = 8;
const CW = (W - 2 * MARGIN - 11 * GUTTER) / 12, RH = (H - 2 * MARGIN - 11 * GUTTER) / 12;
const snap = (v) => Math.round(v / SNAP) * SNAP;
// region [colStart,rowStart,colEnd,rowEnd] (1-indexed, end-exclusive) -> pixels
function region([c1, r1, c2, r2]) {
  const x = snap(MARGIN + (c1 - 1) * (CW + GUTTER)), y = snap(MARGIN + (r1 - 1) * (RH + GUTTER));
  const x2 = snap(MARGIN + (c2 - 1) * (CW + GUTTER) - GUTTER), y2 = snap(MARGIN + (r2 - 1) * (RH + GUTTER) - GUTTER);
  return { x, y, width: x2 - x, height: y2 - y };
}
function slot(r, i, n) {   // divide along the longer axis
  if (r.width >= r.height) {
    const w = (r.width - (n - 1) * GUTTER) / n;
    return { ...r, x: snap(r.x + (i - 1) * (w + GUTTER)), width: snap(w) };
  }
  const h = (r.height - (n - 1) * GUTTER) / n;
  return { ...r, y: snap(r.y + (i - 1) * (h + GUTTER)), height: snap(h) };
}

let z = 0;
function container(visual, pos, { title, alt, panel = true } = {}) {
  z += 1000;
  const vco = {
    padding: [{ properties: { top: num(8), bottom: num(8), left: num(12), right: num(12) } }],
    visualHeader: [{ properties: { show: bool(false) } }],
  };
  if (panel) {
    vco.background = [{ properties: { show: bool(true), color: color(C.panel), transparency: num(0) } }];
    vco.border = [{ properties: { show: bool(true), color: color(C.line), radius: num(8) } }];
  } else {
    vco.background = [{ properties: { show: bool(false) } }];
    vco.border = [{ properties: { show: bool(false) } }];
  }
  vco.title = title
    ? [{ properties: { show: bool(true), text: str(title), fontSize: num(14), bold: bool(true), fontColor: color(C.text) } }]
    : [{ properties: { show: bool(false) } }];
  if (alt) vco.general = [{ properties: { altText: str(alt) } }];
  vco.subTitle = [{ properties: { show: bool(false) } }];
  return { $schema: VISUAL_SCHEMA, name: hex(10), position: { ...pos, z, tabOrder: z }, visual: { ...visual, visualContainerObjects: vco } };
}

const textbox = (pos, text, size = 26) => container({
  visualType: "textbox",
  objects: { general: [{ properties: { paragraphs: [{ textRuns: [{ value: text,
    textStyle: { fontFamily: "Segoe UI Semibold", fontSize: `${size}px`, color: C.text } }], horizontalTextAlignment: "left" }] } }] },
}, pos, { panel: false });

const slicer = (pos, entity, column, header) => slim(container({
  visualType: "slicer",
  query: { queryState: { Values: { projections: [proj(col(entity, column))] } } },
  objects: {
    data: [{ properties: { mode: str("Dropdown") } }],
    header: [{ properties: { show: bool(true), text: str(header) } }],
  },
}, pos, { alt: `Filtro de ${header}` }));
// header band is 64 px: header 28 + dropdown 32 fits only without vertical padding
function slim(v) {
  v.visual.visualContainerObjects.padding = [{ properties: { top: num(0), bottom: num(0), left: num(8), right: num(8) } }];
  return v;
}

const card = (pos, measure, accent, alt) => container({
  visualType: "cardVisual",
  query: { queryState: { Data: { projections: [proj(msr(measure))] } } },
  objects: {
    value: [{ properties: { fontSize: num(32), labelDisplayUnits: str("1") }, selector: { id: "default" } }],
    label: [{ properties: { fontSize: num(13) }, selector: { id: "default" } }],
    padding: [{ properties: { paddingUniform: num(8) }, selector: { id: "default" } }],
    layout: [{ properties: { paddingUniform: num(0) }, selector: { id: "default" } }],
    accentBar: [{ properties: { show: bool(true), position: str("Left"), width: num(6), color: color(accent) }, selector: { id: "default" } }],
  },
}, pos, { alt });

function table(pos, fields, { title, alt, sort, filters, extraValues = [], widths = {}, totals = true }) {
  const v = {
    visualType: "tableEx",
    query: { queryState: { Values: { projections: fields.map(([f, d]) => proj(f, d)) } } },
    objects: {
      columnHeaders: [{ properties: { fontSize: num(11), bold: bool(true), wordWrap: bool(true) } }],
      values: [{ properties: { fontSize: num(11), wordWrap: bool(true) } }, ...extraValues],
      total: [{ properties: { totals: bool(totals) } }],
    },
  };
  const w = Object.entries(widths).map(([ref, px]) => ({ properties: { value: num(px) }, selector: { metadata: ref } }));
  if (w.length) v.objects.columnWidth = w;
  if (sort) v.query.sortDefinition = { sort, isDefaultSort: false };
  return withFilters(container(v, pos, { title, alt }), filters);
}

function withFilters(vis, filters) {
  if (filters && filters.length) vis.filterConfig = { filters };
  return vis;
}
function inFilter(entity, column, values) {
  return { name: "Filter" + hex(12), field: col(entity, column), type: "Categorical",
    filter: { Version: 2, From: [{ Name: "t", Entity: entity, Type: 0 }],
      Where: [{ Condition: { In: { Expressions: [{ Column: { Expression: { SourceRef: { Source: "t" } }, Property: column } }],
        Values: values.map((v) => [{ Literal: { Value: `'${v}'` } }]) } } }] },
    howCreated: "User" };
}
function gtFilter(entity, column, value) {
  return { name: "Filter" + hex(12), field: col(entity, column), type: "Advanced",
    filter: { Version: 2, From: [{ Name: "t", Entity: entity, Type: 0 }],
      Where: [{ Condition: { Comparison: { ComparisonKind: 1,
        Left: { Column: { Expression: { SourceRef: { Source: "t" } }, Property: column } },
        Right: { Literal: { Value: `${value}D` } } } } }] },
    howCreated: "User" };
}

// ------------------------------------------------------------------ semantic model (TMDL)
const T = { s: "string", i: "int64", d: "double", dt: "dateTime" };
const COP = "\\$ #,0", PCT = "0.0%", DATE = "dd/mm/yyyy";
const TABLES = {
  acciones: [
    ["Fecha reporte", "dt", DATE], ["Acción", "s", null, { sortBy: "Orden acción" }], ["Orden acción", "i", "0", { hidden: true }],
    ["Color acción", "s", null, { hidden: true }], ["Producto", "s"], ["Publicación en Rappi", "s"], ["Stock", "d", "0"],
    ["Costo", "d", COP], ["Comisión", "d", PCT], ["Precio Rappi actual", "d", COP], ["Utilidad actual", "d", COP],
    ["Margen actual", "d", PCT], ["Competidor más barato", "s"], ["Precio competidor", "d", COP],
    ["Producto del competidor", "s"], ["Precio sugerido", "d", COP], ["Utilidad sugerida", "d", COP],
    ["Margen sugerido", "d", PCT], ["Precio WhatsApp", "d", COP], ["Nota", "s"],
  ],
  productos: [
    ["Fecha reporte", "dt", DATE], ["Producto", "s"], ["Categoría", "s"], ["Stock", "d", "0"], ["Vendidas recientes", "d", "0"],
    ["Costo", "d", COP], ["Precio WhatsApp", "d", COP], ["Comisión", "d", PCT], ["Publicado en Rappi", "s"],
    ["Precio Rappi actual", "d", COP], ["Margen actual", "d", PCT], ["Competidor más barato", "s"],
    ["Precio competidor", "d", COP], ["Producto del competidor", "s"], ["Competidor confiable", "s"],
    ["Coincidencia", "d", "0.00"], ["Tiendas con el producto", "i", "0"], ["Precio sugerido", "d", COP],
    ["Utilidad con el sugerido", "d", COP], ["Margen sugerido", "d", PCT], ["Brecha vs competidor", "d", PCT],
    ["Acción", "s"], ["Notas", "s"],
  ],
  visibilidad_hora: [
    ["Probado en", "dt", "dd/mm/yyyy hh:nn"], ["Fecha", "dt", "dd/mm"], ["Día", "s"], ["Hora", "s", null, { sortBy: "Hora num" }],
    ["Hora num", "i", "0", { hidden: true }], ["Tipo de día", "s"], ["Según su horario", "s"], ["Según Rappi", "s"],
    ["Página abre", "i", "0"], ["Productos en página", "i", "0"], ["Búsquedas medidas", "i", "0"], ["Aparece en", "i", "0"],
    ["Mejor posición", "i", "0"], ["Dónde aparece", "s"],
  ],
  visibilidad_busqueda: [
    ["Probado en", "dt", "dd/mm/yyyy hh:nn"], ["Búsqueda", "s"], ["Aparece", "i", "0"], ["Posición", "i", "0"],
    ["Tiendas listadas", "i", "0"],
  ],
  visibilidad_semanal: [["Fecha", "dt", DATE], ["Tipo de búsqueda", "s"], ["Búsquedas medidas", "i", "0"], ["Aparece en", "i", "0"], ["Posición promedio", "d", "0.0"]],
  reporte: [["Fecha reporte", "dt", DATE], ["Tienda", "s"], ["Visibilidad hasta", "dt", "dd/mm/yyyy hh:nn"], ["Generado", "dt", "dd/mm/yyyy hh:nn"]],
};
const IN_LINK = '{"Vincular", "No aparece en Rappi", "Revisar vínculo"}';
const MEASURES = [
  ["Para bajar precio", 'CALCULATE(COUNTROWS(acciones), acciones[Acción] = "Bajar precio") + 0', "0"],
  ["Para subir precio", 'CALCULATE(COUNTROWS(acciones), acciones[Acción] = "Subir precio") + 0', "0"],
  ["Para desactivar", 'CALCULATE(COUNTROWS(acciones), acciones[Acción] = "Desactivar") + 0', "0"],
  ["Para vincular o revisar", `CALCULATE(COUNTROWS(acciones), acciones[Acción] IN ${IN_LINK}) + 0`, "0"],
  ["Δ utilidad por unidad", 'SUMX(FILTER(acciones, acciones[Acción] IN {"Bajar precio", "Subir precio"}), acciones[Utilidad sugerida] - acciones[Utilidad actual])', "+\\$ #,0;-\\$ #,0;\\$ 0"],
  ["Productos analizados", "COUNTROWS(productos) + 0", "0"],
  ["Publicados en Rappi", 'CALCULATE(COUNTROWS(productos), productos[Publicado en Rappi] = "Sí") + 0', "0"],
  ["Con stock sin publicar", 'CALCULATE(COUNTROWS(productos), productos[Publicado en Rappi] = "No", productos[Stock] > 0) + 0', "0"],
  ["Con competidor", 'CALCULATE(COUNTROWS(productos), productos[Competidor confiable] = "Sí") + 0', "0"],
  ["Margen Rappi promedio", 'CALCULATE(AVERAGE(productos[Margen actual]), productos[Publicado en Rappi] = "Sí")', PCT],
  ["Brecha vs competidor %", "AVERAGE(productos[Brecha vs competidor])", "+0.0%;-0.0%;0.0%"],
  ["% página abre", "AVERAGE(visibilidad_hora[Página abre])", "0%"],
  ["Búsquedas donde aparece", "AVERAGE(visibilidad_hora[Aparece en])", "0.0"],
  ["Mejor posición en búsqueda", "MIN(visibilidad_busqueda[Posición])", "0"],
  ["Mediciones", "DISTINCTCOUNT(visibilidad_busqueda[Probado en])", "0"],
  ["Veces que aparece", "SUM(visibilidad_busqueda[Aparece]) + 0", "0"],
  ["Aparece % semanal", "DIVIDE(SUM(visibilidad_semanal[Aparece en]), SUM(visibilidad_semanal[Búsquedas medidas]))", "0.0%"],
];

function tableTmdl(name, cols) {
  const lines = [`table ${q(name)}`, ""];
  for (const [c, t, fmt, opt = {}] of cols) {
    lines.push(`\tcolumn ${q(c)}`, `\t\tdataType: ${T[t]}`);
    if (fmt) lines.push(`\t\tformatString: ${fmt}`);
    if (opt.hidden) lines.push("\t\tisHidden");
    lines.push(`\t\tsummarizeBy: none`, `\t\tsourceColumn: ${c}`);
    if (opt.sortBy) lines.push(`\t\tsortByColumn: ${q(opt.sortBy)}`);
    lines.push("");
  }
  lines.push(`\tpartition ${q(name)} = m`, "\t\tmode: import", "\t\tsource =", "\t\t\t\tlet",
    `\t\t\t\t    Origen = Parquet.Document(File.Contents(CarpetaDatos & "${name}.parquet"))`, "\t\t\t\tin", "\t\t\t\t    Origen", "");
  return lines.join("\n");
}

function buildModel() {
  let logicalId = crypto.randomUUID();
  try { logicalId = JSON.parse(fs.readFileSync(path.join(MODEL, ".platform"), "utf8")).config.logicalId; } catch {}
  fs.rmSync(MODEL, { recursive: true, force: true });
  write(path.join(MODEL, ".platform"), {
    $schema: "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
    metadata: { type: "SemanticModel", displayName: NAME }, config: { version: "2.0", logicalId },
  });
  write(path.join(MODEL, "definition.pbism"), {
    $schema: "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
    version: "4.2", settings: {},
  });
  const def = path.join(MODEL, "definition");
  write(path.join(def, "database.tmdl"), "database\n\tcompatibilityLevel: 1600\n\n");
  const refs = [...Object.keys(TABLES), "_Medidas"].map((t) => `ref table ${q(t)}`).join("\n");
  write(path.join(def, "model.tmdl"), [
    "model Model", "\tculture: es-CO", "\tdefaultPowerBIDataSourceVersion: powerBI_V3", "\tsourceQueryCulture: es-CO",
    "\tdataAccessOptions", "\t\tlegacyRedirects", "\t\treturnErrorValuesAsNull", "",
    "annotation __PBI_TimeIntelligenceEnabled = 0", "", refs, "", "ref expression CarpetaDatos", "",
  ].join("\n"));
  write(path.join(def, "expressions.tmdl"),
    `expression CarpetaDatos = "${DATA_DIR}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n` +
    "\tannotation PBI_ResultType = Text\n\n");
  for (const [name, cols] of Object.entries(TABLES)) write(path.join(def, "tables", `${name}.tmdl`), tableTmdl(name, cols));
  const m = ["table _Medidas", ""];
  for (const [n, dax, fmt] of MEASURES) m.push(`\tmeasure ${q(n)} = ${dax}`, `\t\tformatString: ${fmt}`, "");
  m.push("\tcolumn Valor", "\t\tdataType: int64", "\t\tisHidden", "\t\tsummarizeBy: none", "\t\tisNameInferred", "\t\tsourceColumn: [Valor]", "",
    "\tpartition _Medidas = calculated", "\t\tmode: import", '\t\tsource = ROW("Valor", 0)', "");
  write(path.join(def, "tables", "_Medidas.tmdl"), m.join("\n"));
  write(path.join(def, "relationships.tmdl"), [
    `relationship ${crypto.randomUUID()}`, "\tfromColumn: visibilidad_busqueda.'Probado en'",
    "\ttoColumn: visibilidad_hora.'Probado en'", "",
  ].join("\n"));
}

// ------------------------------------------------------------------ theme
function buildTheme() {
  const base = JSON.parse(fs.readFileSync(path.join(ROOT, "powerbi", "theme_base.json"), "utf8"));
  const res = path.join(REPORT, "StaticResources", "RegisteredResources");
  fs.rmSync(res, { recursive: true, force: true });
  const file = `ClientCalm-${hex(4)}.json`;
  const theme = { ...base, name: file,
    dataColors: [C.bajar, C.subir, C.desactivar, C.vincular, C.grey, "#56B4E9", "#E69F00", "#000000"],
    background: C.panel, foreground: C.text, tableAccent: C.bajar };
  delete theme.$schema;
  // the CLI rejects container properties inside the cardVisual theme style; visuals set them via VCOs
  for (const k of ["border", "spacing", "padding"]) delete theme.visualStyles.cardVisual["*"][k];
  write(path.join(res, file), theme);
  const rjPath = path.join(REPORT, "definition", "report.json");
  const rj = JSON.parse(fs.readFileSync(rjPath, "utf8"));
  rj.themeCollection.customTheme = { name: file, reportVersionAtImport: rj.themeCollection.baseTheme.reportVersionAtImport, type: "RegisteredResources" };
  rj.resourcePackages = rj.resourcePackages.filter((p) => p.type !== "RegisteredResources");
  rj.resourcePackages.push({ name: "RegisteredResources", type: "RegisteredResources", items: [{ name: file, path: file, type: "CustomTheme" }] });
  write(rjPath, rj);
}

// ------------------------------------------------------------------ pages
function page(displayName, visuals) {
  const name = hex(10);
  const dir = path.join(REPORT, "definition", "pages", name);
  write(path.join(dir, "page.json"), {
    $schema: PAGE_SCHEMA, name, displayName, displayOption: "FitToPage", height: H, width: W,
    objects: { background: [{ properties: { color: color(C.bg), transparency: num(0) } }],
      outspace: [{ properties: { color: color(C.bg) } }] },
  });
  for (const v of visuals) write(path.join(dir, "visuals", v.name, "visual.json"), v);
  return name;
}

function pageActions() {
  z = 0;
  const kpis = region([1, 2, 13, 4]);
  const queue = region([1, 4, 9, 13]);
  const A = "acciones";
  const fontByAction = { properties: { fontColor: { solid: { color: { expr: agg(A, "Color acción", 3) } } } },
    selector: { data: [{ dataViewWildcard: { matchingOption: 1 } }], metadata: `${A}.Acción` } };
  const impact = container({
    visualType: "clusteredBarChart",
    query: { queryState: {
      Category: { projections: [proj(col(A, "Producto"))] },
      Y: { projections: [proj(agg(A, "Utilidad actual", 0), "Utilidad actual"), proj(agg(A, "Utilidad sugerida", 0), "Utilidad con el sugerido")] },
    }, sortDefinition: { sort: [{ field: agg(A, "Utilidad sugerida", 0), direction: "Descending" }], isDefaultSort: false } },
    objects: {
      dataPoint: [
        { properties: { fill: color(C.grey) }, selector: { metadata: `Sum(${A}.Utilidad actual)` } },
        { properties: { fill: color(C.bajar) }, selector: { metadata: `Sum(${A}.Utilidad sugerida)` } },
      ],
      labels: [{ properties: { show: bool(true), fontSize: num(10) } }],
      legend: [{ properties: { show: bool(true), position: str("Top") } }],
      categoryAxis: [{ properties: { fontSize: num(10) } }],
      valueAxis: [{ properties: { show: bool(false) } }],
    },
  }, region([9, 4, 13, 13]), { title: "Utilidad por unidad: hoy vs con el precio sugerido",
    alt: "Barras por publicación a bajar o subir: utilidad por unidad con el precio actual (gris) y con el sugerido (azul)." });
  return page("Qué cambiar hoy en Rappi", [
    textbox(region([1, 1, 9, 2]), "Qué cambiar hoy en Rappi"),
    slicer(region([9, 1, 13, 2]), A, "Acción", "Acción"),
    card(slot(kpis, 1, 5), "Para bajar precio", C.bajar, "Publicaciones que conviene bajar de precio"),
    card(slot(kpis, 2, 5), "Para subir precio", C.subir, "Publicaciones que pueden subir de precio y seguir siendo las más baratas"),
    card(slot(kpis, 3, 5), "Para desactivar", C.desactivar, "Publicaciones sin stock que hay que desactivar"),
    card(slot(kpis, 4, 5), "Para vincular o revisar", C.vincular, "Publicaciones sin vincular o que no aparecen en Rappi"),
    card(slot(kpis, 5, 5), "Δ utilidad por unidad", C.text, "Cambio de utilidad por unidad si aplica todos los precios sugeridos"),
    table(queue, [
      [col(A, "Acción")], [col(A, "Producto")], [col(A, "Stock")], [col(A, "Precio Rappi actual"), "Precio actual"],
      [col(A, "Precio sugerido")], [col(A, "Competidor más barato"), "Competidor"], [col(A, "Precio competidor")],
      [col(A, "Margen actual")], [col(A, "Nota")],
    ], { title: "Lista de acciones (de arriba hacia abajo)", totals: false,
      widths: { "acciones.Acción": 110, "acciones.Producto": 240, "acciones.Stock": 48, "acciones.Precio Rappi actual": 84,
        "acciones.Precio sugerido": 88, "acciones.Competidor más barato": 128, "acciones.Precio competidor": 88,
        "acciones.Margen actual": 64, "acciones.Nota": 330 }, sort: [{ field: col(A, "Acción"), direction: "Ascending" }],
      extraValues: [fontByAction],
      alt: "Tabla con una fila por publicación en Rappi: acción, producto, precio actual y sugerido, competidor y nota." }),
    withFilters(impact, [inFilter(A, "Acción", ["Bajar precio", "Subir precio"])]),
  ]);
}

function pagePrices() {
  z = 0;
  const P = "productos";
  const kpis = region([1, 2, 13, 4]);
  const filters = region([8, 1, 13, 2]);
  const gap = container({
    visualType: "barChart",
    query: { queryState: {
      Category: { projections: [proj(col(P, "Producto"))] },
      Y: { projections: [proj(msr("Brecha vs competidor %"))] },
    }, sortDefinition: { sort: [{ field: msr("Brecha vs competidor %"), direction: "Descending" }], isDefaultSort: false } },
    objects: {
      dataPoint: [{ properties: { fill: color(C.desactivar) } }],
      labels: [{ properties: { show: bool(true), fontSize: num(10) } }],
      categoryAxis: [{ properties: { fontSize: num(10) } }],
      valueAxis: [{ properties: { show: bool(false) } }],
    },
  }, region([1, 4, 7, 13]), { title: "Su precio en Rappi vs el competidor más barato (+ = más cara)",
    alt: "Barras por producto publicado con competidor: diferencia porcentual entre su precio en Rappi y el competidor más barato." });
  return page("Precios vs competencia", [
    textbox(region([1, 1, 8, 2]), "Dónde está más cara que la competencia"),
    slicer(slot(filters, 1, 2), P, "Categoría", "Categoría"),
    slicer(slot(filters, 2, 2), P, "Publicado en Rappi", "Publicado en Rappi"),
    card(slot(kpis, 1, 5), "Productos analizados", C.grey, "Productos con stock o vendidos recientemente"),
    card(slot(kpis, 2, 5), "Publicados en Rappi", C.grey, "Productos publicados en Rappi"),
    card(slot(kpis, 3, 5), "Con stock sin publicar", C.vincular, "Productos con stock que no están en Rappi"),
    card(slot(kpis, 4, 5), "Con competidor", C.grey, "Productos que otra tienda cercana vende igual"),
    card(slot(kpis, 5, 5), "Margen Rappi promedio", C.subir, "Margen promedio en Rappi después de la comisión"),
    withFilters(gap, [inFilter(P, "Competidor confiable", ["Sí"])]),
    table(region([7, 4, 13, 13]), [
      [col(P, "Producto")], [col(P, "Stock")], [col(P, "Vendidas recientes"), "Vendidas 90 días"],
      [col(P, "Precio sugerido")], [col(P, "Utilidad con el sugerido"), "Utilidad"], [col(P, "Competidor más barato"), "Competidor"],
    ], { title: "Para publicar: tiene stock y no está en Rappi", totals: false,
      widths: { "productos.Producto": 340, "productos.Stock": 56, "productos.Vendidas recientes": 88,
        "productos.Precio sugerido": 96, "productos.Utilidad con el sugerido": 88, "productos.Competidor más barato": 170 },
      sort: [{ field: col(P, "Vendidas recientes"), direction: "Descending" }],
      filters: [inFilter(P, "Publicado en Rappi", ["No"]), gtFilter(P, "Stock", 0)],
      alt: "Tabla de productos con stock que no están publicados en Rappi, ordenados por ventas recientes, con precio sugerido." }),
  ]);
}

function pageVisibility() {
  z = 0;
  const V = "visibilidad_hora", B = "visibilidad_busqueda";
  const kpis = region([1, 2, 13, 4]);
  const filters = region([8, 1, 13, 2]);
  const heatRef = "_Medidas.% página abre";
  const heat = container({
    visualType: "pivotTable",
    query: { queryState: {
      Rows: { projections: [proj(col(V, "Hora"))] },
      Columns: { projections: [proj(col(V, "Fecha"))] },
      Values: { projections: [proj(msr("% página abre"))] },
    } },
    objects: {
      values: [{ properties: { fontSize: num(10), backColor: { solid: { color: { expr: { FillRule: {
        Input: { SelectRef: { ExpressionName: heatRef } },
        FillRule: { linearGradient2: { min: { color: { Literal: { Value: "'#FFFFFF'" } } }, max: { color: { Literal: { Value: `'${C.subir}'` } } },
          nullColoringStrategy: { strategy: { Literal: { Value: "'noColor'" } } } } } } } } } } },
        selector: { data: [{ dataViewWildcard: { matchingOption: 1 } }], metadata: heatRef } }],
      columnHeaders: [{ properties: { fontSize: num(10) } }],
      rowHeaders: [{ properties: { fontSize: num(10) } }],
    },
  }, region([1, 4, 8, 9]), { title: "¿Abre la página de la tienda? (hora × día, % de mediciones)",
    alt: "Matriz de horas por fechas: porcentaje de veces que la página de la tienda abre en Rappi; verde = abre." });
  const trend = container({
    visualType: "lineChart",
    query: { queryState: {
      Category: { projections: [proj(col("visibilidad_semanal", "Fecha"))] },
      Y: { projections: [proj(msr("Aparece % semanal"))] },
      Series: { projections: [proj(col("visibilidad_semanal", "Tipo de búsqueda"))] },
    } },
    objects: {
      legend: [{ properties: { show: bool(true), position: str("Top") } }],
      labels: [{ properties: { show: bool(true), fontSize: num(10) } }],
      lineStyles: [{ properties: { showMarker: bool(true), lineChartType: str("linear"), areaShow: bool(false) } }],
    },
  }, region([8, 4, 13, 9]), { title: "Dónde aparece: búsquedas generales vs sus productos",
    alt: "Dos líneas por fecha de corrida: porcentaje de búsquedas generales (lo que escriben los clientes) y de búsquedas de sus productos donde aparece la tienda." });
  return page("Visibilidad", [
    textbox(region([1, 1, 8, 2]), "Cuándo y dónde la encuentran los clientes"),
    slicer(slot(filters, 1, 2), V, "Tipo de día", "Tipo de día"),
    slicer(slot(filters, 2, 2), V, "Según su horario", "Según su horario"),
    card(slot(kpis, 1, 4), "% página abre", C.subir, "Porcentaje de mediciones en que la página de la tienda abre"),
    card(slot(kpis, 2, 4), "Búsquedas donde aparece", C.bajar, "Promedio de búsquedas, de las medidas cada hora, donde aparece la tienda"),
    card(slot(kpis, 3, 4), "Mejor posición en búsqueda", C.grey, "Mejor posición de la tienda en una búsqueda"),
    card(slot(kpis, 4, 4), "Mediciones", C.grey, "Número de mediciones por hora"),
    heat, trend,
    table(region([1, 9, 13, 13]), [
      [col(B, "Búsqueda")], [msr("Mediciones")], [msr("Veces que aparece")], [msr("Mejor posición en búsqueda"), "Mejor posición"],
    ], { title: "Búsquedas medidas cada hora", sort: [{ field: msr("Veces que aparece"), direction: "Descending" }],
      alt: "Tabla por búsqueda: mediciones, veces que aparece la tienda y su mejor posición." }),
  ]);
}

function buildPages() {
  const pagesDir = path.join(REPORT, "definition", "pages");
  fs.rmSync(pagesDir, { recursive: true, force: true });
  const order = [pageActions(), pagePrices(), pageVisibility()];
  write(path.join(pagesDir, "pages.json"), {
    $schema: `${SCHEMA}/pagesMetadata/1.1.0/schema.json`, pageOrder: order, activePageName: order[0],
  });
}

if (!process.argv.includes("--pages-only")) buildModel();
buildTheme();
buildPages();
console.log(`Built ${NAME}: model ${Object.keys(TABLES).length} tables + ${MEASURES.length} measures, 3 pages -> ${OUT}`);
