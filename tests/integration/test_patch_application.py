"""Test that generated patches are valid and can be applied."""

import pytest
import subprocess
from pathlib import Path


@pytest.mark.integration
def test_patches_can_be_applied():
    """Test that all generated patches can be applied to a clean repo."""
    # This test should be run manually after generating patches
    patch_dir = Path("/tmp/patches_final")
    
    if not patch_dir.exists():
        pytest.skip("No patches to test - run paddington first")
    
    patches = list(patch_dir.glob("*.patch"))
    if not patches:
        pytest.skip("No patch files found")
    
    # Try to apply patches (dry-run)
    model_dir = Path("/rdata/dub/verif/ormagen/model_4/model")
    if not model_dir.exists():
        pytest.skip("Model directory not found")
    
    # Check if patches are already applied
    result = subprocess.run(
        ['git', 'diff', '--quiet'],
        cwd=model_dir,
        capture_output=True
    )
    if result.returncode != 0:
        pytest.skip("Patches already applied or repo has changes")
    
    failed_patches = []
    for patch in patches:
        result = subprocess.run(
            ['git', 'apply', '--check', str(patch)],
            cwd=model_dir,
            capture_output=True
        )
        if result.returncode != 0:
            failed_patches.append((patch.name, result.stderr.decode()))
    
    assert len(failed_patches) == 0, \
        f"{len(failed_patches)} patches failed to apply:\n" + \
        "\n".join(f"  {name}: {err[:100]}" for name, err in failed_patches[:5])


@pytest.mark.integration  
def test_patch_count_reasonable():
    """Test that we generated a reasonable number of patches."""
    patch_dir = Path("/tmp/patches_final")
    
    if not patch_dir.exists():
        pytest.skip("No patches to test")
    
    patches = list(patch_dir.glob("*.patch"))
    
    # Should have generated patches (not 0)
    assert len(patches) > 0, "No patches generated"
    
    # Should have generated a reasonable number (not too few)
    assert len(patches) >= 100, \
        f"Only {len(patches)} patches generated - expected more with all fixes"
