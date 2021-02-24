import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc, html


def lookup_team_owners(team: str, user_choices: pd.DataFrame) -> str:
    """Lookup the users who have tokens for a given team."""
    user_tokens: list[str] = (
        user_choices[(user_choices["team"] == team) & (user_choices["tokens"] > 0)]
        .apply(lambda row: f"""{row["user"]} ({row["tokens"]})""", axis=1)
        .tolist()
    )
    return ", ".join(user_tokens)


def get_day_with_suffix(day: int) -> str:
    """Get the day with the correct suffix."""
    if 11 <= day <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix}"


def create_fixtures_tab(
    fixtures_filtered: pd.DataFrame,
    fixtures_filter_select: dcc.Dropdown,
    user_choices: pd.DataFrame,
    show_users: bool,
) -> dbc.Col:
    """Create the fixtures tab frontend."""
    fixtures_formatted = [
        html.Br(),
        fixtures_filter_select,
    ]

    if fixtures_filtered.empty:
        return fixtures_formatted

    fixtures_filtered["datestamp"] = pd.to_datetime(fixtures_filtered["datestamp"])
    fixtures_filtered = fixtures_filtered.sort_values(by="datestamp")

    for date, rows in fixtures_filtered.groupby("datestamp").__iter__():
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

        for _, row in rows.iterrows():
            matchday = (
                row.loc["Group"] if row.loc["Group"] != "" else row.loc["Round Number"]
            )

            home_team, away_team = row.loc["Home Team"], row.loc["Away Team"]

            home_team_short, away_team_short = (
                row.loc["Home Team Short"],
                row.loc["Away Team Short"],
            )

            home_team_long, away_team_long = (
                row.loc["Home Team Long"],
                row.loc["Away Team Long"],
            )

            if show_users:
                home_tokens = [lookup_team_owners(home_team, user_choices)]
                away_tokens = [lookup_team_owners(away_team, user_choices)]
            else:
                home_tokens = []
                away_tokens = []

            fixtures_formatted += [
                html.Br(),
                dbc.Row(
                    [
                        dbc.Col(
                            home_tokens,
                            style={"text-align": "left"},
                            width=2,
                            class_name="secondaryText",
                        ),  # TODO
                        dbc.Col(
                            dbc.Row(
                                [
                                    dbc.Col(
                                        " ".join(
                                            [
                                                f"""Match {row["Match Number"]}""",
                                                matchday,
                                                row["Location"],
                                            ]
                                        ),
                                        style={
                                            "text-align": "center",
                                        },
                                        width=12,
                                        class_name="secondaryText",
                                    ),
                                    dbc.Col(
                                        html.H5(
                                            home_team_short, className="headerLarge"
                                        ),
                                        style={"text-align": "right"},
                                        width=4,
                                        class_name="shortTeam",
                                    ),
                                    dbc.Col(
                                        html.H5(
                                            home_team_long, className="headerLarge"
                                        ),
                                        style={"text-align": "right"},
                                        width=4,
                                        class_name="longTeam",
                                    ),
                                    dbc.Col(
                                        [
                                            html.H5(
                                                row.loc["timestamp"]
                                                if row["Result"] == ""
                                                else row["Result"],
                                                className="primaryText",
                                            )
                                        ],
                                        style={"text-align": "center"},
                                        width=4,
                                    ),
                                    dbc.Col(
                                        html.H5(
                                            away_team_short, className="headerLarge"
                                        ),
                                        style={"text-align": "left"},
                                        width=4,
                                        class_name="shortTeam",
                                    ),
                                    dbc.Col(
                                        html.H5(
                                            away_team_long, className="headerLarge"
                                        ),
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

    return [
        dbc.Col(
            children=fixtures_formatted,
        )
    ]
