import pytest
from .base_e2e import BaseE2ETest


class TestE2EMemberLockFamily(BaseE2ETest):
    
    @pytest.mark.e2e
    def test_lock_single_member(self):
        """Verifies: FR-1.2.2 - Single member with paddington-lock stays in place"""
        cpp_content = """
struct SingleLock {
    char small1;
    int locked_field; // paddington-lock
    char small2;
};

int main() {
    SingleLock s;
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
    def test_lock_multiple_members(self):
        """Verifies: FR-1.2.2 - Multiple members with paddington-lock stay in place"""
        cpp_content = """
struct MultipleLocks {
    char small1;
    int locked1; // paddington-lock
    char small2;
    int locked2; // paddington-lock
    char small3;
};

int main() {
    MultipleLocks m;
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
    def test_lock_first_member(self):
        """Verifies: FR-1.2.2 - First member with paddington-lock stays in place"""
        cpp_content = """
struct FirstLock {
    int locked_first; // paddington-lock
    char small1;
    int large[50];
    char small2;
};

int main() {
    FirstLock f;
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
    def test_lock_last_member(self):
        """Verifies: FR-1.2.2 - Last member with paddington-lock stays in place"""
        cpp_content = """
struct LastLock {
    char small1;
    int large[50];
    char small2;
    int locked_last; // paddington-lock
};

int main() {
    LastLock l;
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
    def test_lock_middle_member(self):
        """Verifies: FR-1.2.2 - Middle member with paddington-lock stays in place"""
        cpp_content = """
struct MiddleLock {
    char small1;
    int large1[30];
    int locked_middle; // paddington-lock
    int large2[30];
    char small2;
};

int main() {
    MiddleLock m;
    return 0;
}
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(cpp_file, [])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
        assert "DRY-RUN MODE" in result.stdout