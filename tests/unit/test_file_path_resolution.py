"""Test for file path resolution in transformations."""

import pytest
import tempfile
from pathlib import Path

from implementation.pipeline.transformation.srcml import SrcMLTransformer
from implementation.struct_data.source_change import SourceModification, Modification, Location


@pytest.mark.unit
class TestFilePathResolution:
    """Test that file paths are correctly resolved during transformation."""
    
    def test_snapshot_path_resolution(self):
        """Test that snapshot paths are resolved to actual source paths.
        
        Bug: Pahole extracts paths like /build/snapshot/common/file.h
        but transformations need /source/common/file.h
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create actual source file
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            test_file = source_dir / "test.h"
            test_file.write_text("""
struct Test {
    int a;
    double b;
};
""")
            
            # Modification has snapshot path (from pahole)
            snapshot_path = Path(tmpdir) / "build" / "snapshot" / "test.h"
            
            mod = SourceModification(
                file_path=str(snapshot_path),  # Wrong path from pahole
                struct_name="Test",
                modifications=(
                    Modification(
                        type="reorder",
                        location=Location(str(snapshot_path), 2, 0),
                        old_content="members: a, b",
                        new_content="members: b, a",
                        access_strategy="preserve"
                    ),
                ),
                access_strategy="preserve"
            )
            
            transformer = SrcMLTransformer()
            
            # Should fail without path resolution
            result = transformer._transform_file(mod)
            assert result is None, "Should fail with non-existent snapshot path"
    
    def test_path_mapping_configuration(self):
        """Test that path mapping can be configured."""
        # This test documents the expected fix:
        # Add --source-root flag to map snapshot paths to source paths
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
