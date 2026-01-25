"""Dynamic chart generation functions using PolicyEngine microsimulation.

These charts use live microsimulation data for South Carolina H.3492 analysis.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..household import calculate_net_income_by_earnings

# PolicyEngine app-v2 color palette
BLACK = "#000000"
PRIMARY_500 = "#319795"  # Main teal brand color
PRIMARY_700 = "#285E61"  # Dark teal for gains >5%
PRIMARY_ALPHA_60 = "rgba(49, 151, 149, 0.6)"  # Teal with 60% opacity
GRAY_200 = "#E5E7EB"  # No change
GRAY_400 = "#9CA3AF"  # Loss <5%
GRAY_600 = "#4B5563"  # Loss >5%

# Chart watermark configuration
WATERMARK_CONFIG = {
    "source": "https://policyengine.github.io/sc-h3492-eitc-calc/teal-square-transparent.png",
    "xref": "paper",
    "yref": "paper",
    "sizex": 0.07,
    "sizey": 0.07,
    "xanchor": "right",
    "yanchor": "bottom",
}


def create_dynamic_winners_by_decile_chart(microsim_data: dict) -> go.Figure:
    """
    Create Winners/Losers by decile chart using microsimulation data.

    Args:
        microsim_data: Dictionary from calculate_decile_impacts() containing
            decile_outcomes and all_outcomes

    Returns:
        Plotly figure object
    """
    decile_outcomes = microsim_data["decile_outcomes"]
    all_outcomes = microsim_data["all_outcomes"]

    labels_deciles = [str(i) for i in range(1, 11)]

    df_deciles = pd.DataFrame(
        {
            "Income decile": labels_deciles,
            "Gain more than 5%": decile_outcomes["gain_more_than_5pct"],
            "Gain less than 5%": decile_outcomes["gain_less_than_5pct"],
            "No change": decile_outcomes["no_change"],
            "Lose less than 5%": decile_outcomes["loss_less_than_5pct"],
            "Lose more than 5%": decile_outcomes["loss_more_than_5pct"],
        }
    )

    df_all = pd.DataFrame(
        {
            "Income decile": ["All"],
            "Gain more than 5%": [all_outcomes["gain_more_than_5pct"]],
            "Gain less than 5%": [all_outcomes["gain_less_than_5pct"]],
            "No change": [all_outcomes["no_change"]],
            "Lose less than 5%": [all_outcomes["loss_less_than_5pct"]],
            "Lose more than 5%": [all_outcomes["loss_more_than_5pct"]],
        }
    )

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.1, 0.9],
    )

    # Colors
    COLOR_GAIN_MORE = PRIMARY_700
    COLOR_GAIN_LESS = PRIMARY_ALPHA_60
    COLOR_NO_CHANGE = GRAY_200
    COLOR_LOSS_LESS = GRAY_400
    COLOR_LOSS_MORE = GRAY_600

    # Add traces for "All" category - first row
    _add_stacked_bar_traces(
        fig,
        df_all,
        COLOR_GAIN_MORE,
        COLOR_GAIN_LESS,
        COLOR_NO_CHANGE,
        COLOR_LOSS_LESS,
        COLOR_LOSS_MORE,
        row=1,
        show_legend=True,
    )

    # Add traces for deciles - second row
    _add_stacked_bar_traces(
        fig,
        df_deciles,
        COLOR_GAIN_MORE,
        COLOR_GAIN_LESS,
        COLOR_NO_CHANGE,
        COLOR_LOSS_LESS,
        COLOR_LOSS_MORE,
        row=2,
        show_legend=False,
    )

    fig.update_layout(
        barmode="stack",
        title=dict(
            text="Winners of SC H.3492 partially refundable EITC by income decile",
            x=0,
        ),
        font=dict(family="Roboto Serif"),
        xaxis=dict(
            title=dict(text=""),
            ticksuffix="%",
            range=[0, 100],
            showgrid=False,
            showticklabels=False,
            fixedrange=True,
        ),
        xaxis2=dict(
            title=dict(text="Population share"),
            ticksuffix="%",
            range=[0, 100],
            fixedrange=True,
        ),
        yaxis=dict(
            title=dict(text=""),
            tickvals=["All"],
        ),
        yaxis2=dict(
            title=dict(text="Income decile"),
            automargin=True,
        ),
        legend=dict(
            title=dict(text=""),
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="center",
            x=0.5,
            traceorder="normal",
            font=dict(size=10),
        ),
        font_color=BLACK,
        margin={"l": 60, "r": 60, "b": 100, "t": 120, "pad": 4},
        height=580,
        width=800,
        uniformtext=dict(
            mode="hide",
            minsize=8,
        ),
        images=[
            {
                **WATERMARK_CONFIG,
                "sizex": 0.09,
                "sizey": 0.09,
                "x": 1.05,
                "y": -0.20,
            }
        ],
    )

    return fig


def _add_stacked_bar_traces(
    fig: go.Figure,
    df: pd.DataFrame,
    color_gain_more: str,
    color_gain_less: str,
    color_no_change: str,
    color_loss_less: str,
    color_loss_more: str,
    row: int,
    show_legend: bool,
) -> None:
    """Add stacked bar traces to a figure."""
    categories = [
        ("Gain more than 5%", "Gain >5%", color_gain_more, None),
        ("Gain less than 5%", "Gain <5%", color_gain_less, BLACK),
        ("No change", "No change", color_no_change, BLACK),
        ("Lose less than 5%", "Loss <5%", color_loss_less, None),
        ("Lose more than 5%", "Loss >5%", color_loss_more, None),
    ]

    for col_name, legend_name, color, text_color in categories:
        text_kwargs = {}
        if text_color:
            text_kwargs["textfont"] = dict(color=text_color)

        fig.add_trace(
            go.Bar(
                y=df["Income decile"],
                x=df[col_name],
                name=legend_name,
                orientation="h",
                marker_color=color,
                text=[f"{x:.0f}%" if x > 0 else "" for x in df[col_name]],
                textposition="inside",
                textangle=0,
                legendgroup=col_name.lower().replace(" ", "_"),
                showlegend=show_legend,
                hovertemplate="%{x:.1f}%<extra></extra>",
                **text_kwargs,
            ),
            row=row,
            col=1,
        )


def create_dynamic_avg_benefit_by_decile_chart(microsim_data: dict) -> go.Figure:
    """
    Create average benefit by decile chart using microsimulation data.

    Args:
        microsim_data: Dictionary from calculate_decile_impacts() containing
            avg_impact_by_decile

    Returns:
        Plotly figure object
    """
    avg_impact = microsim_data["avg_impact_by_decile"]

    df = pd.DataFrame(
        {
            "Income decile": list(range(1, 11)),
            "Average impact": avg_impact,
        }
    )

    dollar_text = [f"${int(x)}" for x in avg_impact]

    fig = (
        px.bar(
            df,
            x="Income decile",
            y="Average impact",
            text=dollar_text,
            color_discrete_sequence=[PRIMARY_500],
            title="Average benefit of SC H.3492 partially refundable EITC by income decile",
        )
        .update_layout(
            font=dict(family="Roboto Serif"),
            xaxis=dict(
                title=dict(text="Income decile"),
                tickvals=list(range(1, 11)),
                fixedrange=True,
            ),
            yaxis=dict(
                title=dict(text="Absolute change in household income"),
                tickformat=",",
                tickprefix="$",
                fixedrange=True,
            ),
            showlegend=False,
            font_color=BLACK,
            margin={"l": 60, "r": 60, "b": 80, "t": 80, "pad": 4},
            images=[
                {
                    **WATERMARK_CONFIG,
                    "x": 1.05,
                    "y": -0.18,
                }
            ],
        )
        .update_traces(
            hovertemplate="Income decile: %{x}<br>Average impact: $%{y:,.0f}<extra></extra>"
        )
    )

    return fig


def create_dynamic_net_income_change_chart(
    num_children: int = 1,
    max_income: int = 200000,
    step: int = 1000,
) -> go.Figure:
    """
    Create net income change chart using actual PolicyEngine calculations.

    Shows the change in net income for a single parent with one child
    in South Carolina under H.3492.

    Args:
        num_children: Number of children in household
        max_income: Maximum employment income to show
        step: Income step size

    Returns:
        Plotly figure object
    """
    print(f"Calculating net income for SC household with {num_children} child(ren)...")

    # Get actual PolicyEngine calculations
    employment_incomes, baseline_net, reform_net = calculate_net_income_by_earnings(
        state="SC",
        num_children=num_children,
        min_income=0,
        max_income=max_income,
        step=step,
    )

    # Calculate the change
    net_income_changes = [r - b for r, b in zip(reform_net, baseline_net)]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=employment_incomes,
            y=net_income_changes,
            name="Change in net income",
            mode="lines",
            line=dict(color=PRIMARY_500, width=3),
            fill="tozeroy",
            fillcolor=PRIMARY_ALPHA_60,
            hovertemplate=(
                "Employment income: $%{x:,}<br>"
                "Change in net income: $%{y:,.2f}<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title=f"Change in net income from SC H.3492 (single parent, {num_children} child{'ren' if num_children > 1 else ''})",
        font=dict(family="Roboto Serif", color=BLACK),
        xaxis=dict(
            title=dict(text="Employment income"),
            tickformat=",",
            tickprefix="$",
            fixedrange=True,
        ),
        yaxis=dict(
            title=dict(text="Change in net income"),
            tickformat=",",
            tickprefix="$",
            fixedrange=True,
        ),
        showlegend=False,
        font_color=BLACK,
        margin={"l": 60, "r": 60, "b": 80, "t": 80, "pad": 4},
        images=[
            {
                **WATERMARK_CONFIG,
                "x": 1.05,
                "y": -0.18,
            }
        ],
    )

    return fig
