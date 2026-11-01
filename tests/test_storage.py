from typestriker import storage


def fill(count, start=1000):
    for i in range(count):
        storage.add_score(f"P{i}", start + i * 100, 1, 20, 90)


def test_scores_sorted_and_capped_at_ten():
    fill(14)
    scores = storage.load_scores()
    assert len(scores) == 10
    assert [r["score"] for r in scores] == sorted((r["score"] for r in scores), reverse=True)


def test_qualifies():
    assert not storage.qualifies(0)
    assert storage.qualifies(100)
    fill(10, 1000)
    assert not storage.qualifies(1000)
    assert not storage.qualifies(500)
    assert storage.qualifies(1001)


def test_name_is_limited_to_ten_characters():
    storage.add_score("ABCDEFGHIJKLMNOP", 500, 1, 10, 90)
    assert storage.load_scores()[0]["name"] == "ABCDEFGHIJ"


def test_add_score_reports_rank():
    fill(3, 1000)
    assert storage.add_score("TOP", 5000, 2, 10, 90) == 0
    assert storage.add_score("LOW", 1, 2, 10, 90) == 4


def test_progress_records_per_level_and_keeps_bests():
    assert storage.record_level(2, 20.0, 90.0, True) == {"wpm": False, "accuracy": False}
    assert storage.record_level(2, 30.0, 85.0, False) == {"wpm": True, "accuracy": False}
    row = storage.load_progress()["2"]
    assert row["plays"] == 2 and row["clears"] == 1
    assert row["best_wpm"] == 30.0 and row["best_accuracy"] == 90.0
    assert row["last_wpm"] == 30.0 and row["last_accuracy"] == 85.0
    assert len(row["history"]) == 2


def test_history_is_bounded():
    for i in range(storage.HISTORY_LENGTH + 10):
        storage.record_level(1, i, 90, True)
    assert len(storage.load_progress()["1"]["history"]) == storage.HISTORY_LENGTH


def test_damaged_files_do_not_stop_the_game(data_folder):
    (data_folder / "scores.json").write_text("{ not json")
    (data_folder / "progress.json").write_text("[1,2,3]")
    (data_folder / "settings.json").write_text('"oops"')
    assert storage.load_scores() == []
    assert storage.load_progress() == {}
    assert storage.load_settings()["sound"] == storage.DEFAULT_SETTINGS["sound"]
    assert (data_folder / "scores.json.corrupt").exists()


def test_bad_rows_are_skipped(data_folder):
    (data_folder / "scores.json").write_text('[{"name":"OK","score":5},{"name":"bad"},7]')
    assert [r["name"] for r in storage.load_scores()] == ["OK"]
