"""Test for access modifier preservation bug."""

import pytest
import tempfile
from pathlib import Path


@pytest.mark.integration  
class TestAccessModifierPreservation:
    """Test that member reordering preserves access modifiers."""
    
    def test_members_stay_in_correct_access_section(self):
        """Test that protected members stay protected after reordering.
        
        Bug: Members are moved to first container regardless of original
        access modifier, breaking encapsulation.
        
        Example: al_systemc_run_args has protected members that get moved
        before the public: keyword, making them implicitly private.
        """
        # Create test file
        test_code = """
class Test {
public:
    void method();
protected:
    char a;
    int b;
    double c;
};
"""
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            cpp_file = tmpdir / "test.cpp"
            cpp_file.write_text(test_code)
            
            obj_file = tmpdir / "test.o"
            import subprocess
            result = subprocess.run(['g++', '-g', '-c', str(cpp_file), '-o', str(obj_file)],
                                   capture_output=True)
            
            if result.returncode != 0:
                pytest.skip("Compilation failed")
            
            # Run full pipeline
            from implementation.pipeline.extraction import PaholeExtractor
            from implementation.pipeline.analysis import AnalysisStage
            from implementation.pipeline.planning import PlanningStage
            from implementation.pipeline.transformation import SrcMLTransformer
            
            extractor = PaholeExtractor()
            structs = extractor.extract([obj_file])
            
            if not structs:
                pytest.skip("No structs extracted")
            
            analysis = AnalysisStage(min_savings=0, access_modifier_strategy='preserve')
            plans = analysis.process(structs)
            
            if not plans:
                pytest.skip("No optimization plans")
            
            planning = PlanningStage()
            modifications = planning.process(plans)
            
            transformer = SrcMLTransformer()
            transformed = transformer.transform(modifications)
            
            if not transformed:
                pytest.skip("No transformations")
            
            new_content = transformed[0].new_content
            
            # Check that protected: still exists and members are after it
            assert 'protected:' in new_content, "protected: keyword removed!"
            
            # Check that members are after protected:, not before public:
            protected_pos = new_content.index('protected:')
            public_pos = new_content.index('public:')
            
            # Members should be between protected and end, not before public
            assert 'double c' in new_content[protected_pos:], "Member c not in protected section"
            assert 'int b' in new_content[protected_pos:], "Member b not in protected section"
            assert 'char a' in new_content[protected_pos:], "Member a not in protected section"
            
            # Members should NOT appear before public:
            before_public = new_content[:public_pos]
            assert 'double c' not in before_public or before_public.index('double c') > protected_pos, \
                "Member moved before public: (wrong access level)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
