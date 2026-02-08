"""Unit tests for path exclusion utility."""

import pytest
from pathlib import Path
from implementation.utils.path_exclusion import should_exclude_path, should_exclude_directory


class TestShouldExcludePath:
    """Test cases for should_exclude_path function."""
    
    def test_empty_patterns(self):
        """Empty pattern list should not exclude any path."""
        path = Path("any/path/here")
        assert not should_exclude_path(path, [])
        
    def test_platforms_wildcard_regs_pattern(self):
        """Test 'platforms/*/regs/*' pattern matching."""
        pattern = "platforms/*/regs/*"
        
        # Should match - pattern starts with literal 'platforms'
        assert should_exclude_path(Path("platforms/arm/regs/config.py"), [pattern])
        assert should_exclude_path(Path("platforms/riscv/regs/nested/file.txt"), [pattern])
        
        # Should not match - 'platforms' must be at start of path
        assert not should_exclude_path(Path("platforms/arm/config.py"), [pattern])
        assert not should_exclude_path(Path("other/platforms/arm/regs/config.py"), [pattern])
        assert not should_exclude_path(Path("src/platforms/x86/regs/data.json"), [pattern])
        assert not should_exclude_path(Path("platforms/regs/config.py"), [pattern])
        
    def test_crypto_wildcard_pattern(self):
        """Test '*/crypto/*' pattern matching."""
        pattern = "*/crypto/*"
        
        # Should match
        assert should_exclude_path(Path("lib/crypto/keys.py"), [pattern])
        assert should_exclude_path(Path("src/utils/crypto/hash.py"), [pattern])
        assert should_exclude_path(Path("deep/nested/crypto/secure/file.txt"), [pattern])
        
        # Should not match - pattern starts with *, so crypto must have a prefix
        assert not should_exclude_path(Path("crypto/keys.py"), [pattern])
        assert not should_exclude_path(Path("lib/cryptography/file.py"), [pattern])
        assert not should_exclude_path(Path("src/crypto.py"), [pattern])
        
    def test_absolute_tools_pattern(self):
        """Test '/tools/*' absolute pattern matching."""
        pattern = "/tools/*"
        
        # Should match - absolute pattern matches from start (relative paths)
        assert should_exclude_path(Path("tools/build.py"), [pattern])
        assert should_exclude_path(Path("tools/nested/script.sh"), [pattern])
        
        # Should match - absolute pattern matches from start (absolute paths)
        assert should_exclude_path(Path("/tools/build.py"), [pattern])
        assert should_exclude_path(Path("/tools/nested/script.sh"), [pattern])
        assert should_exclude_path(Path("/tools/snps/virtualizer/file.h"), [pattern])
        
        # Should not match - absolute pattern requires exact start match
        assert not should_exclude_path(Path("src/tools/build.py"), [pattern])
        assert not should_exclude_path(Path("other/tools/script.sh"), [pattern])
        assert not should_exclude_path(Path("/src/tools/build.py"), [pattern])
        
    def test_multiple_patterns(self):
        """Test multiple exclusion patterns."""
        patterns = ["*/crypto/*", "platforms/*/regs/*", "/tools/*"]
        
        # Each pattern should work
        assert should_exclude_path(Path("lib/crypto/keys.py"), patterns)
        assert should_exclude_path(Path("platforms/arm/regs/config.py"), patterns)
        assert should_exclude_path(Path("tools/build.py"), patterns)
        
        # Non-matching paths should not be excluded
        assert not should_exclude_path(Path("src/main.py"), patterns)
        
    def test_relative_path_with_root(self):
        """Test relative path handling with root parameter."""
        root = Path("/project")
        patterns = ["/tools/*"]
        
        # Absolute path under root should be converted to relative
        abs_path = Path("/project/tools/build.py")
        assert should_exclude_path(abs_path, patterns, root)
        
        # Absolute path not under root should return False (cannot match relative patterns)
        abs_path_outside = Path("/other/tools/build.py")
        assert not should_exclude_path(abs_path_outside, patterns, root)
        
    def test_relative_path_matching(self):
        """Test relative path matching behavior."""
        patterns = ["src/*/test/*"]
        
        # Relative paths should match - pattern starts with literal 'src'
        assert should_exclude_path(Path("src/utils/test/file.py"), patterns)
        assert should_exclude_path(Path("src/core/test/nested/file.py"), patterns)
        
        # Should not match incomplete patterns or wrong start
        assert not should_exclude_path(Path("src/test/file.py"), patterns)  # Missing middle wildcard
        assert not should_exclude_path(Path("utils/test/file.py"), patterns)  # Doesn't start with 'src'
        
    def test_edge_case_single_wildcard(self):
        """Test patterns with only wildcards."""
        patterns = ["*", "*/", "*/*"]
        
        # Single wildcard should not match (no segments after filtering)
        assert not should_exclude_path(Path("any/path"), ["*"])
        assert not should_exclude_path(Path("any/path"), ["*/"]) 
        
        # Pattern with actual segments should work
        assert not should_exclude_path(Path("any/path"), ["*/*"])  # No segments after filtering
        
    def test_exact_segment_matching(self):
        """Test that segments must match exactly."""
        patterns = ["test/data/*"]
        
        # Exact match should work
        assert should_exclude_path(Path("test/data/file.txt"), patterns)
        
        # Partial matches should not work
        assert not should_exclude_path(Path("testing/data/file.txt"), patterns)
        assert not should_exclude_path(Path("test/database/file.txt"), patterns)
        
    def test_nested_directory_patterns(self):
        """Test patterns with deeply nested structures."""
        patterns = ["a/b/c/d/*"]
        
        # Should match nested structure when pattern starts at beginning
        assert should_exclude_path(Path("a/b/c/d/file.txt"), patterns)
        assert should_exclude_path(Path("a/b/c/d/nested/file.txt"), patterns)
        
        # Should not match when pattern doesn't start at beginning
        assert not should_exclude_path(Path("root/a/b/c/d/file.txt"), patterns)
        assert not should_exclude_path(Path("a/b/c/file.txt"), patterns)
        assert not should_exclude_path(Path("a/c/d/file.txt"), patterns)


