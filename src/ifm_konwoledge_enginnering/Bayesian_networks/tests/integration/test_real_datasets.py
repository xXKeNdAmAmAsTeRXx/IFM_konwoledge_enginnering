from BayesianNetwork.models.data import Data
from BayesianNetwork.models.graph import GraphData
from BayesianNetwork.parsing.data_parsing import parse_data
from BayesianNetwork.parsing.description_parsing import description_parser
from BayesianNetwork.parsing.query_parsing import query_parser


def test_description_parser_integration_dataset(integration_dataset):
    graph = description_parser(str(integration_dataset / "opis.json"))

    assert isinstance(graph, GraphData)
    assert len(graph.exper_edges) == 4
    assert len(graph.required_edges) == 2
    assert len(graph.forbidden_edges) == 2
    assert [len(tier) for tier in graph.tiers] == [2, 2, 1]


def test_description_parser_variable_names(integration_dataset):
    graph = description_parser(str(integration_dataset / "opis.json"))

    assert graph.exper_edges == [
        ("D", "G"),
        ("I", "G"),
        ("G", "L"),
        ("I", "S"),
    ]
    assert graph.tiers == [["D", "I"], ["G", "S"], ["L"]]
    assert set(graph.variables_dict) == {"D", "I", "G", "S", "L"}


def test_description_parser_references_defined_variables(integration_dataset):
    graph = description_parser(str(integration_dataset / "opis.json"))

    assert set(graph.variables_dict) == {"D", "I", "G", "S", "L"}

    referenced = [
        name
        for edge in (*graph.exper_edges, *graph.required_edges, *graph.forbidden_edges)
        for name in edge
    ]
    referenced.extend(name for tier in graph.tiers for name in tier)

    assert referenced
    assert all(name in graph.variables_dict for name in referenced)


def test_query_parser_integration_dataset(integration_dataset):
    variables = description_parser(str(integration_dataset / "opis.json")).variables_dict
    queries = query_parser(str(integration_dataset / "zapytania.txt"), variables)

    assert len(queries) == 4


def test_query_parser_preserves_query_order(integration_dataset):
    variables = description_parser(str(integration_dataset / "opis.json")).variables_dict
    queries = query_parser(str(integration_dataset / "zapytania.txt"), variables)

    assert [query.variables[0] for query in queries] == ["G", "G", "I", "D"]
    assert [len(query.variables) for query in queries] == [1, 1, 1, 2]


def test_parse_data_training_file(integration_dataset):
    variables = description_parser(str(integration_dataset / "opis.json")).variables_dict
    data = parse_data(
        str(integration_dataset / "dane.csv"), variables, is_train_data=True
    )

    assert isinstance(data, Data)
    assert len(data.data_frame) == 5
    assert data.data_frame.notna().all(axis=1).sum() == 3

    missing = data.data_frame.isna().sum().to_dict()
    assert missing == {"D": 1, "I": 1, "G": 0, "S": 1, "L": 0}


def test_parse_data_test_file_is_complete(integration_dataset):
    variables = description_parser(str(integration_dataset / "opis.json")).variables_dict
    data = parse_data(
        str(integration_dataset / "test.csv"),
        variables,
        is_train_data=False,
        allow_missing=False,
    )

    assert len(data.data_frame) == 3
    assert set(data.data_frame.columns) == set(variables)
    assert data.data_frame.isna().sum().sum() == 0
