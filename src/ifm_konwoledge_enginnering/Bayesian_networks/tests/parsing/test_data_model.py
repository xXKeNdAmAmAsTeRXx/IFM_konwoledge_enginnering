import dataclasses

from BayesianNetwork.models.data import Data, DataPurpose


def test_data_has_purpose_and_data_frame_fields():
    field_names = {field.name for field in dataclasses.fields(Data)}

    assert field_names == {"data_purpose", "data_frame"}


def test_data_purpose_has_train_and_test():
    assert hasattr(DataPurpose, "Train")
    assert hasattr(DataPurpose, "Test")


def test_data_purpose_members_are_enum_members():
    assert isinstance(DataPurpose.Train, DataPurpose)
    assert isinstance(DataPurpose.Test, DataPurpose)
    assert DataPurpose.Train != DataPurpose.Test
