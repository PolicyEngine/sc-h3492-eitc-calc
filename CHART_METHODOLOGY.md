# PolicyEngine Chart Methodology

This document describes how to create dynamic charts that match the PolicyEngine app-v2 methodology. Claude should read this when creating distributional impact charts for any PolicyEngine analysis.

## Dataset Selection

### State-Level Analysis
For US state-level analysis, use the state-specific dataset from HuggingFace:

```python
from policyengine_us import Microsimulation

# Use state-specific dataset (replace XX with state code)
dataset = "hf://policyengine/policyengine-us-data/states/XX.h5"
baseline = Microsimulation(dataset=dataset)
reform = Microsimulation(dataset=dataset, reform=your_reform)
```

**Do NOT** use the default `Microsimulation()` which loads national CPS data with very few state-specific records.

### National Analysis
For US national analysis:
```python
baseline = Microsimulation(dataset="enhanced_cps")
reform = Microsimulation(dataset="enhanced_cps", reform=your_reform)
```

## Winners and Losers by Decile Chart

This chart shows the percentage of **people** (not households) in each outcome category by income decile.

### Key Requirements

1. **Use person weights, not household weights**
2. **Use the exact app-v2 income_change formula**
3. **Use the correct outcome thresholds**

### Income Change Formula

The app-v2 uses a specific formula to handle edge cases with low/negative incomes:

```python
import numpy as np

# Calculate values
baseline_income = baseline.calculate("household_net_income", period=year).values
reform_income = reform.calculate("household_net_income", period=year).values
household_weight = baseline.calculate("household_weight", period=year).values
household_count_people = baseline.calculate("household_count_people", period=year).values
decile = baseline.calculate("household_income_decile", period=year).values

# App-v2 income_change formula (from policyengine-api compare.py lines 324-331)
absolute_change = reform_income - baseline_income
capped_baseline_income = np.maximum(baseline_income, 1)
capped_reform_income = np.maximum(reform_income, 1) + absolute_change
income_change = (capped_reform_income - capped_baseline_income) / capped_baseline_income
```

**Important**: Do NOT simplify this to `absolute_change / capped_baseline_income` - the app-v2 formula handles edge cases differently.

### Outcome Thresholds

The app-v2 uses these thresholds (as decimals, not percentages):

| Category | Condition |
|----------|-----------|
| Gain more than 5% | `income_change > 0.05` |
| Gain less than 5% | `income_change > 0.001 and income_change <= 0.05` |
| No change | `income_change > -0.001 and income_change <= 0.001` |
| Lose less than 5% | `income_change > -0.05 and income_change <= -0.001` |
| Lose more than 5% | `income_change <= -0.05` |

Note: "No change" is ±0.1%, NOT exactly zero.

### Person Weighting

The chart shows percentage of **people**, not households. Weight each household by number of people:

```python
# Person weights = household_weight * people_in_household
person_weights = household_weight * household_count_people

# For each decile and outcome category:
for decile_num in range(1, 11):
    in_decile = decile == decile_num
    in_outcome = income_change > 0.05  # example: gain >5%

    people_in_both = person_weights[in_decile & in_outcome].sum()
    people_in_decile = person_weights[in_decile].sum()

    percentage = people_in_both / people_in_decile  # as decimal, multiply by 100 for display
```

### "All" Population Calculation

The app-v2 calculates the "All" row as a simple average of the 10 decile percentages:

```python
all_percentage = sum(decile_percentages) / 10
```

Alternatively, you can calculate the true population-weighted percentage, which is more accurate.

## Average Benefit by Decile Chart

This chart shows the average dollar impact per **household** in each income decile.

### Methodology

Use household weights (not person weights) for this chart:

```python
avg_impact_by_decile = []
for decile_num in range(1, 11):
    in_decile = decile == decile_num

    # Weighted average of income change
    numerator = (absolute_change[in_decile] * household_weight[in_decile]).sum()
    denominator = household_weight[in_decile].sum()

    avg_impact = numerator / denominator
    avg_impact_by_decile.append(avg_impact)
```

## Net Income Change Chart (Household Simulation)

This chart shows change in net income for a specific household type across an income range.

### Methodology

```python
from policyengine_us import Simulation

employment_incomes = range(0, 200001, 1000)
net_income_changes = []

for income in employment_incomes:
    situation = build_household_situation(income, ...)

    baseline_sim = Simulation(situation=situation)
    reform_sim = Simulation(situation=situation, reform=your_reform)

    baseline_net = baseline_sim.calculate("household_net_income", year)
    reform_net = reform_sim.calculate("household_net_income", year)

    change = float(reform_net[0]) - float(baseline_net[0])
    net_income_changes.append(change)
```

## Chart Styling (PolicyEngine Brand)

Use these colors for consistency with PolicyEngine branding:

```python
# PolicyEngine app-v2 color palette
PRIMARY_500 = "#319795"  # Main teal brand color
PRIMARY_700 = "#285E61"  # Dark teal for gains >5%
PRIMARY_ALPHA_60 = "rgba(49, 151, 149, 0.6)"  # Teal with 60% opacity for gains <5%
GRAY_200 = "#E5E7EB"  # No change
GRAY_400 = "#9CA3AF"  # Loss <5%
GRAY_600 = "#4B5563"  # Loss >5%
BLACK = "#000000"

# Font
font_family = "Roboto Serif"
```

### Watermark

Add PolicyEngine logo watermark to charts:

```python
WATERMARK_CONFIG = {
    "source": "https://policyengine.github.io/YOUR-REPO/teal-square-transparent.png",
    "xref": "paper",
    "yref": "paper",
    "sizex": 0.07,
    "sizey": 0.07,
    "xanchor": "right",
    "yanchor": "bottom",
    "x": 1.05,
    "y": -0.18,
}
```

## Reference Implementation

See the following files in this repository for a complete working implementation:

- `sc_h3492_eitc/dynamic_charts/microsim.py` - Microsimulation data calculation
- `sc_h3492_eitc/dynamic_charts/charts.py` - Plotly chart generation
- `generate_dynamic_charts.py` - Chart generation script

## Common Mistakes to Avoid

1. **Using household weights for winners/losers** - Must use person weights (household_weight * household_count_people)

2. **Using simplified income_change formula** - Must use the exact app-v2 formula with capped_reform_income

3. **Using "exactly zero" for no change** - Must use ±0.1% threshold

4. **Using default Microsimulation()** - Must specify state-specific dataset for state analysis

5. **Using percentage instead of decimal for thresholds** - Thresholds are 0.05, not 5

## Verification

To verify charts match the app, compare against the PolicyEngine app-v2 for the same reform:
1. Run the reform in the app at policyengine.org
2. Compare decile 1 and decile 2 values for winners/losers
3. Values should match within ~1% (small differences due to rounding/dataset versions)
