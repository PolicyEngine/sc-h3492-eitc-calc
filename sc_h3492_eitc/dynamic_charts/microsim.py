"""Microsimulation data fetching for dynamic charts.

Uses PolicyEngine-US to calculate distributional impacts by income decile
for South Carolina residents only.
"""

import numpy as np
from policyengine_us import Microsimulation
from policyengine_us.variables.household.demographic.geographic.state_code import (
    StateCode,
)

from ..reform import sc_h3492_reform


def calculate_decile_impacts(year: int = 2026) -> dict:
    """
    Calculate distributional impacts by income decile using microsimulation.

    Filters to South Carolina residents only.
    Uses household-level weights for outcome percentages and average dollar impacts.

    Args:
        year: The tax year to simulate

    Returns:
        Dictionary with:
        - decile_outcomes: dict with percentages for each outcome category by decile
        - all_outcomes: dict with overall population percentages
        - avg_impact_by_decile: list of average dollar impacts per decile (household-weighted)
    """
    print(f"Running microsimulation for South Carolina, {year}...")

    # Run baseline and reform simulations
    baseline = Microsimulation()
    reform = Microsimulation(reform=sc_h3492_reform)

    # =========================================================================
    # HOUSEHOLD-LEVEL DATA (for average impact by decile)
    # =========================================================================
    household_income_decile_hh = baseline.calculate(
        "household_income_decile", period=year
    ).values
    household_weights_hh = baseline.calculate("household_weight", period=year).values
    baseline_income_hh = baseline.calculate("household_net_income", period=year).values
    reform_income_hh = reform.calculate("household_net_income", period=year).values

    # Get state codes at household level - state_code is a household variable
    state_codes = baseline.calculate("state_code", period=year).values

    # Filter to South Carolina households (StateCode.SC enum value)
    # The state_code returns encoded enum values
    sc_code = StateCode.SC.index
    sc_mask = state_codes == sc_code

    # Apply SC filter
    household_income_decile_hh = household_income_decile_hh[sc_mask]
    household_weights_hh = household_weights_hh[sc_mask]
    baseline_income_hh = baseline_income_hh[sc_mask]
    reform_income_hh = reform_income_hh[sc_mask]

    # Calculate change at household level
    income_change_hh = reform_income_hh - baseline_income_hh

    print(f"  SC households: {sc_mask.sum():,}")
    print(f"  SC households with change: {(income_change_hh != 0).sum():,}")

    # Calculate average impact by decile (household-weighted)
    avg_impact_by_decile = []
    for decile in range(1, 11):
        in_decile_hh = household_income_decile_hh == decile
        decile_weight_hh = household_weights_hh[in_decile_hh].sum()
        if decile_weight_hh > 0:
            avg_impact = (
                (income_change_hh[in_decile_hh] * household_weights_hh[in_decile_hh]).sum()
                / decile_weight_hh
            )
            avg_impact_by_decile.append(round(avg_impact, 0))
        else:
            avg_impact_by_decile.append(0)

    # =========================================================================
    # OUTCOME PERCENTAGES (household-weighted)
    # =========================================================================
    # Calculate percentage change at household level
    pct_change_hh = np.where(
        baseline_income_hh > 0,
        (income_change_hh / baseline_income_hh) * 100,
        0,
    )

    # Categorize households by outcome
    gain_more_5_hh = pct_change_hh > 5
    gain_less_5_hh = (pct_change_hh > 0) & (pct_change_hh <= 5)
    no_change_hh = income_change_hh == 0
    loss_less_5_hh = (pct_change_hh < 0) & (pct_change_hh >= -5)
    loss_more_5_hh = pct_change_hh < -5

    # Use household weights for outcome percentages
    outcome_weights = household_weights_hh

    # Calculate outcomes by decile (household-weighted)
    decile_outcomes = {
        "gain_more_than_5pct": [],
        "gain_less_than_5pct": [],
        "no_change": [],
        "loss_less_than_5pct": [],
        "loss_more_than_5pct": [],
    }

    for decile in range(1, 11):
        in_decile = household_income_decile_hh == decile
        decile_weight = outcome_weights[in_decile].sum()

        if decile_weight > 0:
            decile_outcomes["gain_more_than_5pct"].append(
                round((outcome_weights[in_decile & gain_more_5_hh].sum() / decile_weight) * 100, 1)
            )
            decile_outcomes["gain_less_than_5pct"].append(
                round((outcome_weights[in_decile & gain_less_5_hh].sum() / decile_weight) * 100, 1)
            )
            decile_outcomes["no_change"].append(
                round((outcome_weights[in_decile & no_change_hh].sum() / decile_weight) * 100, 1)
            )
            decile_outcomes["loss_less_than_5pct"].append(
                round((outcome_weights[in_decile & loss_less_5_hh].sum() / decile_weight) * 100, 1)
            )
            decile_outcomes["loss_more_than_5pct"].append(
                round((outcome_weights[in_decile & loss_more_5_hh].sum() / decile_weight) * 100, 1)
            )
        else:
            for key in decile_outcomes:
                decile_outcomes[key].append(0)

    # Calculate overall population outcomes
    total_weight = outcome_weights.sum()
    all_outcomes = {
        "gain_more_than_5pct": round(
            (outcome_weights[gain_more_5_hh].sum() / total_weight) * 100, 1
        ),
        "gain_less_than_5pct": round(
            (outcome_weights[gain_less_5_hh].sum() / total_weight) * 100, 1
        ),
        "no_change": round((outcome_weights[no_change_hh].sum() / total_weight) * 100, 1),
        "loss_less_than_5pct": round(
            (outcome_weights[loss_less_5_hh].sum() / total_weight) * 100, 1
        ),
        "loss_more_than_5pct": round(
            (outcome_weights[loss_more_5_hh].sum() / total_weight) * 100, 1
        ),
    }

    # Debug info
    print(f"  Max pct_change: {pct_change_hh.max():.2f}%")
    print(f"  Households with >5% gain: {gain_more_5_hh.sum()}")
    print(f"  Overall gain >5%: {all_outcomes['gain_more_than_5pct']}%")
    print(f"  Decile 1 gain >5%: {decile_outcomes['gain_more_than_5pct'][0]}%")

    return {
        "decile_outcomes": decile_outcomes,
        "all_outcomes": all_outcomes,
        "avg_impact_by_decile": avg_impact_by_decile,
    }


