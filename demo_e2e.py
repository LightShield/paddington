#!/usr/bin/env python3
"""Demo script showing e2e test input/output."""

import subprocess
import tempfile
from pathlib import Path

print("=" * 80)
print("E2E TEST DEMO: Simple Struct Optimization")
print("=" * 80)

# INPUT: C++ code with padding waste
cpp_code = """
struct Simple {
    char a;      // 1 byte
    int b;       // 4 bytes (needs 4-byte alignment, so 3 bytes padding before)
    char c;      // 1 byte
};

int main() {
    Simple s;
    return 0;
}
"""

print("\n📝 INPUT C++ CODE:")
print(cpp_code)

# Create temp directory
with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = Path(tmpdir)
    
    # Write source file
    cpp_file = tmpdir / "test.cpp"
    cpp_file.write_text(cpp_code)
    print(f"\n📁 Source file: {cpp_file}")
    
    # Compile with debug info
    obj_file = tmpdir / "test.o"
    print(f"\n🔨 Compiling: g++ -g -c {cpp_file} -o {obj_file}")
    result = subprocess.run(
        ['g++', '-g', '-c', str(cpp_file), '-o', str(obj_file)],
        capture_output=True
    )
    
    if result.returncode != 0:
        print(f"❌ Compilation failed: {result.stderr.decode()}")
        exit(1)
    
    print(f"✅ Compiled successfully")
    
    # Check struct size with dwarfdump
    print(f"\n🔍 Checking struct size with dwarfdump...")
    result = subprocess.run(
        ['dwarfdump', str(obj_file)],
        capture_output=True,
        text=True
    )
    
    # Extract size from DWARF
    for line in result.stdout.split('\n'):
        if 'DW_TAG_structure_type' in line or 'DW_AT_name' in line or 'DW_AT_byte_size' in line:
            if 'Simple' in line or 'byte_size' in line:
                print(f"  {line.strip()}")
    
    # Run paddingTON analyze (dry-run)
    print(f"\n🔧 Running paddingTON (dry-run):")
    print(f"   python __main__.py {obj_file} --extractor dwarf -vv")
    result = subprocess.run(
        ['python', '__main__.py', str(obj_file), '--extractor', 'dwarf', '-vv'],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )
    
    print(f"\n📊 OUTPUT:")
    print(result.stdout)
    
    if result.returncode != 0:
        print(f"\n❌ Error: {result.stderr}")
    else:
        print(f"\n✅ Command succeeded (exit code: {result.returncode})")
    
    # Generate patches
    patch_dir = tmpdir / "patches"
    print(f"\n📦 Generating patches:")
    print(f"   python __main__.py {obj_file} --output patch --patch-dir {patch_dir}")
    result = subprocess.run(
        ['python', '__main__.py', str(obj_file), '--output', 'patch', '--patch-dir', str(patch_dir)],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )
    
    print(f"\n📊 OUTPUT:")
    print(result.stdout)
    
    # Show generated patches
    if patch_dir.exists():
        patches = list(patch_dir.glob("*.patch"))
        if patches:
            print(f"\n📄 Generated patches:")
            for patch in patches:
                print(f"   {patch.name}")
                print(f"\n   Content:")
                print("   " + "\n   ".join(patch.read_text().split('\n')[:20]))
        else:
            print(f"\n⚠️  No patches generated (struct may already be optimal or extraction failed)")
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
