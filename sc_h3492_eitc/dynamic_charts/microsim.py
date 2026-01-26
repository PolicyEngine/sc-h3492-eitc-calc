"""Microsimulation data fetching for dynamic charts.

Uses PolicyEngine-US to calculate distributional impacts by income decile
for South Carolina residents only.
"""

import numpy as np
from policyengine_us import Microsimulation

from ..reform import sc_h3492_reform


def calculate_decile_impacts(year: int = 2026) -> dict:
    """
    Calculate distributional impacts by income decile using microsimulation.

    Filters to South Carolina residents only.
    Uses person-weighted outcomes (matching app-v2 methodology) and
    household-weighted average dollar impacts.

    Args:
        year: The tax year to simulate

    Returns:
        Dictionary with:
        - decile_outcomes: dict with percentages for each outcome category by decile
        - all_outcomes: dict with overall population percentages
        - avg_impact_by_decile: list of average dollar impacts per decile (household-weighted)
    """
    print(f"Running microsimulation for South Carolina, {year}...")

    # Run baseline and reform simulations using SC-specific dataset
    dataset = "hf://policyengine/policyengine-us-data/states/SC.h5"
    baseline = Microsimulation(dataset=dataset)
    reform = Microsimulation(dataset=dataset, reform=sc_h3492_reform)

    # =========================================================================
    # HOUSEHOLD-LEVEL DATA
    # =========================================================================
    household_income_decile_hh = baseline.calculate(
        "household_income_decile", period=year
    ).values
    household_weights_hh = baseline.calculate("household_weight", period=year).values
    baseline_income_hh = baseline.calculate("household_net_income", period=year).values
    reform_income_hh = reform.calculate("household_net_income", period=year).values
    # Get people count per household for person-weighted outcomes (matches app-v2)
    household_count_people_hh = baseline.calculate(
        "household_count_people", period=year
    ).values

    # Get state codes at household level using state_code_str (returns string like "SC")
    state_codes_str = baseline.calculate("state_code_str", period=year).values

    # Filter to South Carolina households
    sc_mask = state_codes_str == "SC"

    # Apply SC filter
    household_income_decile_hh = household_income_decile_hh[sc_mask]
    household_weights_hh = household_weights_hh[sc_mask]
    baseline_income_hh = baseline_income_hh[sc_mask]
    reform_income_hh = reform_income_hh[sc_mask]
    household_count_people_hh = household_count_people_hh[sc_mask]

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
    # OUTCOME PERCENTAGES (person-weighted, matching app-v2 methodology)
    # =========================================================================
    # Cap baseline income at $1 minimum to prevent division issues (matches app-v2)
    capped_baseline_income = np.maximum(baseline_income_hh, 1)

    # Calculate percentage change using capped baseline (as decimal, not percentage)
    pct_change_hh = income_change_hh / capped_baseline_income

    # Categorize households by outcome using app-v2 thresholds:
    # - Gain >5%: pct_change > 0.05
    # - Gain <5%: pct_change > 0.001 and <= 0.05 (0.1% to 5%)
    # - No change: pct_change > -0.001 and <= 0.001 (±0.1%)
    # - Loss <5%: pct_change > -0.05 and <= -0.001 (-5% to -0.1%)
    # - Loss >5%: pct_change <= -0.05
    gain_more_5_hh = pct_change_hh > 0.05
    gain_less_5_hh = (pct_change_hh > 0.001) & (pct_change_hh <= 0.05)
    no_change_hh = (pct_change_hh > -0.001) & (pct_change_hh <= 0.001)
    loss_less_5_hh = (pct_change_hh > -0.05) & (pct_change_hh <= -0.001)
    loss_more_5_hh = pct_change_hh <= -0.05

    # Use person weights for outcome percentages (matches app-v2)
    # This weights each household by number of people * household_weight
    person_weights = household_weights_hh * household_count_people_hh

    # Calculate outcomes by decile (person-weighted)
    decile_outcomes = {
        "gain_more_than_5pct": [],
        "gain_less_than_5pct": [],
        "no_change": [],
        "loss_less_than_5pct": [],
        "loss_more_than_5pct": [],
    }

    for decile in range(1, 11):
        in_decile = household_income_decile_hh == decile
        decile_people = person_weights[in_decile].sum()

        if decile_people > 0:
            decile_outcomes["gain_more_than_5pct"].append(
                round((person_weights[in_decile & gain_more_5_hh].sum() / decile_people) * 100, 1)
            )
            decile_outcomes["gain_less_than_5pct"].append(
                round((person_weights[in_decile & gain_less_5_hh].sum() / decile_people) * 100, 1)
            )
            decile_outcomes["no_change"].append(
                round((person_weights[in_decile & no_change_hh].sum() / decile_people) * 100, 1)
            )
            decile_outcomes["loss_less_than_5pct"].append(
                round((person_weights[in_decile & loss_less_5_hh].sum() / decile_people) * 100, 1)
            )
            decile_outcomes["loss_more_than_5pct"].append(
                round((person_weights[in_decile & loss_more_5_hh].sum() / decile_people) * 100, 1)
            )
        else:
            for key in decile_outcomes:
                decile_outcomes[key].append(0)

    # Calculate overall population outcomes (person-weighted)
    total_people = person_weights.sum()
    if total_people > 0:
        all_outcomes = {
            "gain_more_than_5pct": round(
                (person_weights[gain_more_5_hh].sum() / total_people) * 100, 1
            ),
            "gain_less_than_5pct": round(
                (person_weights[gain_less_5_hh].sum() / total_people) * 100, 1
            ),
            "no_change": round((person_weights[no_change_hh].sum() / total_people) * 100, 1),
            "loss_less_than_5pct": round(
                (person_weights[loss_less_5_hh].sum() / total_people) * 100, 1
            ),
            "loss_more_than_5pct": round(
                (person_weights[loss_more_5_hh].sum() / total_people) * 100, 1
            ),
        }
    else:
        all_outcomes = {
            "gain_more_than_5pct": 0,
            "gain_less_than_5pct": 0,
            "no_change": 100,
            "loss_less_than_5pct": 0,
            "loss_more_than_5pct": 0,
        }

    # Debug info
    if len(pct_change_hh) > 0:
        print(f"  Max pct_change: {pct_change_hh.max() * 100:.2f}%")
        print(f"  Households with >5% gain: {gain_more_5_hh.sum()}")
        print(f"  Overall gain >5%: {all_outcomes['gain_more_than_5pct']}%")
        print(f"  Decile 1 gain >5%: {decile_outcomes['gain_more_than_5pct'][0]}%")
    else:
        print("  WARNING: No SC households found in microsimulation data!")

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
