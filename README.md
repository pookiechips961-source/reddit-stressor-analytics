# Reddit India Depression — Stressor Analysis Dashboard

An end-to-end data pipeline and interactive dashboard that analyses approximately 17,773 Reddit posts from Indian depression communities. The project identifies five recurring stressor categories through keyword flagging, stores enriched records in MySQL, and surfaces longitudinal and seasonal trends via a Streamlit application built on Plotly.

---

## Overview

Mental health discussions in Indian Reddit communities reflect a distinct set of social pressures — family dynamics, workplace burnout, relationship breakdown, personal vulnerability, and the unique strain of competitive entrance examinations. This project quantifies those patterns over time so that trends can be tracked, compared, and understood at a macro level.

**Pipeline summary**

```
Kaggle CSV  →  data_cleaning.py  →  MySQL (reddit.maintable)  →  site.py (Streamlit)
```

---

## Repository Structure

```
reddit-stressor-analytics/
├── redditposts.csv            # Raw dataset from Kaggle (see note below)
├── data_cleaning.py           # Cleaning and keyword-flagging script
├── redditposts_cleaned.csv    # Output of data_cleaning.py
├── site.py                    # Streamlit dashboard
└── posts.txt                  # Sample posts that triggered all five flags
```

> `redditposts.csv` is included here but is typically gitignored in larger projects given its size. If you have excluded it, download the dataset from Kaggle and place it in the project root before running `data_cleaning.py`.

---

## Dataset

- **Source:** Kaggle — Indian Reddit depression posts
- **Size:** ~17,000 posts
- **Fields used:** `date`, `text`

---

## Data Cleaning (`data_cleaning.py`)

The script performs four steps:

**1. Date normalisation** — Parses dates from `DD-MM-YYYY` and reformats to `YYYY-MM-DD` for MySQL compatibility.

**2. Column cleanup** — Drops the redundant `year` column, which is derivable from the normalised date.

**3. Keyword flagging** — Five binary flag columns are appended based on case-insensitive regex matches against the post body:

| Column | Category | Example keywords |
|---|---|---|
| `flag_academic` | Academic | `JEE`, `NEET`, `exam`, `college`, `placement`, `boards` |
| `flag_family` | Family | `parents`, `mom`, `dad`, `sibling`, `toxic household`, `relatives` |
| `flag_vulnerability` | Vulnerability | `abuse`, `trauma`, `lonely`, `suicidal`, `hopeless`, `anxiety` |
| `flag_corporate` | Corporate | `job`, `boss`, `salary`, `burnout`, `hike`, `increment` |
| `flag_romantic` | Relationship | `gf`, `bf`, `girlfriend`, `boyfriend`, `breakup`, `partner` |

**4. Output** — Writes the enriched dataframe to `redditposts_cleaned.csv`.

```python
import pandas as pd

df = pd.read_csv("redditposts.csv")
df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce').dt.strftime('%Y-%m-%d')
df = df.drop(columns=['year'], errors='ignore')

academic_keywords      = r'\b(JEE|NEET|exam|college|placement|boards)\b'
family_keywords        = r'\b(parents|mom|dad|mother|father|brother|sister|sibling|family|toxic household|relatives|cousin)\b'
vulnerability_keywords = r'\b(abuse|abusive|hitting|beating|trauma|alone|lonely|isolation|crying|depressed|hopeless|suicidal|anxiety)\b'
corporate_keywords     = r'\b(job|boss|salary|increment|hike|burnout)\b'
romantic_keywords      = r'\b(gf|bf|girlfriend|boyfriend|spouse|wife|husband|fiance|fiancee|partner|breakup|dating|relationship)\b'

df['flag_academic']      = df['text'].str.contains(academic_keywords,      case=False, na=False, regex=True).astype(int)
df['flag_family']        = df['text'].str.contains(family_keywords,        case=False, na=False, regex=True).astype(int)
df['flag_vulnerability'] = df['text'].str.contains(vulnerability_keywords, case=False, na=False, regex=True).astype(int)
df['flag_corporate']     = df['text'].str.contains(corporate_keywords,     case=False, na=False, regex=True).astype(int)
df['flag_romantic']      = df['text'].str.contains(romantic_keywords,      case=False, na=False, regex=True).astype(int)

df.to_csv("redditposts_cleaned.csv", index=False)
```

---

## Database Setup

Import the cleaned CSV into a MySQL database named `reddit`, table `maintable`:

```sql
CREATE DATABASE reddit;
USE reddit;

CREATE TABLE maintable (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    date               DATE,
    text               TEXT,
    flag_academic      TINYINT(1),
    flag_family        TINYINT(1),
    flag_vulnerability TINYINT(1),
    flag_corporate     TINYINT(1),
    flag_relationship  TINYINT(1)
);
```

Load the CSV via MySQL Workbench's Table Data Import Wizard, or from the command line:

```bash
mysqlimport --local --fields-terminated-by=',' --lines-terminated-by='\n' \
  --columns='date,text,flag_academic,flag_family,flag_vulnerability,flag_corporate,flag_relationship' \
  -u root -p reddit redditposts_cleaned.csv
```

The dashboard connects to MySQL at `127.0.0.1` with user `root` and no password by default. Update credentials in `site.py → get_data()` to match your local configuration.

---

## Dashboard (`site.py`)

The Streamlit app queries MySQL directly and renders five sections:

| Section | Description |
|---|---|
| A — Key Metrics | Total posts analysed, dominant stressor category, and its mean density per post |
| B — Longitudinal Composition | Normalised area chart showing each stressor's share of total posts across a user-selected year range |
| C — Relative Growth Velocity | Year-over-year growth rate of each stressor relative to the forum's overall growth baseline |
| D — Seasonality & Volatility | Monthly deviation from the annual average for a selected year, revealing recurring stress periods |
| E — Co-occurrence Heatmap | How frequently pairs of stressors appear in the same post; diagonal shows per-category totals |

A final section renders a curated set of posts from `posts.txt` that triggered all five flags simultaneously.

---

## Getting Started

**1. Clone the repository**
```bash
git clone https://github.com/your-username/reddit-stressor-analytics.git
cd reddit-stressor-analytics
```

**2. Install dependencies**
```bash
pip install streamlit pandas mysql-connector-python plotly
```

**3. Prepare the data**
```bash
python data_cleaning.py
# then import redditposts_cleaned.csv into MySQL as described above
```

**4. Run the dashboard**
```bash
streamlit run site.py
```

---

## Tech Stack

- **Python** — pandas, re
- **MySQL** — storage and aggregation
- **Streamlit** — dashboard framework
- **Plotly Express** — interactive charts (area, line, heatmap)

---

## Limitations

- Keyword matching is purely lexical and will produce false positives or miss meaning conveyed through Hinglish, transliteration, or informal abbreviations.
- The `flag_romantic` column produced by `data_cleaning.py` is labelled `flag_relationship` in the MySQL schema and dashboard. Ensure the column name is reconciled consistently on import.
- This project analyses publicly available forum posts. No personally identifiable information is stored or displayed.

---

## License

MIT License. See `LICENSE` for details.
