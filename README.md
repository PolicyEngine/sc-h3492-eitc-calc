# South Carolina H.3492 Partially Refundable EITC Calculator

Analysis of South Carolina H.3492, which would make 25% of the excess state EITC refundable for tax year 2026.

## Key Findings

- **Cost**: $403 million in 2026
- **Beneficiaries**: 23.3% of South Carolina residents
- **Poverty Reduction**: 2.1%
- **Child Poverty Reduction**: 4.8%

## Usage

### Installation

```bash
pip install -e .
```

### Generate Charts

```bash
python generate_dynamic_charts.py
```

This will create HTML chart files in `output/charts/`:
- `net-income-change.html` - Net income change for a single parent with one child
- `winners-by-decile.html` - Winners by income decile
- `avg-benefit-by-decile.html` - Average benefit by income decile

## Charts

After deployment, charts are available at:
- https://policyengine.github.io/sc-h3492-eitc-calc/net-income-change.html
- https://policyengine.github.io/sc-h3492-eitc-calc/winners-by-decile.html
- https://policyengine.github.io/sc-h3492-eitc-calc/avg-benefit-by-decile.html

## License

MIT
