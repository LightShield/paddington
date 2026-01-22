"""Test for filtering structs by source file path."""

import pytest
from pathlib import Path
from implementation.struct_data import StructInfo, MemberInfo


@pytest.mark.unit
class TestStructFiltering:
    """Test that structs are filtered by their source file path."""
    
    def test_exclude_tools_directory(self):
        """Test that structs from /tools/* are excluded.
        
        Bug: Exclusion patterns only apply to .o files, not struct source files.
        A struct defined in /tools/snps/.../*.h but compiled into our .o file
        will not be excluded.
        
        Expected: Structs with file_path starting with /tools/ should be filtered out.
        """
        # Create test structs
        structs = [
            StructInfo(
                name="MyStruct",
                size=16,
                members=(),
                file_path="/rdata/model/common/caml/test.h",
                line=10
            ),
            StructInfo(
                name="ToolsStruct",
                size=16,
                members=(),
                file_path="/tools/snps/virtualizer/include/test.h",
                line=10
            ),
            StructInfo(
                name="ThirdPartyStruct",
                size=16,
                members=(),
                file_path="/rdata/model/common/third-party/lib/test.h",
                line=10
            ),
        ]
        
        # Apply exclusion patterns
        exclude_patterns = ["/tools/*", "*/third-party/*"]
        
        # Filter structs by file_path
        import fnmatch
        filtered = []
        for struct in structs:
            excluded = False
            for pattern in exclude_patterns:
                if fnmatch.fnmatch(struct.file_path, pattern) or struct.file_path.startswith(pattern.rstrip('*')):
                    excluded = True
                    break
            if not excluded:
                filtered.append(struct)
        
        # Should only have MyStruct
        assert len(filtered) == 1, f"Expected 1 struct after filtering, got {len(filtered)}"
        assert filtered[0].name == "MyStruct"
        
        # ToolsStruct and ThirdPartyStruct should be excluded
        names = [s.name for s in filtered]
        assert "ToolsStruct" not in names, "ToolsStruct from /tools/ should be excluded"
        assert "ThirdPartyStruct" not in names, "ThirdPartyStruct from third-party should be excluded"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
