from typing import Callable

import dash_bootstrap_components as dbc
import pandas as pd
from cloudpathlib import S3Path
from dash import dcc, html

from euros.all_users import create_user_choices
from euros.flags import FLAG_UNICODE


def lookup_team_owners(team: str, user_choices: pd.DataFrame) -> dict:
    df = user_choices.set_index("team")
    return dict(df.loc[team].items())


def get_day_with_suffix(day: int) -> str:
    if 11 <= day <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix}"


def create_fixtures(
    fixtures_filter_table: list[dict],
    fixtures_filter_select: dcc.Dropdown,
    filter_fixtures_button: dbc.Button,
    fixtures: pd.DataFrame,
    user_choices: pd.DataFrame,
    show_users: Callable,
    fixtures_id: str,
):

    fixtures_formatted = [
        html.Br(),
        fixtures_filter_select,
    ]

    fixtures_formatted += [
        dbc.Row(
            dbc.Col(
                [
                    html.Br(),
                    filter_fixtures_button,
                    html.Br(),
                ],
                width=3,
            ),
            class_name="fixturesFilterButtonRow",
        ),
    ]

    if not fixtures_filter_table:
        return fixtures_formatted

    for date, rows in fixtures.groupby("datestamp").__iter__():
        day_with_suffix = get_day_with_suffix(date.day)
        formatted_date = date.strftime(f"%A {day_with_suffix} %B")

        fixtures_formatted += [
            html.Br(),
            dbc.Row(
                [html.H5(formatted_date, className="primaryText")],
                style={"text-align": "center"},
            ),
        ]

        rows = rows.sort_values(by="timestamp")

        for num, row in rows.iterrows():
            matchday = row.loc["Group"] if row.loc["Group"] != "" else row.loc["Round Number"]

            home_team, away_team = row.loc["Home Team"], row.loc["Away Team"]

            if "Winner Match" in home_team:
                home_team_short = home_team.replace("Winner Match", "MW")
            elif FLAG_UNICODE.get(home_team) is not None:
                home_team_short = [home_team[:3], FLAG_UNICODE.get(home_team, "")]
            else:
                home_team_short = home_team

            if "Winner Match" in away_team:
                away_team_short = away_team.replace("Winner Match", "MW")
            elif FLAG_UNICODE.get(away_team) is not None:
                away_team_short = [away_team[:3], FLAG_UNICODE.get(away_team, "")]
            else:
                away_team_short = away_team

            if FLAG_UNICODE.get(home_team) is not None:
                home_team_long = home_team + " " + FLAG_UNICODE.get(home_team, "")
            else:
                home_team_long = home_team
            if FLAG_UNICODE.get(away_team) is not None:
                away_team_long = away_team + " " + FLAG_UNICODE.get(away_team, "")
            else:
                away_team_long = away_team

            if show_users():

                home_tokens = (
                    ", ".join([f"""{k} ({v})""" for k, v in lookup_team_owners(home_team, user_choices).items() if v > 0 and k != "total"])
                    if home_team in FLAG_UNICODE.keys()
                    else ""
                )
                away_tokens = (
                    ", ".join([f"""{k} ({v})""" for k, v in lookup_team_owners(away_team, user_choices).items() if v > 0 and k != "total"])
                    if away_team in FLAG_UNICODE.keys()
                    else ""
                )

                fixtures_formatted += [
                    html.Br(),
                    dbc.Row(
                        [
                            dbc.Col(home_tokens, style={"text-align": "left"}, width=2, class_name="secondaryText"),  # TODO
                            dbc.Col(
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            f"""Match {row["Match Number"]}, {matchday}, {row["Location"]}""",
                                            style={
                                                "text-align": "center",
                                            },
                                            width=12,
                                            class_name="secondaryText",
                                        ),
                                        dbc.Col(
                                            html.H5(home_team_short, className="headerLarge"),
                                            style={"text-align": "right"},
                                            width=4,
                                            class_name="shortTeam",
                                        ),
                                        dbc.Col(
                                            html.H5(home_team_long, className="headerLarge"),
                                            style={"text-align": "right"},
                                            width=4,
                                            class_name="longTeam",
                                        ),
                                        dbc.Col(
                                            [
                                                html.H5(
                                                    row.loc["timestamp"] if row["Result"] == "" else row["Result"],
                                                    className="primaryText",
                                                )
                                            ],
                                            style={"text-align": "center"},
                                            width=4,
                                        ),
                                        dbc.Col(
                                            html.H5(away_team_short, className="headerLarge"),
                                            style={"text-align": "left"},
                                            width=4,
                                            class_name="shortTeam",
                                        ),
                                        dbc.Col(
                                            html.H5(away_team_long, className="headerLarge"),
                                            style={"text-align": "left"},
                                            width=4,
                                            class_name="longTeam",
                                        ),
                                    ],
                                    align="center",
                                ),
                                width=8,
                            ),
                            dbc.Col(
                                away_tokens,
                                style={
                                    "text-align": "right",
                                },
                                width=2,
                                class_name="secondaryText",
                            ),
                        ],
                        align="center",
                        class_name="fixtureHeight",
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
                                            class_name="secondaryText",
                                        ),
                                        dbc.Col(html.H5(home_team), style={"text-align": "right"}, width=5),
                                        dbc.Col(
                                            [
                                                html.H5(
                                                    row.loc["timestamp"] if row["Result"] == "" else row["Result"],
                                                    className="primaryText",
                                                )
                                            ],
                                            style={"text-align": "center"},
                                            width=2,
                                        ),
                                        dbc.Col(html.H5(away_team), style={"text-align": "left"}, width=5),
                                    ]
                                ),
                                width=8,
                            ),
                            dbc.Col([], style={"text-align": "right"}, width=2),
                        ],
                        align="center",
                        class_name="fixtureHeight",
                    ),
                ]

    return dbc.Col(
        children=fixtures_formatted,
    )


def create_fixtures_tab(
    fixtures_filter_table: list[dict],
    fixtures_filter_select: dcc.Dropdown,
    filter_fixtures_button: dbc.Button,
    user_choices: pd.DataFrame,
    show_users: Callable,
) -> html.Div:

    fixtures = pd.DataFrame(fixtures_filter_table)

    fixtures["datestamp"] = fixtures["Date"].apply(lambda x: x.split(" ")[0])
    fixtures["timestamp"] = fixtures["Date"].apply(lambda x: x.split(" ")[1])

    # Convert the date column to datetime format
    fixtures["datestamp"] = pd.to_datetime(fixtures["datestamp"], dayfirst=True)

    # Sort the DataFrame by the datetime column
    fixtures = fixtures.sort_values(by="datestamp")

    return [
        create_fixtures(
            fixtures_filter_table,
            fixtures_filter_select,
            filter_fixtures_button,
            fixtures,
            user_choices,
            show_users,
            fixtures_id="small-fixtures",
        ),
        # create_fixtures(
        #     fixtures_filter_table,
        #     fixtures_filter_select,
        #     filter_fixtures_button,
        #     fixtures,
        #     user_choices,
        #     show_users,
        #     fixtures_id="large-fixtures",
        # ),
    ]
