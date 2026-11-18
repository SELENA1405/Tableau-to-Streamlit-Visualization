"""Academic & QA Staff dashboard — Streamlit rebuild of the Week 8/9 Tableau dashboard.

Figure 1: How do departments compare across the three skill areas?
Figure 2: Which instructors need teaching support?
Figure 3: Which subjects have the weakest teaching materials?

Run with:  streamlit run app.py
Put the dataset (CSV or Excel) in the ./data folder, or upload it from the sidebar.
"""

import re
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"
SUPPORTED = {".csv", ".xlsx", ".xls"}

# Red → orange → yellow → green, matching the Tableau "Red-Green Diverging" look.
RDYLGN = [
    [0.00, "#c0272d"],
    [0.25, "#e8613c"],
    [0.50, "#f5c95a"],
    [0.75, "#a9c75a"],
    [1.00, "#2e6f3a"],
]
SKILLS = {
    "Human Skill": "Avg. Human Skill Eval",
    "Material": "Avg. Material Eval",
    "Teaching Skill": "Avg. Teaching Skill Eval",
}

st.set_page_config(page_title="Academic & QA Staff Dashboard", page_icon="🎓", layout="wide")


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def read_table(source, name: str, sheet=None) -> pd.DataFrame:
    if name.lower().endswith(".csv"):
        return pd.read_csv(source)
    return pd.read_excel(source, sheet_name=sheet or 0)


@st.cache_data(show_spinner=False)
def excel_sheets(source) -> list[str]:
    return pd.ExcelFile(source).sheet_names


def norm(text) -> str:
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


def numeric_columns(df: pd.DataFrame) -> list[str]:
    cols = []
    for c in df.columns:
        values = pd.to_numeric(df[c], errors="coerce")
        if values.notna().mean() > 0.8:
            cols.append(c)
    return cols


def guess_text(cols, keywords, prefer=()):
    matches = [c for c in cols if any(k in norm(c) for k in keywords)]
    for p in prefer:
        for c in matches:
            if p in norm(c):
                return c
    return matches[0] if matches else None


def guess_scores(cols, keyword, exclude=()):
    return [c for c in cols if keyword in norm(c) and not any(e in norm(c) for e in exclude)]


def pick_source():
    """Return (source, name) for the dataset, from ./data or an upload."""
    st.sidebar.header("Data")
    files = sorted(p for p in DATA_DIR.glob("*") if p.suffix.lower() in SUPPORTED)
    uploaded = st.sidebar.file_uploader("Upload a dataset (optional)", type=["csv", "xlsx", "xls"])
    if uploaded is not None:
        return uploaded, uploaded.name
    if not files:
        return None, None
    chosen = st.sidebar.selectbox("Dataset in ./data", files, format_func=lambda p: p.name)
    return str(chosen), chosen.name


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def fig_department_heatmap(dept: pd.DataFrame) -> go.Figure:
    z = dept[list(SKILLS)].to_numpy()
    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=list(SKILLS.values()),
            y=dept.index.tolist(),
            colorscale=RDYLGN,
            zmin=z.min(),
            zmax=z.max(),
            texttemplate="%{z:.4f}",
            textfont={"size": 18},
            xgap=2,
            ygap=2,
            colorbar={"title": "Average score", "thickness": 14, "tickformat": ".2f"},
            hovertemplate="<b>%{y}</b><br>%{x}: %{z:.4f}<extra></extra>",
        )
    )
    fig.update_xaxes(side="top", tickfont={"size": 14})
    fig.update_yaxes(autorange="reversed", tickfont={"size": 14})
    fig.update_layout(height=110 + 70 * len(dept), margin={"l": 10, "r": 10, "t": 50, "b": 10})
    return fig


def fig_instructors(inst: pd.DataFrame, threshold: float) -> go.Figure:
    vals = inst["Teaching Skill"]
    fig = go.Figure(
        go.Bar(
            x=vals,
            y=[inst["Department"], inst["Instructor"]],
            orientation="h",
            marker={"color": vals, "colorscale": RDYLGN, "cmin": vals.min(), "cmax": vals.max()},
            text=vals.map("{:.4f}".format),
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>Avg. Teaching Skill Eval: %{x:.4f}<extra></extra>",
        )
    )
    fig.add_vline(
        x=threshold,
        line={"dash": "dash", "color": "#999", "width": 1.5},
        layer="below",
        annotation_text=f"Support threshold {threshold:.2f}",
        annotation_position="top",
    )
    fig.update_xaxes(range=[1, 5.4], title="Avg. Teaching Skill Eval", dtick=1)
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        height=140 + 28 * len(inst),
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
        bargap=0.25,
    )
    return fig


