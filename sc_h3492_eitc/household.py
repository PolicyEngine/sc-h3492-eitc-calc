"""Household impact calculations for SC H.3492 Partially Refundable EITC.

Uses actual PolicyEngine-US calculations rather than hardcoded approximations.
Uses axes for efficient vectorized calculations.
"""

from policyengine_us import Simulation

from .reform import sc_h3492_reform, sc_no_eitc_baseline

# State FIPS codes for setting household state
STATE_FIPS = {
    "SC": 45,  # South Carolina
}


def calculate_net_income_by_earnings(
    state: str = "SC",
    num_children: int = 1,
    min_income: int = 0,
    max_income: int = 200000,
    step: int = 1000,
    year: int = 2026,
) -> tuple[list[int], list[float], list[float]]:
    """
    Calculate baseline and reform net income across employment income range.

    Uses actual PolicyEngine-US simulations to compute net income under
    current law (125% EITC) and SC H.3492 reform scenarios.

    Uses axes for efficient vectorized calculation.

    Args:
        state: State code (default "SC" for South Carolina)
        num_children: Number of children in household (default 1)
        min_income: Minimum employment income to calculate
        max_income: Maximum employment income to calculate
        step: Income increment step size
        year: Tax year to simulate

    Returns:
        Tuple of (employment_income_values, baseline_net_incomes, reform_net_incomes)
    """
    # Build situation with axes for vectorized calculation
    situation = _build_household_situation_with_axes(
        state=state,
        num_children=num_children,
        min_income=min_income,
        max_income=max_income,
        step=step,
        year=year,
    )

    # Run baseline simulation (current law: 125% nonrefundable EITC)
    baseline_sim = Simulation(situation=situation)
    baseline_net = baseline_sim.calculate("household_net_income", year)

    # Run reform simulation (H.3492: 125% + 25% refundable)
    reform_sim = Simulation(situation=situation, reform=sc_h3492_reform)
    reform_net = reform_sim.calculate("household_net_income", year)

    employment_income_values = list(range(min_income, max_income + 1, step))
    return (
        employment_income_values,
        baseline_net.tolist(),
        reform_net.tolist(),
    )


def _build_household_situation_with_axes(
    state: str,
    num_children: int,
    min_income: int,
    max_income: int,
    step: int,
    year: int,
) -> dict:
    """
    Build a PolicyEngine situation with axes for vectorized income calculations.

    Args:
        state: State code (e.g., "SC" for South Carolina)
        num_children: Number of children
        min_income: Minimum employment income
        max_income: Maximum employment income
        step: Income step size
        year: Tax year

    Returns:
        Situation dictionary with axes for PolicyEngine Simulation
    """
    # Get state FIPS code
    state_fips = STATE_FIPS.get(state, 45)  # Default to SC

    # Create people dictionary (income will be set via axes)
    people = {
        "adult": {
            "age": {year: 35},
        }
    }

    # Add children
    members = ["adult"]
    for i in range(num_children):
        child_name = f"child_{i + 1}"
        people[child_name] = {
            "age": {year: 5 + i},  # Ages 5, 6, 7, etc.
        }
        members.append(child_name)

    num_points = len(range(min_income, max_income + 1, step))

    return {
        "people": people,
        "tax_units": {
            "tax_unit": {
                "members": members,
            }
        },
        "spm_units": {
            "spm_unit": {
                "members": members,
            }
        },
        "households": {
            "household": {
                "members": members,
                "state_fips": {year: state_fips},
            }
        },
        "families": {
            "family": {
                "members": members,
            }
        },
        "marital_units": {
            "marital_unit": {
                "members": ["adult"],
            }
        },
        "axes": [
            [
                {
                    "name": "employment_income",
                    "min": min_income,
                    "max": max_income,
                    "count": num_points,
                    "period": year,
                }
            ]
        ],
    }


def calculate_eitc_benefits_by_earnings(
    state: str = "SC",
    num_children: int = 1,
    min_income: int = 0,
    max_income: int = 200000,
    step: int = 1000,
    year: int = 2026,
) -> tuple[list[int], list[float], list[float]]:
    """
    Calculate the EITC benefits under current law and H.3492 reform.

    Computes:
    - Current law EITC benefit: actual SC EITC received (125% nonrefundable, limited by tax liability)
    - H.3492 EITC benefit: actual SC EITC received (125% nonrefundable + 25% refundable excess)

    Both are measured relative to a no-EITC baseline so they represent actual dollars received.

    Uses axes for efficient vectorized calculation.

    Args:
        state: State code (default "SC" for South Carolina)
        num_children: Number of children in household (default 1)
        min_income: Minimum employment income to calculate
        max_income: Maximum employment income to calculate
        step: Income increment step size
        year: Tax year to simulate

    Returns:
        Tuple of (employment_income_values, current_law_benefits, h3492_benefits)
    """
    # Build situation with axes for vectorized calculation
    situation = _build_household_situation_with_axes(
        state=state,
        num_children=num_children,
        min_income=min_income,
        max_income=max_income,
        step=step,
        year=year,
    )

    # No EITC simulation (0% EITC rate)
    no_eitc_sim = Simulation(situation=situation, reform=sc_no_eitc_baseline)
    no_eitc_net = no_eitc_sim.calculate("household_net_income", year)

    # Current law simulation (125% nonrefundable EITC - policyengine-us baseline)
    current_law_sim = Simulation(situation=situation)
    current_law_net = current_law_sim.calculate("household_net_income", year)

    # H.3492 simulation (125% EITC + 25% refundable)
    h3492_sim = Simulation(situation=situation, reform=sc_h3492_reform)
    h3492_net = h3492_sim.calculate("household_net_income", year)

    # Calculate benefits (vectorized) - both relative to no EITC baseline
    # This shows actual EITC dollars received under each policy
    current_law_benefits = current_law_net - no_eitc_net
    h3492_benefits = h3492_net - no_eitc_net

    employment_income_values = list(range(min_income, max_income + 1, step))
    return (
        employment_income_values,
        current_law_benefits.tolist(),
        h3492_benefits.tolist(),
    )
