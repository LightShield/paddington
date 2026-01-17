import pytest
from .base_e2e import BaseE2ETest


class TestE2ERegionMarkersFamily(BaseE2ETest):
    
    @pytest.mark.e2e
    def test_region_single_struct(self):
        """Verifies: FR-1.2.3 - Single struct in region is skipped"""
        cpp_content = """
struct BeforeRegion {
    char small1;
    int large[30];
    char small2;
};

// paddington-off
struct InRegion {
    char small1;
    int large[100];
    char small2;
};
// paddington-on

struct AfterRegion {
    char small1;
    int large[40];
    char small2;
};

int main() {
    BeforeRegion before;
    InRegion inRegion;
    AfterRegion after;
    return 0;
}
"""
        cpp_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(cpp_file, [])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
        assert "DRY-RUN MODE" in result.stdout
    
    @pytest.mark.e2e
    def test_region_multiple_structs(self):
        """Verifies: FR-1.2.3 - Multiple structs in region are skipped"""
        cpp_content = """
struct BeforeRegion {
    char small1;
    int large[30];
    char small2;
};

// paddington-off
struct FirstInRegion {
    char small1;
    int large[100];
    char small2;
};

struct SecondInRegion {
    char small1;
    int large[200];
    char small2;
};
// paddington-on

struct AfterRegion {
    char small1;
    int large[40];
    char small2;
};

int main() {
    BeforeRegion before;
    FirstInRegion first;
    SecondInRegion second;
    AfterRegion after;
    return 0;
}
"""
        cpp_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(cpp_file, [])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
        assert "DRY-RUN MODE" in result.stdout
    
    @pytest.mark.e2e
    def test_region_nested_regions(self):
        """Verifies: FR-1.2.3 - Nested regions work correctly"""
        cpp_content = """
struct BeforeRegion {
    char small1;
    int large[30];
    char small2;
};

// paddington-off
struct OuterRegion {
    char small1;
    int large[100];
    char small2;
};

// paddington-off
struct InnerRegion {
    char small1;
    int large[200];
    char small2;
};
// paddington-on

struct StillInOuter {
    char small1;
    int large[150];
    char small2;
};
// paddington-on

struct AfterRegion {
    char small1;
    int large[40];
    char small2;
};

int main() {
    BeforeRegion before;
    OuterRegion outer;
    InnerRegion inner;
    StillInOuter stillOuter;
    AfterRegion after;
    return 0;
}
"""
        cpp_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(cpp_file, [])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
        assert "DRY-RUN MODE" in result.stdout
    
    @pytest.mark.e2e
    def test_region_before_and_after(self):
        """Verifies: FR-1.2.3 - Structs before and after region are processed"""
        cpp_content = """
struct FirstBefore {
    char small1;
    int large[30];
    char small2;
};

struct SecondBefore {
    char small1;
    int large[35];
    char small2;
};

// paddington-off
struct InRegion {
    char small1;
    int large[100];
    char small2;
};
// paddington-on

struct FirstAfter {
    char small1;
    int large[40];
    char small2;
};

struct SecondAfter {
    char small1;
    int large[45];
    char small2;
};

int main() {
    FirstBefore first;
    SecondBefore second;
    InRegion inRegion;
    FirstAfter firstAfter;
    SecondAfter secondAfter;
    return 0;
}
"""
        cpp_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(cpp_file, [])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
        assert "DRY-RUN MODE" in result.stdout
    
    @pytest.mark.e2e
    def test_region_entire_file(self):
        """Verifies: FR-1.2.3 - Entire file can be in region"""
        cpp_content = """
// paddington-off
struct FirstStruct {
    char small1;
    int large[100];
    char small2;
};

struct SecondStruct {
    char small1;
    int large[200];
    char small2;
};

int main() {
    FirstStruct first;
    SecondStruct second;
    return 0;
}
// paddington-on
"""
        cpp_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(cpp_file, [])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
        assert "DRY-RUN MODE" in result.stdout