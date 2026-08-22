# News Pipeline — Colombia President News Agent

Daily ETL pipeline that gathers, analyzes, and archives news about the
Colombian president (2026–2030 term). Built as a data-engineering project.

## Architecture

```
Ingest (RSS)  →  Transform (LLM)  →  Load (JSON)  →  GitHub (cloud)
ingest.py        transform.py        load.py         Actions workflow
```

- **Extract**: Google News RSS (free, no API key), Spanish + English queries
- **Transform**: LLM summarizes, classifies topics, scores sentiment, filters relevance
- **Load**: daily JSON files in `data/` + dedup index so nothing repeats
- **Orchestration**: GitHub Actions runs it daily at 7am Colombia time and commits results

## Run locally

```powershell
pip install -r requirements.txt

# Local Ollama (free, offline)
python run_pipeline.py

# Gemini (better quality)
python run_pipeline.py gemini
```

## Run in the cloud (free)

1. Push this repo to GitHub
2. Add your `GOOGLE_API_KEY` in repo **Settings → Secrets and variables → Actions**
3. The workflow `.github/workflows/daily-news.yml` runs daily automatically
4. Results accumulate as daily commits in `news-pipeline/data/`

## Data schema

Each article in `data/articles-YYYY-MM-DD.json`:

```json
{
  "title": "...",
  "link": "https://...",
  "source": "El Tiempo",
  "published_at": "2026-08-21T10:00:00+00:00",
  "analysis": {
    "relevant": true,
    "summary_es": "...",
    "topics": ["economía"],
    "sentiment": "neutral"
  }
}
```

## Querying the archive later

```python
import json, glob
articles = []
for f in glob.glob("news-pipeline/data/articles-*.json"):
    articles.extend(json.load(open(f, encoding="utf-8")))
relevant = [a for a in articles if a["analysis"].get("relevant")]
```
