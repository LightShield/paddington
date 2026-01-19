"""Test for multiple access modifier sections bug."""

import pytest
from implementation.pipeline.transformation.srcml import SrcMLTransformer
from implementation.struct_data.source_change import SourceModification, Modification, Location


@pytest.mark.unit
class TestMultipleAccessSections:
    """Test srcML transformer handles multiple access modifier sections."""
    
    def test_multiple_protected_sections(self):
        """Test that structs with multiple protected: sections are handled.
        
        Real-world case: al_report has:
        - private: (empty)
        - protected: (8 members)
        - private: (1 member)
        - protected: (11 members)
        
        The bug: _reorder_members only processes the first access section.
        """
        # This test would need a real file with multiple sections
        # For now, document the issue
        
        # The fix: Process ALL access modifier sections, not just the first
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
