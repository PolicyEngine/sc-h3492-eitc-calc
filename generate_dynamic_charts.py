"""Generate dynamic charts for SC H.3492 Partially Refundable EITC analysis.

This script generates charts using live PolicyEngine-US microsimulation data
for South Carolina residents.
"""

from pathlib import Path

from sc_h3492_eitc.dynamic_charts import (
    calculate_decile_impacts,
    create_dynamic_winners_by_decile_chart,
    create_dynamic_avg_benefit_by_decile_chart,
    create_dynamic_net_income_change_chart,
)

# Output directories
OUTPUT_DIR = Path("output")
CHARTS_DIR = OUTPUT_DIR / "charts"

# HTML template for standalone chart files
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Serif:wght@400;500;600&display=swap" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Roboto Serif', serif;
        }}
        #chart {{
            width: 100%;
            height: 100vh;
        }}
    </style>
</head>
<body>
    <div id="chart"></div>
    <script>
        var figure = {figure_json};
        Plotly.newPlot('chart', figure.data, figure.layout, {{responsive: true}});
    </script>
</body>
</html>
"""


def generate_chart_html(fig, title: str, filename: str) -> None:
    """Generate standalone HTML file for a Plotly chart."""
    html_content = HTML_TEMPLATE.format(
        title=title,
        figure_json=fig.to_json(),
    )

    filepath = CHARTS_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Generated: {filepath}")


def main():
    """Generate all dynamic chart files."""
    # Create output directories
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Generating DYNAMIC charts for SC H.3492 Partially Refundable EITC")
    print("Using PolicyEngine-US microsimulation")
    print("=" * 60)
    print()

    # Step 1: Generate net income change chart (household simulation)
    # Use step=100 for smooth curve (2001 data points)
    print("Step 1: Generating net income change chart...")
    fig1 = create_dynamic_net_income_change_chart(num_children=1, max_income=200000, step=100)
    generate_chart_html(
        fig1,
        "Net Income Change - SC H.3492 Partially Refundable EITC",
        "net-income-change.html",
    )
    print()

    # Step 2: Run microsimulation to get decile data
    print("Step 2: Running microsimulation for decile charts...")
    microsim_data = calculate_decile_impacts()
    print("Microsimulation complete.")
    print()

    # Step 3: Generate distributional charts
    print("Step 3: Generating distributional charts...")
    print()

    # Chart 2: Winners/Losers by decile
    print("Creating winners by decile chart...")
    fig2 = create_dynamic_winners_by_decile_chart(microsim_data)
    generate_chart_html(
        fig2,
        "Winners by Income Decile - SC H.3492 Partially Refundable EITC",
        "winners-by-decile.html",
    )

    # Chart 3: Average benefit by decile
    print("Creating average benefit by decile chart...")
    fig3 = create_dynamic_avg_benefit_by_decile_chart(microsim_data)
    generate_chart_html(
        fig3,
        "Average Benefit by Income Decile - SC H.3492 Partially Refundable EITC",
        "avg-benefit-by-decile.html",
    )

    print()
    print("=" * 60)
    print("Done! Dynamic charts generated in output/charts/")
    print("=" * 60)
    print()
    print("Chart URLs after deployment:")
    print("  https://policyengine.github.io/sc-h3492-eitc-calc/net-income-change.html")
    print("  https://policyengine.github.io/sc-h3492-eitc-calc/winners-by-decile.html")
    print("  https://policyengine.github.io/sc-h3492-eitc-calc/avg-benefit-by-decile.html")


if __name__ == "__main__":
    main()
