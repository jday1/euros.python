import tempfile
from pathlib import Path
from typing import Any

import dash_auth
import dash_bootstrap_components as dbc
import diskcache
import pandas as pd
from cloudpathlib import S3Path
from dash import Dash, DiskcacheManager, Input, Output, State, dcc, html
from flask import request

from euros.all_users import USER_CHOICES_STORE
from euros.config import VALID_USERNAME_PASSWORD_PAIRS
from euros.fixtures import create_fixtures_tab
from euros.flags import FLAG_UNICODE
from euros.groups import create_groups_tab
from euros.knockout import create_knockout_tab
from euros.play import create_play_tab
from euros.standings import create_standings_tab

tmpdir = Path(tempfile.mkdtemp())
cache = diskcache.Cache(tmpdir)
background_callback_manager = DiskcacheManager(cache)
app_name = "euros"
app = Dash(
    name=app_name,
    external_stylesheets=[dbc.themes.LUX],
    background_callback_manager=background_callback_manager,
)


auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS,
    secret_key="kIwjEmZ4fuv09Gwb+5R7IkI2Ftl8JVcA10ExyQ81",
)

app.config.suppress_callback_exceptions = True

# Define the layout
app.layout = dbc.Container(
    [
        dcc.Store(id="username"),
        dcc.Store(id="username-dummy-trigger"),
        html.H2("Euros"),
        dcc.Tabs(
            [
                # create_play_tab(),
                # create_groups_tab(),
                # create_knockout_tab(),
                # create_fixtures_tab(),
                # create_standings_tab(),
                dcc.Tab(label="Play", id="play-tab", value="play-tab"),
                dcc.Tab(label="Groups", id="groups-tab", value="groups-tab"),
                dcc.Tab(label="Knockout", id="knockout-tab", value="knockout-tab"),
                dcc.Tab(label="Fixtures", id="fixtures-tab", value="fixtures-tab"),
                dcc.Tab(label="Standings", id="standings-tab", value="standings-tab"),
            ],
            id="tabs",
            value="play-tab",
        ),
        html.Div(id="tabs-content"),
    ],
    style={"width": "2000px", "margin-top": "50px", "margin-bottom": "50px"},
)


@app.callback(
    Output('tabs-content', 'children'),
    Input('tabs', 'value'),
    Input("username", "data"),
    prevent_initial_call=True,
)
def render_content(tab, username):
    if tab == 'play-tab':
        return create_play_tab(username)
    elif tab == 'groups-tab':
        return create_groups_tab()
    elif tab == 'knockout-tab':
        return create_knockout_tab()
    elif tab == 'fixtures-tab':
        return create_fixtures_tab()
    elif tab == 'standings-tab':
        return create_standings_tab()


@app.callback(
    Output(component_id="username", component_property="data"), 
    Input(component_id="username-dummy-trigger", component_property="data"),
)
def get_username(username_dummy_trigger: Any) -> tuple[str, str]:
    username = request.authorization["username"]
    return username


@app.callback(
    Output(component_id="warning-text", component_property="children",),
    Input(component_id="update-button", component_property="n_clicks"),
    State(component_id="user-choices", component_property="data"),
    State(component_id="username", component_property="data"),
    prevent_initial_call=True,
)
def update_user_choices(n_clicks: int, data: list[dict], username: str) -> dbc.FormText:
    if n_clicks is None:
        return []

    df = pd.DataFrame(data)

    tokens = df["tokens"]

    if (tokens.astype(int) != tokens).all():
        return dbc.FormText("Please enter integers only", color="red")

    if not ((tokens >= 0) & (tokens <= 11)).all():
        return dbc.FormText("Please enter values between 0 and 11", color="red")

    if tokens.sum() != 12:
        return dbc.FormText("Token values must sum to 12", color="red")

    try:
        df["team"] = df["team"].apply(lambda x: " ".join(x.split(" ")[:-1]))

        df.to_csv("choices.csv", index=False)

        (USER_CHOICES_STORE / f"{username}.csv").upload_from("choices.csv")

        return dbc.FormText("Updated selection successfully.", color="blue")
    except Exception as e:
        print(e)
        return dbc.FormText("Something went wrong", color="red")


if __name__ == "__main__":
    app.run(debug=True)
