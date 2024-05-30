from datetime import datetime

import dash_bootstrap_components as dbc
import pandas as pd
from cloudpathlib import S3Path
from dash import dcc, html
from dash.development.base_component import Component

from euros.all_users import create_user_choices
from euros.config import show_users
from euros.flags import FLAG_UNICODE


def lookup_team_owners(team: str, base_path: S3Path) -> dict:
    user_choices: pd.DataFrame = create_user_choices("synteny", base_path)
    user_choices.set_index("team", inplace=True)

    return dict(user_choices.loc[team].items())


def get_day_with_suffix(day: int) -> str:
    if 11 <= day <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix}"


def create_fixtures_tab(fixtures_filter_table: list[dict], fixtures_filter_select: dcc.Dropdown, base_path: S3Path) -> html.Div:

    fixtures_formatted = [
        html.Br(),
        fixtures_filter_select,
    ]

    if not fixtures_filter_table:
        return fixtures_formatted

    fixtures = pd.DataFrame(fixtures_filter_table)

    fixtures["datestamp"] = fixtures["Date"].apply(lambda x: x.split(" ")[0])
    fixtures["timestamp"] = fixtures["Date"].apply(lambda x: x.split(" ")[1])

    # Convert the date column to datetime format
    fixtures["datestamp"] = pd.to_datetime(fixtures["datestamp"], dayfirst=True)

    # Sort the DataFrame by the datetime column
    fixtures = fixtures.sort_values(by="datestamp")

    for date, rows in fixtures.groupby("datestamp").__iter__():
        day_with_suffix = get_day_with_suffix(date.day)
        formatted_date = date.strftime(f"%A {day_with_suffix} %B")

        fixtures_formatted += [
            html.Br(),
            dbc.Row(
                [html.H4(formatted_date)],
                style={"text-align": "center"},
            ),
        ]

        rows = rows.sort_values(by="timestamp")

        for num, row in rows.iterrows():
            matchday = row.loc["Group"] if row.loc["Group"] != "" else row.loc["Round Number"]

            home_team = row.loc["Home Team"] + " " + FLAG_UNICODE.get(row.loc["Home Team"], "")
            away_team = row.loc["Away Team"] + " " + FLAG_UNICODE.get(row.loc["Away Team"], "")

            if show_users(cutoff_time=datetime(2024, 6, 10, 18, 53)):

                home_tokens = (
                    ", ".join(
                        [f"""{k} ({v})""" for k, v in lookup_team_owners(row.loc["Home Team"], base_path).items() if v > 0 and k != "total"]
                    )
                    if row.loc["Home Team"] in FLAG_UNICODE.keys()
                    else ""
                )
                away_tokens = (
                    ", ".join(
                        [f"""{k} ({v})""" for k, v in lookup_team_owners(row.loc["Away Team"], base_path).items() if v > 0 and k != "total"]
                    )
                    if row.loc["Away Team"] in FLAG_UNICODE.keys()
                    else ""
                )

                fixtures_formatted += [
                    html.Br(),
                    dbc.Row(
                        [
                            dbc.Col(home_tokens, style={"text-align": "left"}, width=2),  # TODO
                            dbc.Col(
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            f"""Match {row["Match Number"]}, {matchday}, {row["Location"]}""",
                                            style={"text-align": "center"},
                                            width=12,
                                        ),
                                        dbc.Col(html.H3(home_team), style={"text-align": "right"}, width=5),
                                        dbc.Col(
                                            [html.H4(row.loc["timestamp"] if row["Result"] == "" else row["Result"])],
                                            style={"text-align": "center"},
                                            width=2,
                                        ),
                                        dbc.Col(html.H3(away_team), style={"text-align": "left"}, width=5),
                                    ]
                                ),
                                width=8,
                            ),
                            dbc.Col(away_tokens, style={"text-align": "right"}, width=2),
                        ],
                        align="center",
                        style={"minHeight": "150px"},
                    ),
                ]

            else:

                fixtures_formatted += [
                    html.Br(),
                    dbc.Row(
                        [
                            dbc.Col([], style={"text-align": "left"}, width=2),  # TODO
                            dbc.Col(
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            f"""Match {row["Match Number"]}, {matchday}, {row["Location"]}""",
                                            style={"text-align": "center"},
                                            width=12,
                                        ),
                                        dbc.Col(html.H3(home_team), style={"text-align": "right"}, width=5),
                                        dbc.Col(
                                            [html.H4(row.loc["timestamp"] if row["Result"] == "" else row["Result"])],
                                            style={"text-align": "center"},
                                            width=2,
                                        ),
                                        dbc.Col(html.H3(away_team), style={"text-align": "left"}, width=5),
                                    ]
                                ),
                                width=8,
                            ),
                            dbc.Col([], style={"text-align": "right"}, width=2),
                        ],
                        align="center",
                        style={"minHeight": "150px"},
                    ),
                ]

    return html.Div(
        children=fixtures_formatted,
    )
