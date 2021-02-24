import datetime
from pathlib import Path

from euros.main import create_loader


def test_create_loader():
    """Simple test illustrating how the config loads."""
    filepath = Path(__file__).parent / "resources" / "test_config.yaml"

    load = create_loader(filepath)

    assert load.choices_path("james").exists()
    assert load.load_fixtures()
    assert len(load.load_users()) == 7
    assert not load.create_user_choices().empty

    assert load.model_dump() == {
        "app_name": "Euros",
        "user_group": "example_group",
        "port": 3000,
        "base_path": Path("./euros/tests/resources/example_base_path"),
        "cutoff_time": datetime.datetime(2024, 6, 14, 12, 0, tzinfo=datetime.UTC),
        "debug": False,
        "host": "0.0.0.0",
        "suppress_callback_exceptions": False,
    }