def fig_subjects(subj: pd.DataFrame) -> go.Figure:
    vals = subj["Material"]
    avg = vals.mean()
    fig = go.Figure(
        go.Bar(
            x=subj["Subject"].astype(str),
            y=vals,
            marker={"color": vals, "colorscale": RDYLGN, "cmin": vals.min(), "cmax": vals.max()},
            text=vals.map("{:.2f}".format),
            textposition="inside",
            insidetextanchor="end",
            textangle=-90,
            textfont={"color": "white"},
            hovertemplate="<b>%{x}</b><br>Avg. Material Eval: %{y:.4f}<extra></extra>",
        )
    )
    fig.add_hline(
        y=avg,
        line={"color": "#555", "width": 2},
        annotation_text=f"Average {avg:.2f}",
        annotation_position="top left",
    )
    fig.update_xaxes(tickangle=-90, type="category")
    fig.update_yaxes(range=[1, 5], title="Avg. Material Eval", dtick=0.5)
    fig.update_layout(height=640, margin={"l": 10, "r": 10, "t": 40, "b": 10}, bargap=0.15)
    return fig


def fig_trend(trend: pd.DataFrame, split_col=None) -> go.Figure:
    colors = {"Human Skill": "#3b6ea8", "Material": "#d9822b", "Teaching Skill": "#5a9e4b"}
    dashes = ["solid", "dot", "dash", "dashdot"]
    groups = [(None, trend)] if split_col is None else list(trend.groupby(split_col))
    fig = go.Figure()
    for i, (group, g) in enumerate(groups):
        for skill, label in SKILLS.items():
            name = label.replace("Avg. ", "") + (f" ({group})" if group is not None else "")
            fig.add_trace(
                go.Scatter(
                    x=g["Period"],
                    y=g[skill],
                    name=name,
                    mode="lines+markers",
                    line={"color": colors[skill], "width": 2.5, "dash": dashes[i % len(dashes)]},
                    hovertemplate=f"<b>{name}</b><br>%{{x}}: %{{y:.4f}}<extra></extra>",
                )
            )
    fig.update_xaxes(type="category", title=None)
    fig.update_yaxes(title="Average score", tickformat=".2f")
    fig.update_layout(
        height=420,
        margin={"l": 10, "r": 10, "t": 30, "b": 10},
        legend={"orientation": "h", "y": -0.15},
        hovermode="x unified",
    )
    return fig


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
st.title("Academic & QA Staff")
st.caption("Teaching evaluation dashboard: departments, instructors and subjects across the three skill areas.")

source, name = pick_source()
if source is None:
    st.info(
        "No dataset found yet. Put the class dataset (CSV or Excel) in the `data/` folder "
        "and refresh, or upload it from the sidebar."
    )
    st.stop()

sheet = None
if not name.lower().endswith(".csv"):
    sheets = excel_sheets(source)
    if len(sheets) > 1:
        sheet = st.sidebar.selectbox("Sheet", sheets)

raw = read_table(source, name, sheet)
cols = raw.columns.tolist()
num_cols = numeric_columns(raw)
text_cols = [c for c in cols if c not in num_cols] or cols

# Column mapping — auto-detected, but editable in case the dataset uses other names.
with st.sidebar.expander("Column mapping", expanded=False):
    st.caption("Auto-detected from column names. If several score columns are picked, they are averaged per row.")

    def text_select(label, guess):
        options = [None] + cols
        return st.selectbox(label, options, index=options.index(guess) if guess in options else 0)

    dept_col = text_select("Department", guess_text(text_cols, ["depart", "dept", "faculty", "program"]))
    inst_col = text_select(
        "Instructor", guess_text(text_cols, ["instructor", "lecturer", "teacher", "professor"], prefer=["name"])
    )
    subj_col = text_select("Subject", guess_text(text_cols, ["subject", "course"], prefer=["code", "id"]))
    score_cols = {
        "Human Skill": st.multiselect("Human skill score column(s)", num_cols, guess_scores(num_cols, "human")),
        "Material": st.multiselect("Material score column(s)", num_cols, guess_scores(num_cols, "material")),
        "Teaching Skill": st.multiselect(
            "Teaching skill score column(s)", num_cols, guess_scores(num_cols, "teaching", exclude=["material"])
        ),
    }
    st.caption("Optional")
    year_col = text_select("Year", guess_text(cols, ["year"]))
    sem_col = text_select("Semester", guess_text(cols, ["semester", "term"]))
    resp_col = text_select("Respondents", guess_text(num_cols, ["respondent"]))
    enrol_col = text_select("Enrolled", guess_text(num_cols, ["enrol"]))

missing = [k for k, v in {"Department": dept_col, "Instructor": inst_col, "Subject": subj_col}.items() if v is None]
missing += [f"{k} score" for k, v in score_cols.items() if not v]
if missing:
    st.warning(
        "Couldn't find these columns automatically: **" + ", ".join(missing) + "**. "
        "Set them under **Column mapping** in the sidebar."
    )
    with st.expander("Preview of the dataset"):
        st.dataframe(raw.head(20), width="stretch")
    st.stop()

df = pd.DataFrame(
    {
        "Department": raw[dept_col].astype(str).str.strip(),
        "Instructor": raw[inst_col].astype(str).str.strip(),
        "Subject": raw[subj_col].astype(str).str.strip(),
        **{
            skill: raw[c].apply(pd.to_numeric, errors="coerce").mean(axis=1)
            for skill, c in score_cols.items()
        },
    }
)
for label, c in {"Year": year_col, "Semester": sem_col}.items():
    if c is not None:
        df[label] = raw[c]
