"""South Carolina H.3492 Partially Refundable EITC reform definition."""

from policyengine_core.reforms import Reform

from policyengine_us.reforms.states.sc.h3492.sc_h3492_eitc_refundable import (
    create_sc_h3492_eitc_refundable,
)

# Use the pre-built reform from policyengine-us
# This reform makes 25% of the excess state EITC refundable
sc_h3492_reform = create_sc_h3492_eitc_refundable()

# Baseline reform: No SC EITC (rate = 0)
# Used to show the benefit of having the current 125% EITC
sc_no_eitc_baseline = Reform.from_dict(
    {
        "gov.states.sc.tax.income.credits.eitc.rate": {
            "2026-01-01.2100-12-31": 0,
        },
    },
    country_id="us",
)

# Current law EITC reform (125% match rate, nonrefundable)
# Explicitly sets the rate to 1.25 for clarity
sc_current_law_eitc_reform = Reform.from_dict(
    {
        "gov.states.sc.tax.income.credits.eitc.rate": {
            "2026-01-01.2100-12-31": 1.25,
        },
    },
    country_id="us",
)
