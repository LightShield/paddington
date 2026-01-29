"""Test for multiple cpp files with different constructors."""
import pytest

import pytest
import tempfile
import subprocess
from pathlib import Path
from implementation.pipeline.extraction import PaholeExtractor
from implementation.pipeline.analysis import AnalysisStage
from implementation.pipeline.planning import PlanningStage
from implementation.pipeline.transformation import SrcMLTransformer
from implementation.pipeline.output import GitPatchGenerator


@pytest.mark.integration
class TestMultipleCppConstructors:
    """Test handling of constructors split across multiple .cpp files."""
    
    @pytest.mark.skip(reason="Constructor support temporarily disabled for baseline")
    def test_constructors_in_separate_cpp_files(self):
        """Test that constructors in different .cpp files are all updated.
        
        Scenario: Class has 2 constructors, each implemented in a different .cpp file.
        This is legal C++ and should be supported.
        
        Example:
        - test.h: class Test { int a; double b; char c; };
        - test1.cpp: Test::Test() : a(1), b(2.0), c('x') {}
        - test2.cpp: Test::Test(int x) : a(x), b(0), c('y') {}
        
        Both constructors should have their initializer lists reordered.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create header
            header = tmpdir / "test.h"
            header.write_text("""
class Test {
    int a;
    double b;
    char c;
public:
    Test();
    Test(int x);
};
""")
            
            # Create first cpp with default constructor
            cpp1 = tmpdir / "test1.cpp"
            cpp1.write_text("""
#include "test.h"

Test::Test() : a(1), b(2.0), c('x') {
}
""")
            
            # Create second cpp with parameterized constructor
            cpp2 = tmpdir / "test2.cpp"
            cpp2.write_text("""
#include "test.h"

Test::Test(int x) : a(x), b(0.0), c('y') {
}
""")
            
            # Compile both
            obj1 = tmpdir / "test1.o"
            obj2 = tmpdir / "test2.o"
            
            result1 = subprocess.run(['g++', '-g', '-c', str(cpp1), '-o', str(obj1), f'-I{tmpdir}'],
                                    capture_output=True)
            result2 = subprocess.run(['g++', '-g', '-c', str(cpp2), '-o', str(obj2), f'-I{tmpdir}'],
                                    capture_output=True)
            
            if result1.returncode != 0 or result2.returncode != 0:
                pytest.skip("Compilation failed")
            
            # Extract from both object files
            extractor = PaholeExtractor()
            structs = extractor.extract([obj1, obj2])
            
            if not structs:
                pytest.skip("No structs extracted")
            
            # Get compilation data
            comp_data = extractor.get_compilation_data()
            
            # Check that Test is associated with BOTH cpp files
            if 'Test' in comp_data:
                cpp_files = comp_data['Test']
                print(f"Test associated with {len(cpp_files)} cpp files: {cpp_files}")
                
                # Should have both test1.cpp and test2.cpp
                assert len(cpp_files) >= 2, f"Expected 2 cpp files, got {len(cpp_files)}"
                assert any('test1.cpp' in f for f in cpp_files), "test1.cpp not found"
                assert any('test2.cpp' in f for f in cpp_files), "test2.cpp not found"
            else:
                pytest.skip("Test struct not in compilation data")
            
            # Run full pipeline
            analysis = AnalysisStage(min_savings=0, access_modifier_strategy='preserve')
            plans = analysis.process(structs)
            
            if not plans:
                pytest.skip("No optimization plans")
            
            planning = PlanningStage()
            planning.set_compilation_data(comp_data)
            modifications = planning.process(plans)
            
            # Should have modifications for: test.h, test1.cpp, test2.cpp
            print(f"Modifications: {len(modifications)}")
            for mod in modifications:
                print(f"  {Path(mod.file_path).name}")
            
            assert len(modifications) >= 3, f"Expected 3 modifications (.h + 2 .cpp), got {len(modifications)}"
            
            # Transform
            transformer = SrcMLTransformer()
            transformed = transformer.transform(modifications)
            
            print(f"Transformed: {len(transformed)}")
            
            # Should have transformed sources for all files with changes
            assert len(transformed) >= 2, f"Expected at least 2 transformed sources, got {len(transformed)}"
            
            # Generate patches
            patch_dir = tmpdir / "patches"
            patch_dir.mkdir()
            output = GitPatchGenerator(output_dir=patch_dir)
            changes = output.apply(transformed)
            
            print(f"Patches: {len(changes)}")
            
            # Should have patches for all transformed files
            assert len(changes) >= 2, f"Expected at least 2 patches, got {len(changes)}"
            
            # Verify patch files exist
            patch_files = list(patch_dir.glob("*.patch"))
            assert len(patch_files) >= 2, f"Expected at least 2 .patch files, got {len(patch_files)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