for label, c in {"Respondents": resp_col, "Enrolled": enrol_col}.items():
    if c is not None:
        df[label] = pd.to_numeric(raw[c], errors="coerce")

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")
view = df
for label in ("Year", "Semester"):
    if label in df:
        options = sorted(df[label].dropna().unique())
        chosen = st.sidebar.multiselect(label, options, default=options)
        view = view[view[label].isin(chosen)]
departments = sorted(df["Department"].unique())
sel_depts = st.sidebar.multiselect("Department", departments, default=departments)
subjects = sorted(df.loc[df["Department"].isin(sel_depts), "Subject"].unique())
sel_subjects = st.sidebar.multiselect("Subject (blank = all)", subjects)

view = view[view["Department"].isin(sel_depts)]
if sel_subjects:
    view = view[view["Subject"].isin(sel_subjects)]
if view.empty:
    st.warning("No rows match the current filters.")
    st.stop()

default_threshold = round(float(view["Teaching Skill"].mean()), 2)
threshold = st.sidebar.slider(
    "Teaching support threshold",
    1.0,
    5.0,
    default_threshold,
    0.05,
    help="Instructors whose average teaching skill score is below this line are flagged for support. "
    "Defaults to the overall average.",
)

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
k = st.columns(4)
k[0].metric("Class sections", f"{len(view):,}", help="Each row of the dataset is one evaluated class section.")
k[1].metric("Instructors", view["Instructor"].nunique())
k[2].metric("Subjects", view["Subject"].nunique())
if {"Respondents", "Enrolled"} <= set(view.columns):
    k[3].metric(
        "Response rate",
        f"{view['Respondents'].sum() / view['Enrolled'].sum():.1%}",
        help=f"{view['Respondents'].sum():,.0f} respondents out of {view['Enrolled'].sum():,.0f} enrolled students.",
    )
k = st.columns(4)
for col, skill in zip(k, SKILLS):
    col.metric(SKILLS[skill], f"{view[skill].mean():.4f}")

# ---------------------------------------------------------------------------
# Figure 1
# ---------------------------------------------------------------------------
st.subheader("Figure 1: How do departments compare across the three skill areas?")
dept = view.groupby("Department")[list(SKILLS)].mean().sort_index()
st.plotly_chart(fig_department_heatmap(dept), width="stretch")
best = {s: (dept[s].idxmax(), dept[s].max()) for s in SKILLS}
st.caption(
    " · ".join(f"Strongest in {SKILLS[s].replace('Avg. ', '')}: **{d}** ({v:.2f})" for s, (d, v) in best.items())
)

# ---------------------------------------------------------------------------
# Figures 2 and 3
# ---------------------------------------------------------------------------
left, right = st.columns(2, gap="large")

with left:
    st.subheader("Figure 2: Which instructors need teaching support?")
    inst = (
        view.groupby(["Department", "Instructor"], as_index=False)["Teaching Skill"]
        .mean()
        .sort_values(["Department", "Teaching Skill"])
    )
    st.plotly_chart(fig_instructors(inst, threshold), width="stretch")
    flagged = inst[inst["Teaching Skill"] < threshold]
    st.caption(f"**{len(flagged)} of {len(inst)}** instructors are below the support threshold of {threshold:.2f}.")
    with st.expander("Instructors flagged for support"):
        st.dataframe(
            flagged.sort_values("Teaching Skill").style.format({"Teaching Skill": "{:.4f}"}),
            hide_index=True,
            width="stretch",
        )

with right:
    st.subheader("Figure 3: Which subjects have the weakest teaching materials?")
    subj = view.groupby("Subject", as_index=False)["Material"].mean().sort_values("Material")
    st.plotly_chart(fig_subjects(subj), width="stretch")
    below = subj[subj["Material"] < subj["Material"].mean()]
    st.caption(
        f"**{len(below)} of {len(subj)}** subjects score below the average material rating. "
        f"Weakest: **{subj.iloc[0]['Subject']}** ({subj.iloc[0]['Material']:.2f})."
    )

# ---------------------------------------------------------------------------
# Figure 4 (refinement): trend over time
# ---------------------------------------------------------------------------
if "Year" in view:
    st.subheader("Figure 4: How have the three skill areas changed over time?")
    split = st.radio("Show", ["All selected departments", "By department"], horizontal=True)
    keys = ["Year", "Semester"] if "Semester" in view else ["Year"]
    by = keys + (["Department"] if split == "By department" else [])
    trend = view.groupby(by, as_index=False)[list(SKILLS)].mean().sort_values(by)
    trend["Period"] = trend[keys].astype(str).agg(" S".join, axis=1) if len(keys) == 2 else trend["Year"].astype(str)
    st.plotly_chart(fig_trend(trend, "Department" if split == "By department" else None), width="stretch")

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
with st.expander("Filtered data"):
    st.dataframe(view, hide_index=True, width="stretch")
    st.download_button(
        "Download filtered data (CSV)",
        view.to_csv(index=False).encode("utf-8"),
        file_name="filtered_evaluations.csv",
        mime="text/csv",
    )
