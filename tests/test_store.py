import json
from jarvis import store


def test_save_and_load(mock_data_dir):
    data = [{"title": "Buy groceries", "done": False}]
    store.save("todos", data)

    loaded = store.load("todos", default=[])
    assert loaded == data


def test_load_nonexistent_returns_default(mock_data_dir):
    loaded = store.load("non_existent_file", default=["fallback"])
    assert loaded == ["fallback"]


def test_corrupted_json_recovery(mock_data_dir):
    # Write intentionally invalid JSON
    bad_file = mock_data_dir / "notes.json"
    bad_file.write_text("{ unclosed json: ", encoding="utf-8")

    loaded = store.load("notes", default=[])
    assert loaded == []

    # Verify corrupt file was moved to .bad backup
    assert not bad_file.exists()
    assert (mock_data_dir / "notes.bad").exists()