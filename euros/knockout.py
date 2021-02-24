from collections.abc import Callable
from datetime import datetime

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html

from euros.fixtures import get_day_with_suffix


def _add_team_info(
    x_position: float, y_position: float, labels: list[str], color: str, font_size: int
):
    return go.Scatter(
        x=[x_position, x_position],
        y=[y_position - 0.1, y_position + 0.1],
        mode="text",
        text=labels,
        textfont=dict(size=font_size, family="monospace"),
        textfont_color=color,
        showlegend=False,
        hoverinfo="none",
    )


def _add_match_info(
    x_position: float, y_position: float, match_label: str, font_size: int, color
):
    return go.Scatter(
        x=[x_position - 0.7],
        y=[y_position + 0.3],
        mode="text",
        text=[match_label],
        textfont=dict(size=font_size, family="monospace"),
        textfont_color=color,
        showlegend=False,
        hoverinfo="none",
        textposition="middle right",  # Align text to the left
    )


def _add_date_info(
    x_position: list[float],
    y_position: list[float],
    date_string: list[str],
    color: str,
    text_size: int,
):
    return go.Scatter(
        x=x_position,
        y=y_position,
        mode="text",
        text=date_string,
        textfont=dict(size=text_size, family="monospace"),
        textfont_color=color,
        showlegend=False,
        hoverinfo="none",
        textposition="middle right",  # Align text to the left
    )


def _add_legend(fig: go.Figure) -> None:
    for color, name in [
        ("blue", "Round of 16"),
        ("red", "Quarter Finals"),
        ("green", "Semi-Finals"),
        ("gold", "Final"),
    ]:
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="lines",
                line=dict(color=color),
                name=name,
                showlegend=True,
            )
        )


def _update_fig_layout(fig: go.Figure) -> None:
    fig.update_layout(
        xaxis=dict(showticklabels=False, range=[-0.5, 6.3], autorange=False),
        yaxis=dict(showticklabels=False, autorange=True),
        height=1000,
        plot_bgcolor="white",
        legend=dict(
            title="",
            itemsizing="constant",
            orientation="h",
        ),
    )


def _add_surrounding_box(
    add: bool, fig: go.Figure, x_position: float, y_position: float, color: str
):
    if add:
        x_adj = 0.7
        y_adj = 0.2

        fig.add_trace(
            go.Scatter(
                x=[
                    x_position - x_adj,
                    x_position + x_adj,
                    x_position + x_adj,
                    x_position - x_adj,
                    x_position - x_adj,
                ],
                y=[
                    y_position - y_adj,
                    y_position - y_adj,
                    y_position + y_adj,
                    y_position + y_adj,
                    y_position - y_adj,
                ],
                mode="lines",
                showlegend=False,
                line=dict(color=color),
                hoverinfo="none",
            )
        )


def _create_base_positions(
    ko_fixtures: pd.DataFrame,
    base_x_position: float,
    x_distance: float,
    base_y_position: float,
    y_distance: float,
) -> pd.DataFrame:
    ko_fixtures.loc[:, ["x_position", "y_position"]] = [
        (base_x_position, base_y_position + y_distance * 4),
        (base_x_position + x_distance * 3, base_y_position),
        (base_x_position, base_y_position + y_distance * 6),
        (base_x_position + x_distance * 3, base_y_position + y_distance * 2),
        (base_x_position, base_y_position + y_distance * 2),
        (base_x_position, base_y_position),
        (base_x_position + x_distance * 3, base_y_position + y_distance * 6),
        (base_x_position + x_distance * 3, base_y_position + y_distance * 4),
        (base_x_position + x_distance * 0.5, base_y_position + y_distance * 5),
        (base_x_position + x_distance * 0.5, base_y_position + y_distance * 1),
        (base_x_position + x_distance * 2.5, base_y_position + y_distance * 5),
        (base_x_position + x_distance * 2.5, base_y_position + y_distance * 1),
        (base_x_position + x_distance * 1, base_y_position + y_distance * 3),
        (base_x_position + x_distance * 2, base_y_position + y_distance * 3),
        (base_x_position + x_distance * 1.5, base_y_position + y_distance * 1),
    ]

    return ko_fixtures


def large_date_formatter(row: pd.Series) -> list[str]:
    """Format the date for the large knockout stage figure."""
    date_string = f"""{row["Date"]}"""
    date_obj = datetime.strptime(date_string, "%d/%m/%Y %H:%M")
    day_with_suffix = get_day_with_suffix(date_obj.day)
    formatted_date_with_suffix = date_obj.strftime(
        f"%A {day_with_suffix} %B %H:%M"  # noqa: E231
    )

    return [formatted_date_with_suffix]


