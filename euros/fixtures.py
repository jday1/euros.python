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


def create_fixtures_large(
    fixtures_filter_table: list[dict],
    fixtures_filter_select: dcc.Dropdown,
    base_path: S3Path,
    show_users: Callable,
    group: str,
    fixtures_id: str,
    header_small: Callable = html.H4,
    header_large: Callable = html.H3,
    font_size: int = 14,
    shorten_countries: bool = False,
):

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

    user_choices = create_user_choices(group, base_path)

    for date, rows in fixtures.groupby("datestamp").__iter__():
        day_with_suffix = get_day_with_suffix(date.day)
        formatted_date = date.strftime(f"%A {day_with_suffix} %B")

        fixtures_formatted += [
            html.Br(),
            dbc.Row(
                [header_small(formatted_date)],
                style={"text-align": "center"},
            ),
        ]

        rows = rows.sort_values(by="timestamp")

        for num, row in rows.iterrows():
            matchday = row.loc["Group"] if row.loc["Group"] != "" else row.loc["Round Number"]

            home_team, away_team = row.loc["Home Team"], row.loc["Away Team"]

            if shorten_countries:
                if "Winner Match" in home_team:
                    home_team = home_team.replace("Winner Match", "MW")
                elif FLAG_UNICODE.get(home_team) is not None:
                    home_team = home_team[:3] + " " + FLAG_UNICODE.get(home_team, "")
                else:
                    home_team = home_team

                if "Winner Match" in away_team:
                    away_team = away_team.replace("Winner Match", "MW")
                elif FLAG_UNICODE.get(away_team) is not None:
                    away_team = away_team[:3] + " " + FLAG_UNICODE.get(away_team, "")
                else:
                    away_team = away_team
            else:
                if FLAG_UNICODE.get(home_team) is not None:
                    home_team = home_team + " " + FLAG_UNICODE.get(home_team, "")
                if FLAG_UNICODE.get(away_team) is not None:
                    away_team = away_team + " " + FLAG_UNICODE.get(away_team, "")

            if show_users():

                home_tokens = (
                    ", ".join(
                        [
                            f"""{k} ({v})"""
                            for k, v in lookup_team_owners(row.loc["Home Team"], user_choices).items()
                            if v > 0 and k != "total"
                        ]
                    )
                    if row.loc["Home Team"] in FLAG_UNICODE.keys()
                    else ""
                )
                away_tokens = (
                    ", ".join(
                        [
                            f"""{k} ({v})"""
                            for k, v in lookup_team_owners(row.loc["Away Team"], user_choices).items()
                            if v > 0 and k != "total"
                        ]
                    )
                    if row.loc["Away Team"] in FLAG_UNICODE.keys()
                    else ""
                )

                fixtures_formatted += [
                    html.Br(),
                    dbc.Row(
                        [
                            dbc.Col(home_tokens, style={"text-align": "left", "fontSize": font_size}, width=2),  # TODO
                            dbc.Col(
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            f"""Match {row["Match Number"]}, {matchday}, {row["Location"]}""",
                                            style={"text-align": "center", "fontSize": font_size},
                                            width=12,
                                        ),
                                        dbc.Col(header_large(home_team), style={"text-align": "right"}, width=4),
                                        dbc.Col(
                                            [header_small(row.loc["timestamp"] if row["Result"] == "" else row["Result"])],
                                            style={"text-align": "center"},
                                            width=4,
                                        ),
                                        dbc.Col(header_large(away_team), style={"text-align": "left"}, width=4),
                                    ]
                                ),
                                width=8,
                            ),
                            dbc.Col(away_tokens, style={"text-align": "right", "fontSize": font_size}, width=2),
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
                                            style={"text-align": "center", "fontSize": font_size},
                                            width=12,
                                        ),
                                        dbc.Col(header_large(home_team), style={"text-align": "right"}, width=5),
                                        dbc.Col(
                                            [header_small(row.loc["timestamp"] if row["Result"] == "" else row["Result"])],
                                            style={"text-align": "center"},
                                            width=2,
                                        ),
                                        dbc.Col(header_large(away_team), style={"text-align": "left"}, width=5),
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

    return dbc.Col(
        children=fixtures_formatted,
        className=fixtures_id,
    )


def create_fixtures_tab(
    fixtures_filter_table: list[dict], fixtures_filter_select: dcc.Dropdown, base_path: S3Path, show_users: Callable, group: str
) -> html.Div:

    return [
        create_fixtures_large(
            fixtures_filter_table,
            fixtures_filter_select,
            base_path,
            show_users,
            group,
            fixtures_id="small-fixtures",
            font_size=8,
            header_small=html.H6,
            header_large=html.H6,
            shorten_countries=True,
        ),
        create_fixtures_large(
            fixtures_filter_table,
            fixtures_filter_select,
            base_path,
            show_users,
            group,
            fixtures_id="large-fixtures",
        ),
    ]
