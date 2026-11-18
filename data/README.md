# Dataset

Put the class dataset here (CSV or Excel). The app picks up any `.csv`, `.xlsx` or `.xls` file in this folder.

The app looks for these columns by name (case and spacing don't matter):

| Role | Matched by a column name containing |
| --- | --- |
| Department | `department`, `dept`, `faculty`, `program` |
| Instructor | `instructor`, `lecturer`, `teacher`, `professor` |
| Subject | `subject`, `course` |
| Human skill score | `human` |
| Material score | `material` |
| Teaching skill score | `teaching` |

If several columns match one score (for example one per survey question), they're averaged per response.
If a column isn't found, set it under **Column mapping** in the sidebar.

The dataset itself is class material, so it isn't committed to git (see `.gitignore`).
