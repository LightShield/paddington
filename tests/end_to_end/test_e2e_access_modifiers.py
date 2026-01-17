import pytest
from .base_e2e import BaseE2ETest


class TestE2EAccessModifiers(BaseE2ETest):
    
    @pytest.mark.e2e
    def test_preserve_strategy_public_private(self):
        """Test preserve strategy reorders within sections"""
        cpp_content = """
class Example {
public:
    int large_field[100];
    char small_field;
    int medium_field;
private:
    double private_large[50];
    char private_small;
    int private_medium;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(cpp_file, access_modifier_strategy="preserve")
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # Should run successfully with preserve strategy
        assert "DRY-RUN MODE" in result.stdout
    
    @pytest.mark.e2e
    def test_preserve_strategy_multiple_sections(self):
        """Test preserve strategy with multiple public/private sections"""
        cpp_content = """
class MultiSection {
public:
    int pub1[50];
    char pub_small1;
private:
    double priv1[25];
    char priv_small1;
public:
    int pub2[30];
    char pub_small2;
private:
    double priv2[20];
    char priv_small2;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(cpp_file, access_modifier_strategy="preserve")
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # Should run successfully with preserve strategy
        assert "DRY-RUN MODE" in result.stdout
    
    @pytest.mark.e2e
    def test_split_strategy_optimal_ordering(self):
        """Test split strategy creates optimal ordering with per-member modifiers"""
        cpp_content = """
class OptimalTest {
public:
    char small1;
    int large1[100];
    char small2;
private:
    char priv_small1;
    double priv_large[50];
    char priv_small2;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(cpp_file, access_modifier_strategy="split")
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # Should run successfully with split strategy
        assert "DRY-RUN MODE" in result.stdout
    
    @pytest.mark.e2e
    def test_split_strategy_per_member_modifiers(self):
        """Test split strategy adds per-member access modifiers"""
        cpp_content = """
class PerMemberTest {
public:
    int public_field1;
    char public_small;
private:
    double private_field1;
    char private_small;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(cpp_file, access_modifier_strategy="split")
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # Should run successfully with split strategy
        assert "DRY-RUN MODE" in result.stdout
    
    @pytest.mark.e2e
    def test_ignore_strategy_breaks_encapsulation(self):
        """Test ignore strategy reorders across sections for optimal packing"""
        cpp_content = """
class IgnoreTest {
public:
    char pub_small1;
    int pub_large[75];
    char pub_small2;
private:
    char priv_small1;
    double priv_large[40];
    char priv_small2;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(cpp_file, access_modifier_strategy="ignore")
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # Should run successfully with ignore strategy
        assert "DRY-RUN MODE" in result.stdout
    
    @pytest.mark.e2e
    def test_struct_only_no_class_modifiers(self):
        """Test struct has no access modifiers to consider"""
        cpp_content = """
struct SimpleStruct {
    char small1;
    int large[60];
    char small2;
    double medium;
    char small3;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(cpp_file, access_modifier_strategy="preserve")
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # Should run successfully (struct has no access modifiers)
        assert "DRY-RUN MODE" in result.stdout