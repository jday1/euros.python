from datetime import datetime
from cloudpathlib import S3Path
import pandas as pd
import plotly.graph_objects as go
from dash import dcc
from dash import dash_table, dcc, html

from euros.config import load_fixtures
from euros.fixtures import get_day_with_suffix
from euros.flags import FLAG_UNICODE


def create_knockout_fig(base_path: S3Path) -> go.Figure:
    # Create figure
    fig = go.Figure()

    fixtures = load_fixtures(base_path)
    ko_fixtures = fixtures[
        ~fixtures["Round Number"].isin(
            [
                "1",
                "2",
                "3",
            ]
        )
    ]

    ko_fixtures.loc[:, "color"] = ko_fixtures["Round Number"].apply(
        lambda x: "blue" if x == "Round of 16" else "red" if x == "Quarter Finals" else "green" if x == "Semi Finals" else "gold"
    )

    base_x_position = 0.5
    x_distance = 1.6

    base_y_position = 0.2
    y_distance = 0.8

    ko_fixtures.loc[:, "position"] = [
        (base_x_position, base_y_position + y_distance * 4),  # 37
        (base_x_position + x_distance * 3, base_y_position),  # 38
        (base_x_position, base_y_position + y_distance * 6),  # 39
        (base_x_position + x_distance * 3, base_y_position + y_distance * 2),  # 40
        (base_x_position, base_y_position + y_distance * 2),  # 41
        (base_x_position, base_y_position),  # 42
        (base_x_position + x_distance * 3, base_y_position + y_distance * 6),  # 43
        (base_x_position + x_distance * 3, base_y_position + y_distance * 4),  # 44
        (base_x_position + x_distance * 0.5, base_y_position + y_distance * 5),
        (base_x_position + x_distance * 0.5, base_y_position + y_distance * 1),
        (base_x_position + x_distance * 2.5, base_y_position + y_distance * 5),
        (base_x_position + x_distance * 2.5, base_y_position + y_distance * 1),
        (base_x_position + x_distance * 1, base_y_position + y_distance * 3),
        (base_x_position + x_distance * 2, base_y_position + y_distance * 3),
        (base_x_position + x_distance * 1.5, base_y_position + y_distance * 1),
    ]

    for num, row in ko_fixtures.iterrows():

        x_position, y_position = row["position"]
        labels = [row["Away Team"], row["Home Team"]]
        color = row["color"]

        fig.add_trace(
            go.Scatter(
                x=[x_position, x_position],
                y=[y_position - 0.1, y_position + 0.1],
                mode="text",
                text=[f"""{label} {FLAG_UNICODE[label]}""" if FLAG_UNICODE.get(label) is not None else f"{label}" for label in labels],
                textfont=dict(size=18, family="monospace"),
                showlegend=False,
                hoverinfo="none",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[x_position - 0.7],
                y=[y_position + 0.3],
                mode="text",
                text=[f"""Match {row["Match Number"]} - {row["Location"]}"""],
                textfont=dict(size=10, family="monospace"),
                showlegend=False,
                hoverinfo="none",
                textposition="middle right",  # Align text to the left
            )
        )

        date_string = f"""{row["Date"]}"""
        date_obj = datetime.strptime(date_string, "%d/%m/%Y %H:%M")
        # formatted_date = date_obj.strftime("%A %d %B %H:%M")
        day_with_suffix = get_day_with_suffix(date_obj.day)
        formatted_date_with_suffix = date_obj.strftime(f"%A {day_with_suffix} %B %H:%M")

        fig.add_trace(
            go.Scatter(
                x=[x_position - 0.7],
                y=[y_position - 0.3],
                mode="text",
                text=formatted_date_with_suffix,
                textfont=dict(size=10, family="monospace"),
                showlegend=False,
                hoverinfo="none",
                textposition="middle right",  # Align text to the left
            )
        )

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

    for color, name in [("blue", "Round of 16"), ("red", "Quarter Finals"), ("green", "Semi-Finals"), ("gold", "Final")]:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", line=dict(color=color), name=name, showlegend=True))

    fig.update_layout(
        xaxis=dict(showticklabels=False, range=[-0.5, 6.3], autorange=False),
        # yaxis=dict(showticklabels=False, range=[-1.0, 6.2], autorange=False),
        yaxis=dict(showticklabels=False, autorange=True),
        width=1300,
        height=1000,
        plot_bgcolor="white",
        legend=dict(
            title="",
            itemsizing="constant",
            orientation="h",
        ),
    )

    return fig


def create_knockout_tab(base_path: S3Path) -> html.Div:
    return html.Div(
        children=[dcc.Graph(figure=create_knockout_fig(base_path), style={"width": "100%"}, id="knockout-stage-graph")],
    )