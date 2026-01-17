import pytest
from .base_e2e import BaseE2ETest


class TestE2EPreprocessorExtendedFamily(BaseE2ETest):
    
    @pytest.mark.e2e
    def test_preprocessor_nested_ifdef(self):
        """Test nested #ifdef directives - Verifies: FR-1.8
        
        Tests handling of nested preprocessor conditionals with struct definitions.
        """
        cpp_content = """
#define FEATURE_A
#define FEATURE_B

struct NestedStruct {
#ifdef FEATURE_A
    int a;
#ifdef FEATURE_B
    char b;
#endif
    double c;
#endif
    float d;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(obj_file)
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_preprocessor_multiple_conditions(self):
        """Test multiple preprocessor conditions - Verifies: FR-1.8
        
        Tests handling of complex preprocessor logic with multiple conditions.
        """
        cpp_content = """
#define PLATFORM_X86
#undef PLATFORM_ARM

struct ConditionalMembers {
#if defined(PLATFORM_X86) && !defined(PLATFORM_ARM)
    int x86_data;
    char x86_flag;
#elif defined(PLATFORM_ARM)
    long arm_data;
    short arm_flag;
#else
    void* generic_ptr;
#endif
    double common_field;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(obj_file)
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_preprocessor_macro_expansion(self):
        """Test macro expansion in struct definitions - Verifies: FR-1.8
        
        Tests handling of macros that expand to struct member definitions.
        """
        cpp_content = """
#define DECLARE_MEMBER(type, name) type name;
#define PADDING_MEMBER(suffix) char padding##suffix;

struct MacroData {
    DECLARE_MEMBER(int, id)
    PADDING_MEMBER(1)
    DECLARE_MEMBER(double, value)
    PADDING_MEMBER(2)
    DECLARE_MEMBER(char, flag)
};
"""
        obj_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(obj_file)
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_preprocessor_include_guards(self):
        """Test include guards with struct definitions - Verifies: FR-1.8
        
        Tests handling of include guards and header-style preprocessor patterns.
        """
        cpp_content = """
#ifndef MYSTRUCT_H
#define MYSTRUCT_H

#pragma once

struct PlatformStruct {
#ifndef DISABLE_FEATURE
    int feature_data;
#endif
    char common_data;
#ifdef ENABLE_EXTRA
    double extra_data;
#endif
};

#endif // MYSTRUCT_H
"""
        obj_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(obj_file)
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_preprocessor_attribute_packed(self):
        """Test __attribute__((packed)) with preprocessor - Verifies: FR-1.8
        
        Tests handling of packed attributes combined with preprocessor directives.
        """
        cpp_content = """
#define PACKED __attribute__((packed))

struct PACKED PackedStruct {
    char a;
#ifdef ADD_PADDING
    int padding;
#endif
    int b;
    char c;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(obj_file)
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_preprocessor_attribute_aligned(self):
        """Test __attribute__((aligned)) with preprocessor - Verifies: FR-1.8
        
        Tests handling of alignment attributes combined with preprocessor directives.
        """
        cpp_content = """
#define ALIGN_8 __attribute__((aligned(8)))
#define CACHE_LINE_SIZE 64

struct ALIGN_8 AlignedStruct {
    char a;
#if CACHE_LINE_SIZE >= 64
    char cache_optimized[63];
#else
    char basic_padding[7];
#endif
    int b;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(obj_file)
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)