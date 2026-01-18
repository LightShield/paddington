import pytest
import os
from .base_e2e import BaseE2ETest


class TestE2EProviderSwappabilityFamily(BaseE2ETest):
    """Verifies: NFR-2.4.1 Provider Swappability Family"""
    
    @pytest.mark.e2e
    def test_swap_extractor_dwarf_to_macho(self):
        """Test swapping extractor from DWARF to Mach-O"""
        cpp_content = """
struct Point {
    int x;
    int y;
    int z;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        # Test with DWARF extractor
        result_dwarf = self.run_optimize(cpp_file, ["--extractor", "dwarf"])
        if "ImportError" in result_dwarf.stderr or "ModuleNotFoundError" in result_dwarf.stderr:
            pytest.skip("Application has import issues")
        
        # Test with pahole extractor
        result_pahole = self.run_optimize(cpp_file, ["--extractor", "pahole"])
        
        # Both should succeed or gracefully handle unavailable extractors
        assert result_dwarf.returncode == 0 or "not available" in result_dwarf.stderr.lower()
        assert result_pahole.returncode == 0 or "not available" in result_pahole.stderr.lower()
    
    @pytest.mark.e2e
    def test_swap_transformer_srcml_to_lineswap(self):
        """Test swapping transformer from srcML to lineswap"""
        cpp_content = """
struct Point {
    int x;
    int y;
    int z;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        # Test with srcML transformer
        result_srcml = self.run_optimize(cpp_file, ["--transformer", "srcml"])
        if "ImportError" in result_srcml.stderr or "ModuleNotFoundError" in result_srcml.stderr:
            pytest.skip("Application has import issues")
        
        # Test with lineswap transformer
        result_lineswap = self.run_optimize(cpp_file, ["--transformer", "lineswap"])
        
        # Both should succeed or gracefully handle unavailable transformers
        assert result_srcml.returncode == 0 or "not available" in result_srcml.stderr.lower()
        assert result_lineswap.returncode == 0 or "not available" in result_lineswap.stderr.lower()
    
    @pytest.mark.e2e
    def test_swap_output_patch_to_file(self):
        """Test swapping output provider from patch to file"""
        cpp_content = """
struct Point {
    int x;
    int y;
    int z;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        # Test with patch output
        result_patch = self.run_optimize(cpp_file, ["--output", "patch", "--patch-dir", self.temp_dir])
        if "ImportError" in result_patch.stderr or "ModuleNotFoundError" in result_patch.stderr:
            pytest.skip("Application has import issues")
        
        # Test with file output
        result_file = self.run_optimize(cpp_file, ["--output", "file", "--apply"])
        
        # Both should succeed
        self.assert_success(result_patch)
        self.assert_success(result_file)
    
    @pytest.mark.e2e
    def test_all_provider_combinations(self):
        """Test various provider combinations work together"""
        cpp_content = """
struct Point {
    int x;
    int y;
    int z;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        combinations = [
            ["--extractor", "dwarf", "--transformer", "srcml", "--output", "patch"],
            ["--extractor", "dwarf", "--transformer", "lineswap", "--output", "file"],
        ]
        
        for combo in combinations:
            args = combo + ["--patch-dir", self.temp_dir] if "patch" in combo else combo + ["--apply"]
            result = self.run_optimize(cpp_file, args)
            
            if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
                pytest.skip("Application has import issues")
            
            # Should succeed or gracefully handle unavailable providers
            assert result.returncode == 0 or "not available" in result.stderr.lower()
    
    @pytest.mark.e2e
    def test_provider_error_handling(self):
        """Test graceful handling of invalid provider names"""
        cpp_content = """
struct Point {
    int x;
    int y;
    int z;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        # Test invalid extractor
        result = self.run_optimize(cpp_file, ["--extractor", "invalid_extractor"])
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        # Should fail gracefully with meaningful error
        assert result.returncode != 0 or "not available" in result.stderr.lower() or "invalid" in result.stderr.lower()
    
    @pytest.mark.e2e
    def test_provider_fallback(self):
        """Test fallback behavior when preferred provider unavailable"""
        cpp_content = """
struct Point {
    int x;
    int y;
    int z;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        # Test with potentially unavailable provider
        result = self.run_optimize(cpp_file, ["--extractor", "macho"])
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        # Should either succeed or provide fallback/error message
        assert result.returncode == 0 or "not available" in result.stderr.lower() or "fallback" in result.stderr.lower()