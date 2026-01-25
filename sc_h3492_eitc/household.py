"""Household impact calculations for SC H.3492 Partially Refundable EITC.

Uses actual PolicyEngine-US calculations rather than hardcoded approximations.
"""

from policyengine_us import Simulation

from .reform import sc_h3492_reform

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
    baseline and SC H.3492 reform scenarios.

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
    employment_income_values = list(range(min_income, max_income + 1, step))
    baseline_net_incomes = []
    reform_net_incomes = []

    for income in employment_income_values:
        # Build household situation
        situation = _build_household_situation(
            state=state,
            num_children=num_children,
            employment_income=income,
            year=year,
        )

        # Run baseline simulation
        baseline_sim = Simulation(situation=situation)
        baseline_net = baseline_sim.calculate("household_net_income", year)
        baseline_net_incomes.append(float(baseline_net[0]))

        # Run reform simulation
        reform_sim = Simulation(situation=situation, reform=sc_h3492_reform)
        reform_net = reform_sim.calculate("household_net_income", year)
        reform_net_incomes.append(float(reform_net[0]))

    return employment_income_values, baseline_net_incomes, reform_net_incomes


def _build_household_situation(
    state: str,
    num_children: int,
    employment_income: float,
    year: int,
) -> dict:
    """
    Build a PolicyEngine situation dictionary for a single parent household.

    Args:
        state: State code (e.g., "SC" for South Carolina)
        num_children: Number of children
        employment_income: Annual employment income
        year: Tax year

    Returns:
        Situation dictionary for PolicyEngine Simulation
    """
    # Get state FIPS code
    state_fips = STATE_FIPS.get(state, 45)  # Default to SC

    # Create people dictionary
    people = {
        "adult": {
            "age": {year: 35},
            "employment_income": {year: employment_income},
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
    }
