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
    create_dynamic_eitc_benefit_chart,
)

# Output directories
OUTPUT_DIR = Path("output")
CHARTS_DIR = OUTPUT_DIR / "charts"

# Base URL for GitHub Pages deployment
BASE_URL = "https://policyengine.github.io/sc-h3492-eitc-calc"

# Chart metadata for SEO (filename -> description)
CHART_METADATA = {
    "net-income-change.html": {
        "description": (
            "Interactive chart showing how South Carolina H.3492 partially "
            "refundable EITC changes net income for a single parent with one "
            "child across employment income levels. Powered by PolicyEngine."
        ),
    },
    "eitc-benefit-comparison.html": {
        "description": (
            "Interactive chart comparing South Carolina EITC benefits under "
            "current law vs H.3492 for a single parent with one child. Shows "
            "how making 25% of excess EITC refundable increases benefits. "
            "Powered by PolicyEngine."
        ),
    },
    "winners-by-decile.html": {
        "description": (
            "Interactive chart showing winners and losers of SC H.3492 "
            "partially refundable EITC by income decile. 23.3% of South "
            "Carolina residents benefit. Powered by PolicyEngine."
        ),
    },
    "avg-benefit-by-decile.html": {
        "description": (
            "Interactive chart showing the average dollar benefit of SC H.3492 "
            "partially refundable EITC by income decile. Estimated cost: $403 "
            "million in 2026. Powered by PolicyEngine."
        ),
    },
}

# HTML template for standalone chart files
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | PolicyEngine</title>
    <meta name="description" content="{meta_description}">
    <link rel="canonical" href="{canonical_url}">
    <meta name="theme-color" content="#319795">
    <link rel="icon" href="https://policyengine.org/favicon.ico" type="image/x-icon">

    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="article">
    <meta property="og:title" content="{title} | PolicyEngine">
    <meta property="og:description" content="{meta_description}">
    <meta property="og:url" content="{canonical_url}">
    <meta property="og:image" content="{og_image}">
    <meta property="og:site_name" content="PolicyEngine">

    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title} | PolicyEngine">
    <meta name="twitter:description" content="{meta_description}">
    <meta name="twitter:image" content="{og_image}">
    <meta name="twitter:site" content="@ThePolicyEngine">

    <!-- Preconnect for performance -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="preconnect" href="https://cdn.plot.ly">

    <link href="https://fonts.googleapis.com/css2?family=Roboto+Serif:wght@400;500;600&display=swap" rel="stylesheet">
    <script defer src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-2YHG89FY0N"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', 'G-2YHG89FY0N', {{ tool_name: 'sc-h3492-eitc-calc' }});
    </script>
    <script>
    (function() {{
      var TOOL_NAME = 'sc-h3492-eitc-calc';
      if (typeof window === 'undefined' || !window.gtag) return;

      var scrollFired = {{}};
      window.addEventListener('scroll', function() {{
        var docHeight = document.documentElement.scrollHeight - window.innerHeight;
        if (docHeight <= 0) return;
        var pct = Math.floor((window.scrollY / docHeight) * 100);
        [25, 50, 75, 100].forEach(function(m) {{
          if (pct >= m && !scrollFired[m]) {{
            scrollFired[m] = true;
            window.gtag('event', 'scroll_depth', {{ percent: m, tool_name: TOOL_NAME }});
          }}
        }});
      }}, {{ passive: true }});

      [30, 60, 120, 300].forEach(function(sec) {{
        setTimeout(function() {{
          if (document.visibilityState !== 'hidden') {{
            window.gtag('event', 'time_on_tool', {{ seconds: sec, tool_name: TOOL_NAME }});
          }}
        }}, sec * 1000);
      }});

      document.addEventListener('click', function(e) {{
        var link = e.target && e.target.closest ? e.target.closest('a') : null;
        if (!link || !link.href) return;
        try {{
          var url = new URL(link.href, window.location.origin);
          if (url.hostname && url.hostname !== window.location.hostname) {{
            window.gtag('event', 'outbound_click', {{
              url: link.href,
              target_hostname: url.hostname,
              tool_name: TOOL_NAME
            }});
          }}
        }} catch (err) {{}}
      }});
    }})();
    </script>

    <!-- Structured data (JSON-LD) -->
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "Dataset",
      "name": "{title}",
      "description": "{meta_description}",
      "url": "{canonical_url}",
      "creator": {{
        "@type": "Organization",
        "name": "PolicyEngine",
        "url": "https://policyengine.org"
      }},
      "license": "https://opensource.org/licenses/MIT",
      "temporalCoverage": "2026",
      "spatialCoverage": {{
        "@type": "Place",
        "name": "South Carolina, United States"
      }},
      "isPartOf": {{
        "@type": "WebSite",
        "name": "PolicyEngine",
        "url": "https://policyengine.org"
      }}
    }}
    </script>

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
        .sr-only {{
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }}
        noscript p {{
            padding: 2rem;
            text-align: center;
            font-size: 1.1rem;
            color: #4B5563;
        }}
    </style>
</head>
<body>
    <main>
        <h1 class="sr-only">{title}</h1>
        <div id="chart" role="img" aria-label="{title} - interactive chart by PolicyEngine"></div>
        <noscript>
            <p>This interactive chart requires JavaScript to display. Please enable
            JavaScript in your browser to view the {title} analysis from
            <a href="https://policyengine.org">PolicyEngine</a>.</p>
        </noscript>
    </main>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var figure = {figure_json};
            Plotly.newPlot('chart', figure.data, figure.layout, {{responsive: true}});
        }});
    </script>
</body>
</html>
"""


def generate_chart_html(fig, title: str, filename: str) -> None:
    """Generate standalone HTML file for a Plotly chart."""
    meta = CHART_METADATA.get(filename, {})
    description = meta.get("description", f"{title} - PolicyEngine analysis of South Carolina H.3492 partially refundable EITC.")
    canonical_url = f"{BASE_URL}/{filename}"
    og_image = f"{BASE_URL}/teal-square-transparent.png"

    html_content = HTML_TEMPLATE.format(
        title=title,
        meta_description=description,
        canonical_url=canonical_url,
        og_image=og_image,
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
    print("Step 1: Generating net income change chart...")
    fig1 = create_dynamic_net_income_change_chart(
        num_children=1, max_income=200000, step=1000
    )
    generate_chart_html(
        fig1,
        "Net Income Change - SC H.3492 Partially Refundable EITC",
        "net-income-change.html",
    )
    print()

    # Step 1b: Generate EITC benefit comparison chart
    print("Step 1b: Generating EITC benefit comparison chart...")
    fig1b = create_dynamic_eitc_benefit_chart(
        num_children=1, max_income=200000, step=1000
    )
    generate_chart_html(
        fig1b,
        "EITC Benefits Comparison - SC Current Law vs H.3492",
        "eitc-benefit-comparison.html",
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
    print(
        "  https://policyengine.github.io/sc-h3492-eitc-calc/eitc-benefit-comparison.html"
    )
    print("  https://policyengine.github.io/sc-h3492-eitc-calc/winners-by-decile.html")
    print(
        "  https://policyengine.github.io/sc-h3492-eitc-calc/avg-benefit-by-decile.html"
    )


if __name__ == "__main__":
    main()
