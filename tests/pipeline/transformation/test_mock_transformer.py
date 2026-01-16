import pytest
from implementation.pipeline.transformation.mock import MockTransformer
from implementation.struct_data import SourceModification, TransformedSource


@pytest.mark.unit
def test_mock_transformer_default_behavior():
    transformer = MockTransformer()
    
    result = transformer.transform([])
    assert result == []
    assert transformer.can_handle_file("test.py") is True


@pytest.mark.unit
def test_mock_transformer_custom_transform_result():
    expected_result = [
        TransformedSource(
            file_path="test.py", 
            original_content="original", 
            new_content="transformed content",
            modifications=()
        )
    ]
    transformer = MockTransformer(transform_result=expected_result)
    
    modifications = [SourceModification(file_path="test.py", struct_name="TestStruct", modifications=())]
    result = transformer.transform(modifications)
    
    assert result == expected_result


@pytest.mark.unit
def test_mock_transformer_custom_can_handle():
    transformer = MockTransformer(can_handle_result=False)
    
    assert transformer.can_handle_file("test.py") is False
    assert transformer.can_handle_file("any_file.txt") is False


@pytest.mark.unit
def test_mock_transformer_both_custom_values():
    expected_result = [
        TransformedSource(
            file_path="file1.py", 
            original_content="orig1", 
            new_content="content1",
            modifications=()
        ),
        TransformedSource(
            file_path="file2.py", 
            original_content="orig2", 
            new_content="content2",
            modifications=()
        )
    ]
    transformer = MockTransformer(
        transform_result=expected_result,
        can_handle_result=False
    )
    
    modifications = [SourceModification(file_path="test.py", struct_name="TestStruct", modifications=())]
    result = transformer.transform(modifications)
    
    assert result == expected_result
    assert transformer.can_handle_file("test.py") is False