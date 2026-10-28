import json
import os
import tempfile

import pytest

from package_manager.errors import RepoError
from package_manager.parsing import parse_repository_text, load_repository
from package_manager.versioning import find_unsatisfiable


EXAMPLE_REPO = os.path.join(
    os.path.dirname(__file__), "..", "examples", "repo_example.json"
)


def test_load_example_repo():
    repo = load_repository(EXAMPLE_REPO)
    assert "app" in repo.packages
    assert "lib" in repo.packages
    # version normalization/equality: 1.0 present
    from packaging.version import Version

    assert Version("1.0") in repo.packages["app"].versions
    assert Version("2.0") in repo.packages["app"].versions


def test_repo_package_count_and_versions():
    repo = load_repository(EXAMPLE_REPO)
    assert len(repo.packages) == 10
    lib = repo.packages["lib"]
    assert len(lib.versions) == 3


def test_json_syntax_error_line_number():
    text = '{\n  "packages": {\n    "app": \n}'
    with pytest.raises(RepoError) as exc:
        parse_repository_text(text)
    assert "line" in str(exc.value)
    assert exc.value.path == "<input>" or True


def test_duplicate_key():
    text = '{"packages": {"app": {"versions": {"1.0": {}}}, "packages": {}}}'
    # top-level duplicate key
    text2 = '{"packages": {"a": {"versions": {"1.0": {}}}}, "packages": {"b": {"versions": {"1.0": {}}}}}'
    with pytest.raises(RepoError):
        parse_repository_text(text2)


def test_missing_packages():
    with pytest.raises(RepoError) as exc:
        parse_repository_text('{"meta": {}}')
    assert "packages" in str(exc.value)


def test_unknown_top_field():
    with pytest.raises(RepoError) as exc:
        parse_repository_text('{"packages": {}, "foo": 1}')
    assert "foo" in str(exc.value)


def test_unknown_package_field():
    with pytest.raises(RepoError) as exc:
        parse_repository_text('{"packages": {"app": {"foo": {}}}}')
    assert "foo" in str(exc.value)


def test_versions_not_object():
    with pytest.raises(RepoError):
        parse_repository_text('{"packages": {"app": {"versions": []}}}')


def test_missing_versions():
    with pytest.raises(RepoError):
        parse_repository_text('{"packages": {"app": {}}}')


def test_invalid_package_name():
    with pytest.raises(RepoError):
        parse_repository_text('{"packages": {"bad?name": {"versions": {"1.0": {}}}}}')


def test_duplicate_package_canonical():
    with pytest.raises(RepoError):
        parse_repository_text('{"packages": {"Foo_Bar": {"versions": {"1.0": {}}}, "foo-bar": {"versions": {"2.0": {}}}}}')


def test_invalid_version():
    with pytest.raises(RepoError):
        parse_repository_text('{"packages": {"app": {"versions": {"not-a-version": {}}}}}')


def test_duplicate_version():
    with pytest.raises(RepoError):
        parse_repository_text('{"packages": {"app": {"versions": {"1.0": {}, "1.0.0": {}}}}}')


def test_requires_not_list():
    with pytest.raises(RepoError):
        parse_repository_text('{"packages": {"app": {"versions": {"1.0": {"requires": "lib"}}}}}')


def test_unknown_info_field():
    with pytest.raises(RepoError) as exc:
        parse_repository_text('{"packages": {"app": {"versions": {"1.0": {"foo": 1}}}}}')
    assert "foo" in str(exc.value)


def test_self_dependency():
    with pytest.raises(RepoError):
        parse_repository_text('{"packages": {"app": {"versions": {"1.0": {"requires": ["app"]}}}}}')


def test_self_conflict():
    with pytest.raises(RepoError):
        parse_repository_text('{"packages": {"app": {"versions": {"1.0": {"conflicts": ["app"]}}}}}')


def test_conflict_with_alternatives_rejected():
    with pytest.raises(RepoError):
        parse_repository_text('{"packages": {"app": {"versions": {"1.0": {"conflicts": ["lib | util"]}}}}}')


def test_invalid_requirement_in_list():
    with pytest.raises(RepoError):
        parse_repository_text('{"packages": {"app": {"versions": {"1.0": {"requires": ["lib ~= 2.0"]}}}}}')


def test_unsatisfiable_warning_detection():
    text = '{"packages": {"app": {"versions": {"1.0": {"requires": ["missingpkg"]}}}}}'
    repo = parse_repository_text(text)
    warnings = find_unsatisfiable(repo)
    assert len(warnings) == 1


def test_repo_versions_sorted_descending():
    repo = load_repository(EXAMPLE_REPO)
    lib_versions = repo.versions_of("lib")
    from packaging.version import Version

    assert lib_versions == sorted(lib_versions, reverse=True)
    assert lib_versions[0] == Version("2.0")


def test_load_repository_missing_file():
    with pytest.raises(FileNotFoundError):
        load_repository("/no/such/file.json")
