"""Test for patch generation bug - transformation returns empty."""

import pytest
import tempfile
from pathlib import Path
from implementation.pipeline.extraction import PaholeExtractor
from implementation.pipeline.analysis import AnalysisStage
from implementation.pipeline.planning import PlanningStage
from implementation.pipeline.transformation import SrcMLTransformer
from implementation.pipeline.output import GitPatchGenerator


@pytest.mark.integration
class TestPatchGeneration:
    """Test end-to-end patch generation."""
    
    def test_al_report_generates_patch(self):
        """Test that al_report optimization generates a patch file.
        
        This test catches the bug where transformation returns empty
        despite having valid modifications.
        """
        # Use real al_report.o file
        objfile = Path('/scratch/sim_reg7/users/ormagen/paddington/build_storm/al_common/tlm_tmp/caml/obj_and_deps/scratch/sim_reg7/users/ormagen/paddington/build_storm/snapshot/common/caml/logging/al_report.o')
        
        if not objfile.exists():
            pytest.skip("al_report.o not found")
        
        # Extract
        extractor = PaholeExtractor()
        structs = extractor.extract([objfile])
        structs = [s for s in structs if s.name == 'al_report' and not s.file_path.startswith('/tools')]
        assert len(structs) > 0, "al_report not extracted"
        
        # Analysis
        analysis = AnalysisStage(min_savings=0, access_modifier_strategy='preserve')
        plans = analysis.process(structs)
        assert len(plans) > 0, "No optimization plans generated"
        
        # Planning
        planning = PlanningStage()
        modifications = planning.process(plans)
        assert len(modifications) > 0, "No modifications generated"
        
        # Transformation - THIS IS WHERE THE BUG IS
        transformer = SrcMLTransformer()
        transformed = transformer.transform(modifications)
        
        # BUG: transformer returns empty despite having modifications
        assert len(transformed) > 0, f"Transformer returned empty! Had {len(modifications)} modifications but got 0 transformed sources"
        
        # Output
        with tempfile.TemporaryDirectory() as tmpdir:
            patch_dir = Path(tmpdir) / "patches"
            patch_dir.mkdir()
            output = GitPatchGenerator(output_dir=patch_dir)
            changes = output.apply(transformed)
            
            assert len(changes) > 0, "No changes applied"
            assert list(patch_dir.glob("*.patch")), "No .patch files created"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
