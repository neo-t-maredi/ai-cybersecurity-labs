"""Tests for the dataset audit. Each test documents one rule of the file format."""

from pathlib import Path

import pytest

from audit_dataset import (
    AuditError,
    audit,
    count_physical_lines,
    find_failures,
    load_records,
)


def write(tmp_path: Path, data: bytes) -> Path:
    path = tmp_path / "SMSSpamCollection"
    path.write_bytes(data)
    return path


# --- Parsing: one record per physical line ---------------------------------


def test_reads_label_and_message(tmp_path):
    path = write(tmp_path, b"ham\thi\nspam\tWIN now\n")
    assert load_records(path) == [("ham", "hi"), ("spam", "WIN now")]


def test_missing_final_newline_is_accepted(tmp_path):
    path = write(tmp_path, b"ham\thi\nspam\tWIN")
    assert load_records(path) == [("ham", "hi"), ("spam", "WIN")]


def test_crlf_line_endings_are_accepted(tmp_path):
    path = write(tmp_path, b"ham\thi\r\nspam\tWIN\r\n")
    assert load_records(path) == [("ham", "hi"), ("spam", "WIN")]


def test_quotes_are_literal_text(tmp_path):
    path = write(tmp_path, b'ham\t"unclosed quote\nham\tsaid "yes"\n')
    assert load_records(path) == [("ham", '"unclosed quote'), ("ham", 'said "yes"')]


def test_na_like_messages_stay_text(tmp_path):
    path = write(tmp_path, b"ham\tNA\nham\tNULL\nham\tNaN\n")
    assert [text for _, text in load_records(path)] == ["NA", "NULL", "NaN"]


def test_tab_inside_message_belongs_to_message(tmp_path):
    path = write(tmp_path, b"ham\ta\tb\n")
    assert load_records(path) == [("ham", "a\tb")]


def test_lone_carriage_return_stays_inside_message(tmp_path):
    path = write(tmp_path, b"ham\tone\rtwo\nspam\tWIN\n")
    assert load_records(path) == [("ham", "one\rtwo"), ("spam", "WIN")]


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (b"ham\thi\n\nspam\tWIN\n", "Blank line at line 2"),
        (b"ham hi\n", "Missing label separator at line 1"),
        (b"Ham\thi\n", "Invalid label 'Ham' at line 1"),
        (b"ham\t\n", "Empty message at line 1"),
        (b"ham\thi\nham\tcaf\xe9\n", "Invalid UTF-8 at line 2"),
        (b"", "no records"),
    ],
)
def test_malformed_input_fails_with_line_number(tmp_path, data, message):
    with pytest.raises(AuditError, match=message):
        load_records(write(tmp_path, data))


# --- Line counting ----------------------------------------------------------


@pytest.mark.parametrize(
    ("data", "lines"),
    [(b"", 0), (b"a\n", 1), (b"a", 1), (b"a\nb\n", 2), (b"a\nb", 2)],
)
def test_count_physical_lines(tmp_path, data, lines):
    assert count_physical_lines(write(tmp_path, data)) == lines


# --- Duplicate and conflict statistics -------------------------------------

SAMPLE = [
    ("ham", "hi"),
    ("spam", "WIN"),
    ("spam", "WIN"),
    ("spam", "WIN"),
    ("ham", "ok"),
    ("ham", "ok"),
    ("ham", "see you"),
    ("spam", "see you"),
]


def test_duplicate_statistics():
    results = audit(SAMPLE)
    assert results["total"] == 8
    assert results["ham"] == 4
    assert results["spam"] == 4
    assert results["redundant_exact_rows"] == 3  # 2 extra WIN, 1 extra ok
    assert results["rows_in_exact_groups"] == 5  # 3 WIN + 2 ok
    assert results["exact_groups"] == 2
    assert results["unique_texts"] == 4
    assert results["redundant_texts"] == 4  # "see you" repeats with a new label
    assert results["conflicting_texts"] == ["see you"]


# --- Checks against independent sources ------------------------------------


def test_line_count_mismatch_is_reported():
    results = audit([("ham", "hi")])
    failures = find_failures(results, physical_lines=2)
    assert any("file has 2 lines" in f for f in failures)


def test_conflicting_labels_are_reported():
    failures = find_failures(audit(SAMPLE), physical_lines=8)
    assert any("conflicting labels" in f for f in failures)


def test_expected_counts_mismatch_is_reported():
    failures = find_failures(audit(SAMPLE), physical_lines=8)
    assert any(f.startswith("total: expected 5574") for f in failures)
