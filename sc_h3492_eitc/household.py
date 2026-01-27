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

    Uses PolicyEngine axes to compute all income points in a single simulation
    pair (one baseline, one reform) rather than per-point.

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
    count = ((max_income - min_income) // step) + 1
    employment_income_values = list(range(min_income, max_income + 1, step))

    # Build situation with axes to vary employment income across the range
    situation = _build_household_situation_with_axes(
        state=state,
        num_children=num_children,
        min_income=min_income,
        max_income=max_income,
        count=count,
        year=year,
    )

    # Run baseline simulation (single sim for all income points)
    baseline_sim = Simulation(situation=situation)
    baseline_net = baseline_sim.calculate("household_net_income", year)
    baseline_net_incomes = [float(v) for v in baseline_net]

    # Run reform simulation (single sim for all income points)
    reform_sim = Simulation(situation=situation, reform=sc_h3492_reform)
    reform_net = reform_sim.calculate("household_net_income", year)
    reform_net_incomes = [float(v) for v in reform_net]

    return employment_income_values, baseline_net_incomes, reform_net_incomes


def _build_household_situation_with_axes(
    state: str,
    num_children: int,
    min_income: int,
    max_income: int,
    count: int,
    year: int,
) -> dict:
    """
    Build a PolicyEngine situation with axes to vary employment income.

    Uses a single simulation with axes instead of creating separate
    simulations per income point.

    Args:
        state: State code (e.g., "SC" for South Carolina)
        num_children: Number of children
        min_income: Minimum employment income
        max_income: Maximum employment income
        count: Number of data points
        year: Tax year

    Returns:
        Situation dictionary with axes for PolicyEngine Simulation
    """
    state_fips = STATE_FIPS.get(state, 45)

    people = {
        "adult": {
            "age": {year: 35},
            "employment_income": {year: 0},
        }
    }

    members = ["adult"]
    for i in range(num_children):
        child_name = f"child_{i + 1}"
        people[child_name] = {
            "age": {year: 5 + i},
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
        "axes": [
            [
                {
                    "name": "employment_income",
                    "min": min_income,
                    "max": max_income,
                    "count": count,
                }
            ]
        ],
    }


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
