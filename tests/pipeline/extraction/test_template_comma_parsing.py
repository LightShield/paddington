"""Test for template name parsing with multiple parameters."""

import pytest
from implementation.pipeline.extraction.pahole import PaholeExtractor


@pytest.mark.unit
class TestTemplateNameParsing:
    """Test that template names with multiple parameters are parsed correctly."""
    
    def test_template_with_two_parameters(self):
        """Test parsing template with 2 parameters: Template<Type1, Type2>
        
        BUG: Template names are truncated at comma, resulting in:
        'AppendValue<al_cso_arblist_type,' instead of full name.
        """
        output = """/* <29> /tmp/test.h:1 */
class AppendValue<al_cso_arblist_type, bool> {
	int                        value;                /*     0     4 */

	/* size: 4, cachelines: 1, members: 1 */
};"""
        
        extractor = PaholeExtractor()
        structs = extractor._parse_pahole_output(output)
        
        assert len(structs) == 1
        assert structs[0].name == "AppendValue<al_cso_arblist_type, bool>"
        assert ',' in structs[0].name, "Template name should include comma"
        assert structs[0].name.endswith('>'), "Template name should end with >"
    
    def test_nested_template_with_commas(self):
        """Test parsing nested template: Template<Type1<A, B>, Type2>"""
        output = """/* <29> /tmp/test.h:1 */
class Container<std::pair<int, double>, bool> {
	int                        value;                /*     0     4 */

	/* size: 4, cachelines: 1, members: 1 */
};"""
        
        extractor = PaholeExtractor()
        structs = extractor._parse_pahole_output(output)
        
        assert len(structs) == 1
        assert structs[0].name == "Container<std::pair<int, double>, bool>"
        assert structs[0].name.count(',') == 2, "Should have 2 commas"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
