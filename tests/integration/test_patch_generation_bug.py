"""Test for patch generation bug - transformation returns empty."""

import pytest
import tempfile
from pathlib import Path
from implementation.pipeline.extraction import PaholeExtractor
from implementation.pipeline.analysis import AnalysisStage
from implementation.pipeline.planning import PlanningStage
from implementation.pipeline.transformation import SrcMLTransformer
from implementation.pipeline.output import GitPatchGenerator

try:
    import srcml_caller
    SRCML_AVAILABLE = True
except ImportError:
    SRCML_AVAILABLE = False


@pytest.mark.integration
class TestPatchGeneration:
    """Test end-to-end patch generation."""
    
    def test_al_report_generates_patch(self):
        """Test that struct optimization generates a patch file.
        
        This test catches the bug where transformation returns empty
        despite having valid modifications.
        """
        # Create a simple test case instead of relying on external files
        import tempfile
        import subprocess
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create a simple C++ file
            cpp_file = tmpdir / "test.cpp"
            cpp_content = """
struct TestStruct {
    char a;      // 1 byte
    int b;       // 4 bytes  
    char c;      // 1 byte
};

int main() {
    TestStruct t;
    return 0;
}
"""
            cpp_file.write_text(cpp_content)
            
            # Compile it
            obj_file = tmpdir / "test.o"
            result = subprocess.run(['g++', '-g', '-c', str(cpp_file), '-o', str(obj_file)], 
                                  capture_output=True)
            if result.returncode != 0:
                pytest.skip("Failed to compile test file")
            
            # Extract
            extractor = PaholeExtractor()
            structs = extractor.extract([obj_file])
            structs = [s for s in structs if s.name == 'TestStruct']
            assert len(structs) > 0, "TestStruct not extracted"
            
            # Analysis
            analysis = AnalysisStage(min_savings=0, access_modifier_strategy='preserve')
            plans = analysis.process(structs)
            assert len(plans) > 0, "No optimization plans generated"
            
            # Planning
            planning = PlanningStage()
            modifications = planning.process(plans)
            assert len(modifications) > 0, "No modifications generated"
            
            # Transformation - THIS IS WHERE THE BUG WAS
            transformer = SrcMLTransformer()
            transformed = transformer.transform(modifications)
            
            # Should not return empty if srcML is available
            if not SRCML_AVAILABLE:
                pytest.skip("srcML not available")
            
            # If srcML is available, we should get results
            assert len(transformed) > 0, f"Transformer returned empty! Had {len(modifications)} modifications but got 0 transformed sources"
            
            # Output
            patch_dir = tmpdir / "patches"
            patch_dir.mkdir()
            output = GitPatchGenerator(output_dir=patch_dir)
            changes = output.apply(transformed)
            
            assert len(changes) > 0, "No changes applied"
            assert list(patch_dir.glob("*.patch")), "No .patch files created"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
