# Tableau to Streamlit Visualization

Data Visualization, Week 11: a Streamlit rebuild of our Week 8/9 Tableau dashboard on teaching evaluations.

**Live dashboard:** [Open the Academic & QA Staff dashboard](https://academic-and-quality-assurance-staff-dashboard.streamlit.app/)

If the app has been idle, it may show a sleep screen first. Click "Yes, get this app back up!" and wait about 30 seconds.

## What it shows

- **Figure 1:** How do departments compare across the three skill areas? (heatmap of average human skill, material and teaching skill scores by department)
- **Figure 2:** Which instructors need teaching support? (average teaching skill score per instructor, grouped by department, with an adjustable support threshold)
- **Figure 3:** Which subjects have the weakest teaching materials? (average material score per subject, with an average reference line)

Refinements over the Tableau version:

- Sidebar filters for year, semester, department and subject
- **Figure 4:** how the three skill areas changed by year and semester, overall or split by department
- A teaching-support threshold slider that flags instructors below it
- Summary KPIs (class sections, instructors, subjects, response rate, skill averages) and auto-generated takeaways under each figure
- A downloadable table of the filtered data

## Run it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install streamlit pandas plotly openpyxl
streamlit run app.py
```

Put the class dataset (CSV or Excel) in `data/` (see [data/README.md](data/README.md)), or upload it from the app's sidebar.

## Files

- `app.py`: the Streamlit app
- `requirements.txt`: Python packages, used by Streamlit Community Cloud
- `data/`: the dataset (`Wk08_dataset.xlsx`)
- `screenshots/`: dashboard screenshots for submission
- `PROMPTS.md`: AI prompts and the model used
