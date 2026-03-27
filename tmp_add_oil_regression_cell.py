from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell


NOTEBOOK_PATH = Path("macro-analysis.ipynb")


NEW_CELL = """# ── Chart 7b: BTC vs Oil scatter plot with OLS regression ─────────────
x_col      = "Oil"
y_col      = "BTC"
start_date = "2000-01-01"

import statsmodels.api as sm
import plotly.express as px

oil_file = r"data\\btc_oil_bybit_thahbib.xlsx"

oil_df = (
    pd.read_excel(oil_file, parse_dates=["Date"])
    .rename(columns={
        "CL1 COMB Comdty  (R1)": "Oil",
        "XBTUSD BGN Curncy  (L1)": "BTC",
    })
    .set_index("Date")
    .sort_index()
)

# Filter and prepare data
scatter_df = oil_df[[x_col, y_col]].loc[start_date:].dropna().copy()

# OLS regression
X = sm.add_constant(scatter_df[x_col])
model = sm.OLS(scatter_df[y_col], X).fit()
scatter_df["Regression_Line"] = model.predict(X)
regression_label = f"R² = {model.rsquared:.4f}"

# Year labels for colour axis
scatter_df["Year"] = scatter_df.index.year.astype(str)
year_order = sorted(scatter_df["Year"].unique(), key=int)
year_to_num = {y: i for i, y in enumerate(year_order)}
scatter_df["YearNum"] = scatter_df["Year"].map(year_to_num)

# Scatter
fig7b = px.scatter(
    scatter_df,
    x=x_col, y=y_col,
    color="YearNum",
    color_continuous_scale="Peach",
    labels={"YearNum": "Year"},
)

# Regression line
fig7b.add_trace(go.Scatter(
    x=scatter_df[x_col],
    y=scatter_df["Regression_Line"],
    mode="lines", name=regression_label,
    line=dict(color="white", width=2),
))

# Highlight latest point
latest = scatter_df.iloc[-1]
fig7b.add_trace(go.Scatter(
    x=[latest[x_col]], y=[latest[y_col]],
    mode="markers", name="Latest",
    marker=dict(color="#14F195", size=15, symbol="x"),
    showlegend=True,
))

# Layout
fig7b.update_layout(
    height=1000, width=1000,
    font=dict(size=20, color="white"),
    plot_bgcolor="#101A2E", paper_bgcolor="#101A2E",
    hovermode="closest", title="",
    xaxis=dict(title=x_col, showgrid=True, gridcolor="#293e68",
               zeroline=False, tickformat="~s"),
    yaxis=dict(title=y_col, tickprefix="$", showgrid=True,
               gridcolor="#293e68", zeroline=False),
    legend=dict(orientation="h", yanchor="top", y=1.1,
                xanchor="center", x=0.5),
    margin=dict(l=150, r=30, b=50, t=80, pad=4),
    coloraxis_colorbar=dict(
        title="",
        tickvals=list(year_to_num.values()),
        ticktext=list(year_to_num.keys()),
    ),
)
add_watermark(fig7b)
fig7b
"""


def main() -> None:
    nb = nbformat.read(NOTEBOOK_PATH, as_version=4)
    target_idx = None
    for i, cell in enumerate(nb.cells):
        if cell.cell_type == "code" and "Chart 7: Scatter plot with OLS regression" in cell.source:
            target_idx = i
            break
    if target_idx is None:
        raise RuntimeError("Could not find Chart 7 regression cell.")

    insert_idx = target_idx + 1
    if insert_idx < len(nb.cells) and "Chart 7b: BTC vs Oil scatter plot with OLS regression" in nb.cells[insert_idx].source:
        nb.cells[insert_idx] = new_code_cell(NEW_CELL)
    else:
        nb.cells.insert(insert_idx, new_code_cell(NEW_CELL))

    nbformat.write(nb, NOTEBOOK_PATH)


if __name__ == "__main__":
    main()
