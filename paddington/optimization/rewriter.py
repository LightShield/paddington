"""Source code rewriting utilities."""

from typing import List, Dict, Optional
import re
from ..core import StructInfo, MemberInfo
from ..utils import Logger


def find_struct_start_line(lines: List[str], struct_line: int) -> int:
    """Find the line where struct/class keyword appears.

    Args:
        lines: Source file lines
        struct_line: Line number from libclang (1-indexed)

    Returns:
        0-indexed line number where struct/class keyword is found
    """
    struct_start = struct_line - 1
    while (
        struct_start > 0
        and "struct" not in lines[struct_start]
        and "class" not in lines[struct_start]
    ):
        struct_start -= 1
    return struct_start


def find_opening_brace(lines: List[str], start_line: int) -> Optional[int]:
    """Find opening brace of struct/class definition.

    Args:
        lines: Source file lines
        start_line: Line to start searching from

    Returns:
        Line number of opening brace, or None if not found
    """
    brace_line = start_line
    while brace_line < len(lines) and "{" not in lines[brace_line]:
        brace_line += 1

    return brace_line if brace_line < len(lines) else None


def find_closing_brace(lines: List[str], opening_brace_line: int) -> Optional[int]:
    """Find matching closing brace.

    Args:
        lines: Source file lines
        opening_brace_line: Line number of opening brace

    Returns:
        Line number after closing brace, or None if not found
    """
    closing_brace = opening_brace_line + 1
    brace_count = 1

    while closing_brace < len(lines) and brace_count > 0:
        if "{" in lines[closing_brace]:
            brace_count += 1
        if "}" in lines[closing_brace]:
            brace_count -= 1
        closing_brace += 1

    return closing_brace if brace_count == 0 else None


def rewrite_struct_definition(
    file_path: str, struct: StructInfo, new_order: List[MemberInfo]
) -> str:
    """Rewrite struct definition with new member order."""
    log = Logger()

    with open(file_path, "r") as f:
        lines = f.readlines()

    # Find struct boundaries
    struct_start = find_struct_start_line(lines, struct.line)
    brace_line = find_opening_brace(lines, struct_start)

    if brace_line is None:
        log.error(f"Could not find opening brace for struct {struct.name}")
        return "".join(lines)

    closing_brace = find_closing_brace(lines, brace_line)

    if closing_brace is None:
        log.error(f"Could not find closing brace for struct {struct.name}")
        return "".join(lines)

    # Extract member declarations with their access specifiers
    # Track which access specifier each member belongs to
    member_lines = {}
    member_access = {}  # member_name -> access_specifier
    current_access = None  # Track current access level
    other_lines = []
    other_access = {}  # line_index -> access_specifier for non-members

    # Track if we're inside a function/constructor body
    in_function_body = False
    brace_depth = 0

    for i in range(brace_line + 1, closing_brace - 1):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            continue

        # Track braces to detect function bodies
        if "{" in line:
            brace_depth += line.count("{")
            if brace_depth > 0:
                in_function_body = True
        if "}" in line:
            brace_depth -= line.count("}")
            if brace_depth == 0:
                in_function_body = False

        # Check for access specifiers
        if stripped in ["public:", "private:", "protected:"]:
            current_access = stripped
            continue

        # Check if this is a member declaration (only outside function bodies)
        is_member = False
        if not in_function_body:
            for member in struct.members:
                # Look for member name followed by semicolon
                # Must be a declaration, not an assignment
                if re.search(rf"\b{member.type_name}\s+{member.name}\b.*;", line):
                    member_lines[member.name] = line
                    member_access[member.name] = current_access
                    is_member = True
                    break

        # If not a member, it's a constructor/method/comment
        if not is_member:
            other_lines.append(line)
            other_access[len(other_lines) - 1] = current_access

    # Build new struct body preserving access control
    # Group members by access specifier while maintaining optimal order
    new_body = []

    # Group members by access specifier
    access_groups: Dict[Optional[str], List[MemberInfo]] = {}
    for member in new_order:
        if member.name in member_lines:
            access = member_access.get(member.name)
            if access not in access_groups:
                access_groups[access] = []
            access_groups[access].append(member)

    # Group other lines by access specifier
    other_groups: Dict[Optional[str], List[str]] = {}
    for idx, line in enumerate(other_lines):
        access = other_access.get(idx)
        if access not in other_groups:
            other_groups[access] = []
        other_groups[access].append(line)

    # Output in order: preserve the original access specifier order
    seen_access: List[Optional[str]] = []
    for member in struct.members:
        access = member_access.get(member.name)
        if access and access not in seen_access:
            seen_access.append(access)

    # Add None (no access specifier) at the beginning if it exists
    if None in access_groups or None in other_groups:
        if None not in seen_access:
            seen_access.insert(0, None)

    for access in seen_access:
        # Add access specifier
        if access:
            new_body.append(f"{access}\n")

        # Add members in optimal order
        if access in access_groups:
            for member in access_groups[access]:
                new_body.append(member_lines[member.name])

        # Add methods/constructors for this access level
        if access in other_groups:
            if access in access_groups:
                new_body.append("\n")
            new_body.extend(other_groups[access])

    # Reconstruct file
    new_lines = lines[: brace_line + 1] + new_body + lines[closing_brace - 1 :]

    return "".join(new_lines)


def find_constructor_initializers(content: str, struct_name: str) -> List[tuple]:
    """Find constructor initializer lists for a struct."""
    # Pattern: StructName(...) : member1(...), member2(...) {}
    pattern = rf"{struct_name}\s*\([^)]*\)\s*:\s*([^{{]+)\{{"
    matches = []

    for match in re.finditer(pattern, content, re.MULTILINE):
        init_list = match.group(1)
        start = match.start(1)
        end = match.end(1)
        matches.append((start, end, init_list))

    return matches


def reorder_initializer_list(init_list: str, new_order: List[MemberInfo]) -> str:
    """Reorder constructor initializer list to match new member order.

    Preserves base class initializers (e.g., Base(x, y)) at the beginning.
    """
    # Parse initializers: member(value) or member{value}
    initializers = {}
    base_class_inits = []  # Store base class initializers
    member_names = {m.name for m in new_order}

    # Split by comma, handling nested parentheses
    parts = []
    current: List[str] = []
    depth = 0

    for char in init_list:
        if char in "({":
            depth += 1
        elif char in ")}":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
            continue
        current.append(char)

    if current:
        parts.append("".join(current).strip())

    # Extract member name and initialization
    for part in parts:
        match = re.match(r"(\w+)\s*[\(\{]", part)
        if match:
            name = match.group(1)
            # Check if this is a member or base class initializer
            if name in member_names:
                initializers[name] = part
            else:
                # Likely a base class initializer
                base_class_inits.append(part)

    # Rebuild: base class initializers first, then reordered members
    new_inits = base_class_inits.copy()
    for member in new_order:
        if member.name in initializers:
            new_inits.append(initializers[member.name])

    return ", ".join(new_inits)


def rewrite_constructors(
    file_path: str, struct: StructInfo, new_order: List[MemberInfo]
) -> str:
    """Rewrite constructor initializer lists."""
    with open(file_path, "r") as f:
        content = f.read()

    matches = find_constructor_initializers(content, struct.name)

    # Process matches in reverse order to maintain offsets
    for start, end, init_list in reversed(matches):
        new_init_list = reorder_initializer_list(init_list, new_order)
        content = content[:start] + new_init_list + content[end:]

    return content


def write_file(file_path: str, content: str):
    """Write content to file."""
    with open(file_path, "w") as f:
        f.write(content)
