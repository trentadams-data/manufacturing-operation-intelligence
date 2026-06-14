# Frontend Integration Guide

How to copy the generated outputs into the portfolio website (Bolt.new / React /
Vite) and consume them on the case-study page.

> Run `python src/run_pipeline.py` first so the JSON and chart files exist.

---

## 1. Copy the generated files

Copy the **data exports** into the site's public data folder:

```text
From:  data/web_exports/
To:    portfolio-site/public/data/manufacturing/
```

Copy the **chart images** into the site's public images folder:

```text
From:  outputs/charts/
To:    portfolio-site/public/images/manufacturing/
```

Example (run from the analytics project root; adjust the destination to your repo):

```bash
PORTFOLIO=../../portfolio-site   # path to the website repo

mkdir -p "$PORTFOLIO/public/data/manufacturing"
mkdir -p "$PORTFOLIO/public/images/manufacturing"

cp data/web_exports/*.json "$PORTFOLIO/public/data/manufacturing/"
cp outputs/charts/*.png    "$PORTFOLIO/public/images/manufacturing/"
```

After copying, the website serves:

- `/data/manufacturing/manufacturing_case_study.json` (the combined document)
- `/images/manufacturing/oee_trend.png` (and the other four charts)

The `image` field on every chart asset in the JSON already points at
`/images/manufacturing/<file>.png`, so the paths line up automatically.

---

## 2. Read the case study in React

The combined document lives in `public/`, so fetch it at runtime (no rebuild
needed when the data changes):

```tsx
import { useEffect, useState } from "react";
import type { ManufacturingCaseStudy } from "./manufacturing.types";

export function useManufacturingCaseStudy() {
  const [data, setData] = useState<ManufacturingCaseStudy | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/data/manufacturing/manufacturing_case_study.json")
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load case study (${res.status})`);
        return res.json() as Promise<ManufacturingCaseStudy>;
      })
      .then(setData)
      .catch((err) => setError(err.message));
  }, []);

  return { data, error };
}
```

Rendering the KPI cards and charts:

```tsx
function ManufacturingCaseStudyPage() {
  const { data, error } = useManufacturingCaseStudy();

  if (error) return <p>{error}</p>;
  if (!data) return <p>Loading…</p>;

  return (
    <section>
      <h1>{data.project.title}</h1>
      <p>{data.project.subtitle}</p>

      <div className="kpi-grid">
        {data.executive_kpis.map((kpi) => (
          <div key={kpi.key} className="kpi-card">
            <span className="kpi-value">{kpi.display}</span>
            <span className="kpi-label">{kpi.label}</span>
            <span className="kpi-context">{kpi.context}</span>
          </div>
        ))}
      </div>

      <div className="chart-grid">
        {data.charts.map((chart) => (
          <figure key={chart.key}>
            <img src={chart.image} alt={chart.title} loading="lazy" />
            <figcaption>{chart.title}</figcaption>
          </figure>
        ))}
      </div>
    </section>
  );
}
```

### Alternative: import at build time

If you prefer to bundle the data (and you copy the JSON into `src/` instead of
`public/`), Vite can import it directly:

```tsx
import caseStudy from "@/data/manufacturing/manufacturing_case_study.json";
// caseStudy is typed as ManufacturingCaseStudy after the cast below.
```

Fetching from `public/` is recommended so you can refresh the data by re-copying
the JSON without rebuilding the site.

---

## 3. TypeScript interfaces

Save as `manufacturing.types.ts` next to the page component. These cover the
fields the page consumes; the analytics domain sections are typed loosely so the
page can read any nested figure without over-constraining the shape.

```ts
export type KpiFormat = "percent" | "percent_pts" | "currency" | "number" | "count";

export interface ExecutiveKpi {
  key: string;
  label: string;
  value: number;
  format: KpiFormat;
  display: string;   // pre-formatted string, e.g. "85.3%"
  context: string;
}

export interface RootCauseItem {
  finding: string;
  likely_driver: string;
  business_impact: string;
  recommended_action: string;
  priority: "High" | "Medium" | "Low";
  affected_area: string;
}

export interface ChartAsset {
  key: string;
  title: string;
  file: string;          // e.g. "oee_trend.png"
  description: string;
  image: string;         // web path, e.g. "/images/manufacturing/oee_trend.png"
  available: boolean;
}

export interface ProjectHeader {
  title: string;
  subtitle: string;
  description: string;
  tools: string[];
  data_type: string;
}

export interface DatasetProfile {
  data_source: string;
  data_through: string;
  date_range: { start: string; end: string };
  plants: number;
  plant_names: string[];
  production_lines: number;
  production_line_names: string[];
  machines: number;
  products: number;
  shifts: string[];
  record_counts: Record<string, number>;
  note: string;
}

export interface ExecutiveRecommendation {
  action: string;
  area: string;
  rationale: string;
  priority: "High" | "Medium" | "Low";
}

export interface ManufacturingCaseStudy {
  project: ProjectHeader;
  executive_kpis: ExecutiveKpi[];
  dataset_profile: DatasetProfile;
  oee: Record<string, unknown>;
  downtime: Record<string, unknown>;
  quality: Record<string, unknown>;
  spc: Record<string, unknown>;
  predictive_maintenance: Record<string, unknown>;
  root_cause: RootCauseItem[];
  executive_recommendations: ExecutiveRecommendation[];
  charts: ChartAsset[];
  meta: { schema_version: string; reproducible: boolean; note: string };
}
```

---

## 4. Refreshing the data

Whenever the analysis changes, re-run the pipeline and re-copy:

```bash
python src/run_pipeline.py
python src/validate_outputs.py          # optional: confirm outputs are complete
cp data/web_exports/*.json "$PORTFOLIO/public/data/manufacturing/"
cp outputs/charts/*.png    "$PORTFOLIO/public/images/manufacturing/"
```

Because the pipeline is deterministic (fixed random seed), the regenerated files
are stable across runs unless the analysis code itself changes.