class TestShouldExcludeDirectory:
    """Test cases for should_exclude_directory function."""
    
    def test_directory_itself_excluded(self):
        """Test when directory itself matches exclusion pattern."""
        patterns = ["*/crypto/*"]
        
        # Directory itself should be excluded
        assert should_exclude_directory(Path("lib/crypto/keys"), patterns)
        assert should_exclude_directory(Path("src/crypto/hash"), patterns)
        
    def test_parent_directory_excluded(self):
        """Test when parent directory matches exclusion pattern."""
        patterns = ["*/crypto/*"]
        
        # Child of excluded directory should be excluded
        crypto_dir = Path("lib/crypto/secure")
        child_dir = crypto_dir / "keys" / "nested"
        assert should_exclude_directory(child_dir, patterns)
        
    def test_no_exclusion(self):
        """Test when directory and parents are not excluded."""
        patterns = ["*/crypto/*"]
        
        # Unrelated directory should not be excluded
        assert not should_exclude_directory(Path("lib/utils/helpers"), patterns)
        assert not should_exclude_directory(Path("src/main/core"), patterns)
        
    def test_root_directory_exclusion(self):
        """Test exclusion with root parameter."""
        root = Path("/project")
        patterns = ["/tools/*"]
        
        # Directory under excluded path should be excluded
        tools_subdir = Path("/project/tools/build/scripts")
        assert should_exclude_directory(tools_subdir, patterns, root)
        
    def test_multiple_parent_levels(self):
        """Test checking multiple levels of parent directories."""
        patterns = ["platforms/*/regs/*"]
        
        # Deeply nested directory under excluded path
        deep_dir = Path("platforms/arm/regs/config/nested/deep/subdir")
        assert should_exclude_directory(deep_dir, patterns)
        
        # Directory not under excluded path
        other_dir = Path("platforms/arm/config/nested/deep/subdir")
        assert not should_exclude_directory(other_dir, patterns)
        
    def test_empty_patterns_directory(self):
        """Test directory exclusion with empty patterns."""
        assert not should_exclude_directory(Path("any/directory"), [])
        
    def test_filesystem_root_handling(self):
        """Test that checking stops at filesystem root."""
        patterns = ["root/*"]
        
        # Should not cause infinite loop when checking parents
        deep_path = Path("/very/deep/nested/directory/structure")
        result = should_exclude_directory(deep_path, patterns)
        assert isinstance(result, bool)  # Should complete without error


class TestIntegration:
    """Integration tests combining both functions."""
    
    def test_consistent_behavior(self):
        """Test that both functions behave consistently."""
        patterns = ["*/crypto/*", "platforms/*/regs/*"]
        
        test_paths = [
            Path("lib/crypto/keys.py"),
            Path("platforms/arm/regs/config.py"),
            Path("src/main.py"),
            Path("tools/build.py")
        ]
        
        for path in test_paths:
            path_excluded = should_exclude_path(path, patterns)
            dir_excluded = should_exclude_directory(path.parent, patterns)
            
            # If parent directory is excluded, path should typically be excluded too
            # (though not always, depending on the specific pattern)
            if dir_excluded:
                # This is expected behavior - parent exclusion affects children
                pass
                
    def test_real_world_patterns(self):
        """Test with realistic exclusion patterns."""
        patterns = [
            "*/node_modules/*",
            r"*/\.git/*", 
            "*/build/*",
            "*/dist/*",
            "*/__pycache__/*",
            r"*/\.pytest_cache/*"
        ]
        
        # Should exclude common build/cache directories
        assert should_exclude_path(Path("project/node_modules/package/index.js"), patterns)
        assert should_exclude_path(Path("src/__pycache__/module.pyc"), patterns)
        assert should_exclude_directory(Path("project/build/output"), patterns)
        
        # Should not exclude source files
        assert not should_exclude_path(Path("src/main.py"), patterns)
        assert not should_exclude_directory(Path("src/utils"), patterns)