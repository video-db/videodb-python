import pytest

from videodb.understanding import normalize_understanding_analyzers


def test_omitted_analyzer_name_remains_unset():
    analyzers = [
        {"type": "vlm"},
        {"type": "object_detection", "name": "custom_objects"},
    ]

    normalized = normalize_understanding_analyzers(analyzers)

    assert normalized == [
        {"type": "vlm"},
        {"type": "object_detection", "name": "custom_objects"},
    ]
    assert analyzers == [
        {"type": "vlm"},
        {"type": "object_detection", "name": "custom_objects"},
    ]


def test_analyzer_type_is_preserved():
    normalized = normalize_understanding_analyzers([{"type": "spoken_words"}])

    assert normalized == [{"type": "spoken_words"}]


def test_repeated_unnamed_analyzer_types_are_allowed():
    normalized = normalize_understanding_analyzers([{"type": "vlm"}, {"type": "vlm"}])

    assert normalized == [{"type": "vlm"}, {"type": "vlm"}]


def test_duplicate_explicit_analyzer_names_are_rejected():
    with pytest.raises(ValueError, match="Duplicate analyzer name: summary"):
        normalize_understanding_analyzers(
            [
                {"type": "vlm", "name": "summary"},
                {"type": "vlm", "name": "summary"},
            ]
        )