def create_knockout_fig(
    ko_fixtures: pd.DataFrame,
    labels_formatter: Callable,
    team_text_size: int,
    team_text_color: str | None,
    match_text_size: int,
    match_text_formatter: Callable,
    date_x_position: Callable,
    date_y_position: Callable,
    date_formatter: Callable,
    date_text_size: int,
    add_surrounding_box: bool,
) -> go.Figure:
    """Create the knockout stage figure."""
    fig = go.Figure()

    base_x_position, x_distance, base_y_position, y_distance = 0.5, 1.6, 0.2, 0.8

    ko_fixtures = _create_base_positions(
        ko_fixtures, base_x_position, x_distance, base_y_position, y_distance
    )

    for _, row in ko_fixtures.iterrows():
        x_position, y_position = row["x_position"], row["y_position"]
        labels = labels_formatter(row)
        color = row["color"]

        entry_text_color = color if team_text_color is None else team_text_color

        fig.add_trace(
            _add_team_info(
                x_position, y_position, labels, entry_text_color, team_text_size
            )
        )

        fig.add_trace(
            _add_match_info(
                x_position,
                y_position,
                match_text_formatter(row),
                match_text_size,
                color=entry_text_color,
            )
        )

        fig.add_trace(
            _add_date_info(
                date_x_position(x_position),
                date_y_position(y_position),
                date_formatter(row),
                entry_text_color,
                date_text_size,
            )
        )

        _add_surrounding_box(
            add=add_surrounding_box,
            fig=fig,
            x_position=x_position,
            y_position=y_position,
            color=color,
        )

    _add_legend(fig)

    _update_fig_layout(fig)

    return fig


def create_knockout_tab(fixtures: pd.DataFrame) -> html.Div:
    """Create the knockout tab frontend."""
    ko_fixtures = fixtures[
        ~fixtures["Round Number"].isin(
            [
                "1",
                "2",
                "3",
            ]
        )
    ]

    ko_fixtures.loc[:, ["color"]] = ko_fixtures["Round Number"].apply(
        lambda x: "blue"
        if x == "Round of 16"
        else "red"
        if x == "Quarter Finals"
        else "green"
        if x == "Semi Finals"
        else "gold"
    )

    small_fig = create_knockout_fig(
        ko_fixtures,
        lambda row: [row["Away Team Short"], row["Home Team Short"]],
        team_text_size=10,
        team_text_color=None,
        match_text_size=6,
        match_text_formatter=lambda row: f"""Match {row["Match Number"]}""",
        date_x_position=lambda x_position: [x_position - 0.7, x_position - 0.7],
        date_y_position=lambda y_position: [y_position - 0.3, y_position - 0.4],
        date_formatter=lambda row: row["Date"].split(" "),
        date_text_size=6,
        add_surrounding_box=False,
    )
    medium_fig = create_knockout_fig(
        ko_fixtures,
        lambda row: [row["Away Team Short"], row["Home Team Short"]],
        18,
        "black",
        10,
        lambda row: f"""Match {row["Match Number"]}""",
        lambda x_position: [x_position - 0.7],
        lambda y_position: [y_position - 0.3],
        lambda row: [row["Date"]],
        10,
        True,
    )
    large_fig = create_knockout_fig(
        ko_fixtures,
        lambda row: [row["Away Team Long"], row["Home Team Long"]],
        18,
        "black",
        10,
        lambda row: f"""Match {row["Match Number"]} - {row["Location"]}""",
        lambda x_position: [x_position - 0.7],
        lambda y_position: [y_position - 0.3],
        large_date_formatter,
        10,
        True,
    )

    return [
        dbc.Col(
            html.Div(
                dcc.Graph(
                    figure=small_fig,
                    style={"width": "100%", "minWidth": "400px"},
                    config={"staticPlot": True},
                ),
                style={"overflowX": "auto"},
            ),
            width=12,
            className="small-knockout",
        ),
        dbc.Col(
            dcc.Graph(
                figure=medium_fig,
                style={"width": "100%"},
            ),
            width=12,
            className="medium-knockout",
        ),
        dbc.Col(
            dcc.Graph(
                figure=large_fig,
                style={"width": "100%"},
            ),
            width=12,
            className="large-knockout",
        ),
    ]