def main():
    """Run the microsimulation and print results for verification."""
    print("=" * 60)
    print("SC H.3492 Dynamic Charts - Microsimulation Data")
    print("=" * 60)
    print()

    results = calculate_decile_impacts()

    print("\nDecile Outcomes (%):")
    print("-" * 60)
    print(f"{'Decile':<8} {'Gain>5%':<10} {'Gain<5%':<10} {'No Change':<10} {'Loss<5%':<10} {'Loss>5%':<10}")
    print("-" * 60)
    for i in range(10):
        print(
            f"{i+1:<8} "
            f"{results['decile_outcomes']['gain_more_than_5pct'][i]:<10.1f} "
            f"{results['decile_outcomes']['gain_less_than_5pct'][i]:<10.1f} "
            f"{results['decile_outcomes']['no_change'][i]:<10.1f} "
            f"{results['decile_outcomes']['loss_less_than_5pct'][i]:<10.1f} "
            f"{results['decile_outcomes']['loss_more_than_5pct'][i]:<10.1f}"
        )

    print("\nOverall Population Outcomes (%):")
    print("-" * 60)
    for key, value in results["all_outcomes"].items():
        print(f"  {key}: {value:.1f}%")

    print("\nAverage Impact by Decile ($):")
    print("-" * 60)
    for i, impact in enumerate(results["avg_impact_by_decile"], 1):
        print(f"  Decile {i}: ${impact:.0f}")


if __name__ == "__main__":
    main()
