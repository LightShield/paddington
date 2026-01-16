# Pipeline Stages Explained in Detail

## Overview

The paddingTON pipeline transforms compiled object files into optimized source code through 5 distinct stages. Each stage has a single responsibility and clear input/output contracts.

---

## Stage 1: EXTRACTION

**Purpose**: Extract struct layout information from compiled object files

**Input**: `List[Path]` - Paths to `.o` files compiled with `-g` debug flag

**Output**: `List[StructInfo]` - Structured data about each struct found

**What it does**:
1. Reads DWARF debug information from object files
2. Finds all struct/class definitions
3. For each struct, extracts:
   - Struct name (e.g., "UserData")
   - Total size in bytes (e.g., 24)
   - Each member's name, type, size, and byte offset
   - Source file location (file path and line number)
4. Deduplicates structs found in multiple object files

**Example**:

```cpp
// Source: user.h:10
struct UserData {
    char flag;    // offset 0, size 1
    int id;       // offset 4, size 4 (3 bytes padding before)
    double score; // offset 8, size 8
};
// Total size: 16 bytes
```

Becomes:

```python
StructInfo(
    name="UserData",
    size=16,
    members=[
        MemberInfo(name="flag", type="char", size=1, offset=0),
        MemberInfo(name="id", type="int", size=4, offset=4),
        MemberInfo(name="score", type="double", size=8, offset=8),
    ],
    file_path="/path/to/user.h",
    line=10
)
```

**Why this stage exists**: We need accurate struct layouts to calculate padding. The compiler has already done the hard work of resolving types, templates, and alignment. We just extract what it knows.

**Provider implementations**:
- **PaholeExtractor**: Calls `pahole` command-line tool (fast, native C)
- **DwarfExtractor**: Uses pyelftools library (slow, pure Python)
- **MockExtractor**: Returns hardcoded data (for testing)

---

## Stage 2: ANALYSIS (ITERATIVE)

**Purpose**: Analyze structs to identify optimization opportunities IN DEPENDENCY ORDER

**Input**: `List[StructInfo]` - All structs from extraction

**Output**: `List[OptimizationPlan]` - Which structs to optimize and why, in bottom-up order

**CRITICAL**: This stage is **iterative**, not single-pass. Each struct's analysis uses the optimized sizes of its dependencies.

**What it does**:

### Step 1: Build Dependency Graph (One-Time)
```python
# Identify which structs contain other structs as members
graph = {}
for struct in structs:
    deps = set()
    for member in struct.members:
        if member.type in all_struct_names:
            deps.add(member.type)
    graph[struct.name] = deps

# Example:
# graph = {
#     "Inner": set(),           # No dependencies (leaf)
#     "Outer": {"Inner"},       # Depends on Inner
#     "Container": {"Outer"},   # Depends on Outer
# }
```

### Step 2: Topological Sort (One-Time)
```python
# Order structs so dependencies come before dependents
# Uses DFS with visited tracking
ordered = topological_sort(graph)

# Result: ["Inner", "Outer", "Container"]
# Guarantees: Inner is analyzed before Outer, Outer before Container
```

### Step 3: Iterative Analysis (Main Loop)

**Key insight**: We must analyze structs in dependency order and update sizes as we go.

```python
# Initialize global type size table with original sizes
type_sizes = {s.name: s.size for s in structs}
plans = []

for struct_name in ordered:
    struct = find_struct(struct_name)
    
    # 3a. UPDATE member sizes using current type table
    # This is critical! Members may reference previously optimized structs
    updated_members = []
    for member in struct.members:
        if member.type in type_sizes:
            # Use potentially updated size from previous optimizations
            updated_size = type_sizes[member.type]
            updated_member = MemberInfo(
                name=member.name,
                type=member.type,
                size=updated_size,  # ← May differ from original!
                offset=member.offset
            )
            updated_members.append(updated_member)
        else:
            updated_members.append(member)
    
    # 3b. RECALCULATE struct size with updated member sizes
    # Original DWARF size may be wrong if dependencies were optimized
    actual_size = calculate_struct_size(updated_members)
    
    # 3c. CALCULATE padding with updated sizes
    padding = calculate_padding(updated_members, actual_size)
    
    # 3d. DETERMINE if optimization is beneficial
    should_opt, skip_reason = should_optimize(
        struct=struct,
        padding=padding,
        members=updated_members
    )
    
    # 3e. CREATE optimization plan
    if should_opt:
        optimal_order = sort_members_by_size_descending(updated_members)
        optimized_size = calculate_struct_size(optimal_order)
        
        plan = OptimizationPlan(
            struct=struct,
            original_order=tuple(updated_members),
            optimal_order=tuple(optimal_order),
            padding_saved=actual_size - optimized_size,
            skip_reason=None
        )
    else:
        plan = OptimizationPlan(
            struct=struct,
            original_order=tuple(updated_members),
            optimal_order=tuple(updated_members),
            padding_saved=0,
            skip_reason=skip_reason
        )
    
    plans.append(plan)
    
    # 3f. UPDATE global type table with new size
    # Next structs that depend on this one will use the updated size
    if should_opt:
        type_sizes[struct_name] = optimized_size
    else:
        type_sizes[struct_name] = actual_size

# Return plans in dependency order (leaves first)
return plans
```

### Example: Why Iteration Matters

**Scenario**: `Outer` contains `Inner` as a member

```cpp
// Original (from DWARF)
struct Inner {
    char a;    // offset 0, size 1
    int b;     // offset 4, size 4 (3 bytes padding before)
    char c;    // offset 8, size 1
};
// Size: 12 bytes, Padding: 6 bytes

struct Outer {
    char x;      // offset 0, size 1
    Inner inner; // offset 4, size 12 (3 bytes padding before)
    int y;       // offset 16, size 4
};
// Size: 20 bytes, Padding: 3 bytes
```

**Iteration 1: Analyze Inner**
```python
# Initial type_sizes = {"Inner": 12, "Outer": 20}

struct = Inner
members = [char a (1), int b (4), char c (1)]
padding = 6 bytes

# Optimize: reorder to [int b, char a, char c]
optimized_size = 8 bytes  # int(4) + char(1) + char(1) + pad(2)

# Update type table
type_sizes["Inner"] = 8  # ← Changed from 12!

plan = OptimizationPlan(
    struct=Inner,
    optimal_order=[int b, char a, char c],
    padding_saved=4  # 12 - 8
)
```

**Iteration 2: Analyze Outer**
```python
# Current type_sizes = {"Inner": 8, "Outer": 20}

struct = Outer
members = [char x (1), Inner inner (12), int y (4)]  # Original sizes

# UPDATE member sizes from type table
updated_members = [
    char x (1),
    Inner inner (8),  # ← Updated from 12 to 8!
    int y (4)
]

# RECALCULATE Outer's actual size
actual_size = 1 + 3(pad) + 8 + 4 = 16 bytes  # Not 20!

# Calculate padding with updated sizes
padding = 3 bytes  # Only padding before Inner

# Optimize: reorder to [Inner inner, int y, char x]
optimized_size = 8 + 4 + 1 + 3(pad) = 16 bytes

# No savings! Already optimal after Inner optimization
type_sizes["Outer"] = 16

plan = OptimizationPlan(
    struct=Outer,
    optimal_order=[Inner inner, int y, char x],
    padding_saved=0,  # Already optimal
    skip_reason="no additional savings"
)
```

**Without iteration**: We'd analyze `Outer` with `Inner=12`, calculate wrong padding, make wrong decisions.

**With iteration**: We analyze `Outer` with `Inner=8`, get correct padding, make correct decisions.

**Why this stage exists**: Struct optimization is not independent. A struct's optimal layout depends on the optimized sizes of its member types. This stage ensures we make decisions based on actual post-optimization sizes, not original DWARF sizes.

**Key algorithms**:
- **Dependency graph**: Track which structs contain other structs
- **Topological sort**: Ensure leaves are analyzed before parents
- **Iterative size updates**: Propagate optimized sizes through dependency chain
- **Padding recalculation**: Use updated sizes for accurate padding analysis

---

## Stage 3: PLANNING

**Purpose**: Convert optimization plans into concrete source code modifications

**Input**: `List[OptimizationPlan]` - What to optimize

**Output**: `List[SourceModification]` - Exactly how to modify source files

**What it does**:
1. **For each optimization plan**, determine what needs to change:
   
   a. **Struct definition** - Reorder member declarations
   b. **Constructor initializer lists** - Reorder to match new member order
   c. **Aggregate initializations** - Reorder values in `{...}` syntax
   d. **Smart pointer calls** - Reorder arguments in `make_unique<T>(...)`

2. **Create modification instructions** for each change:
   - Type of modification (reorder_member, reorder_initializer, etc.)
   - Location (file, line, column)
   - Old content vs new content
   - Context (surrounding code for validation)

3. **Group modifications by file**:
   - Multiple structs in same file → single SourceModification
   - Ensures we don't modify same file multiple times

**Example**:

```python
# Input: OptimizationPlan for UserData

# Output:
SourceModification(
    file_path="/path/to/user.h",
    struct_name="UserData",
    modifications=[
        # 1. Reorder struct members
        Modification(
            type="reorder_member",
            location=Location(file="user.h", line=11),
            old_content="    char flag;\n    int id;\n    double score;",
            new_content="    double score;\n    int id;\n    char flag;",
        ),
        
        # 2. Reorder constructor initializer list
        Modification(
            type="reorder_initializer",
            location=Location(file="user.h", line=15),
            old_content="UserData(char f, int i, double s) : flag(f), id(i), score(s) {}",
            new_content="UserData(char f, int i, double s) : score(s), id(i), flag(f) {}",
        ),
        
        # 3. Reorder aggregate initialization in user.cpp
        Modification(
            type="reorder_aggregate",
            location=Location(file="user.cpp", line=42),
            old_content='UserData data = {\'A\', 123, 3.14};',
            new_content='UserData data = {3.14, 123, \'A\'};',
        ),
    ]
)
```

**Why this stage exists**: The transformation stage (next) doesn't know about C++ semantics. It just manipulates source code. This stage provides the "intelligence" - it knows that if you reorder struct members, you must also reorder initializer lists to match.

**Key decisions**:
- **Constructor signatures unchanged**: Too risky to change parameter order (breaks all call sites)
- **Initializer lists must match member order**: C++ requirement
- **Aggregate initializations must match member order**: C++ requirement

---

## Stage 4: TRANSFORMATION

**Purpose**: Apply modifications to source code files

**Input**: `List[SourceModification]` - What to change

**Output**: `List[TransformedSource]` - Original and new file contents

**What it does**:
1. **Read source file** from disk
2. **Parse source code** into manipulable format
3. **Apply each modification**:
   - Find the target location (struct, constructor, etc.)
   - Make the change (reorder, replace, etc.)
   - Validate the change (syntax check)
4. **Generate new source code** from modified format
5. **Return both versions** (original + new) for comparison

**Provider implementations**:

### A. SrcMLTransformer (Recommended)

Uses srcML tool to convert source ↔ XML:

```bash
# Source to XML
srcml user.h > user.xml

# XML structure
<struct>
  <name>UserData</name>
  <block>
    <decl><type>char</type> <name>flag</name>;</decl>
    <decl><type>int</type> <name>id</name>;</decl>
    <decl><type>double</type> <name>score</name>;</decl>
  </block>
</struct>

# Reorder <decl> nodes in XML

# XML back to source
srcml user.xml > user_new.h
```

**Advantages**:
- Preserves all formatting (whitespace, comments, indentation)
- Understands C++ syntax (handles templates, macros, etc.)
- Round-trip transformation (source → XML → source) is lossless
- Can manipulate AST nodes directly

**Process**:
1. Convert source file to srcML XML
2. Parse XML with ElementTree
3. Find struct node by name
4. Find member declaration nodes
5. Reorder nodes according to modifications
6. Convert XML back to source
7. Return new source code

### B. LineSwapTransformer (Current, Fallback)

Simple line-based rewriting:

```python
# 1. Read file into lines
lines = file.readlines()

# 2. Find struct boundaries
struct_start = find_line_with("struct UserData")
struct_end = find_matching_brace(struct_start)

# 3. Find member lines
member_lines = {
    "flag": 11,  # Line 11: char flag;
    "id": 12,    # Line 12: int id;
    "score": 13, # Line 13: double score;
}

# 4. Swap lines
lines[11], lines[13] = lines[13], lines[11]  # Swap flag and score

# 5. Write back
file.write(lines)
```

**Advantages**:
- Simple, no external dependencies
- Fast for simple cases

**Disadvantages**:
- Fragile (breaks on multi-line declarations)
- Doesn't understand C++ syntax
- Can't handle complex cases (templates, macros)
- May break formatting

**Why this stage exists**: Different projects have different needs. Some want perfect formatting preservation (srcML), others want speed and simplicity (line swap). The provider pattern lets you choose.

---

## Stage 5: APPLICATION

**Purpose**: Write transformed source code to disk or generate patches

**Input**: `List[TransformedSource]` - New file contents

**Output**: `List[AppliedChange]` - What was actually changed

**What it does**:
1. **Validate changes**:
   - Ensure new content is valid C++
   - Check that file is writable
   - Verify no conflicts with other changes

2. **Apply changes** (provider-specific):
   - **FileWriter**: Directly overwrite source files
   - **PatchGenerator**: Create git patches for review

3. **Record what changed**:
   - File path
   - Lines modified
   - Bytes changed
   - Timestamp

**Provider implementations**:

### A. DirectFileWriter

```python
def apply(self, transformed: List[TransformedSource]) -> List[AppliedChange]:
    results = []
    for t in transformed:
        # Backup original
        backup_path = f"{t.file_path}.backup"
        shutil.copy(t.file_path, backup_path)
        
        # Write new content
        with open(t.file_path, 'w') as f:
            f.write(t.new_content)
        
        results.append(AppliedChange(
            file_path=t.file_path,
            backup_path=backup_path,
            lines_changed=count_diff_lines(t.original_content, t.new_content),
            timestamp=datetime.now()
        ))
    
    return results
```

**Use case**: Quick iteration, local development

### B. GitPatchGenerator

```python
def apply(self, transformed: List[TransformedSource]) -> List[AppliedChange]:
    results = []
    for t in transformed:
        # Create temp file with new content
        temp_path = f"/tmp/{Path(t.file_path).name}"
        with open(temp_path, 'w') as f:
            f.write(t.new_content)
        
        # Generate git diff
        diff = subprocess.run(
            ['git', 'diff', '--no-index', t.file_path, temp_path],
            capture_output=True,
            text=True
        ).stdout
        
        # Write patch file
        patch_path = f"patches/{t.struct_name}.patch"
        with open(patch_path, 'w') as f:
            f.write(diff)
        
        # Write commit message
        msg_path = f"patches/{t.struct_name}.msg"
        with open(msg_path, 'w') as f:
            f.write(f"refactor: Optimize padding for {t.struct_name}\n\n")
            f.write(f"Reorder members to minimize padding.\n")
            f.write(f"Saves {t.padding_saved} bytes per instance.\n")
        
        results.append(AppliedChange(
            file_path=t.file_path,
            patch_path=patch_path,
            message_path=msg_path,
            timestamp=datetime.now()
        ))
    
    return results
```

**Use case**: Code review, incremental adoption, team collaboration

**Why this stage exists**: Different workflows need different outputs. Some developers want immediate changes (file writer), others want reviewable patches (patch generator). Some want dry-run reports, others want CI/CD integration.

---

## Complete Pipeline Flow Example

### Input: Compiled object file

```bash
# user.o compiled from user.h + user.cpp with -g flag
```

### Stage 1: EXTRACTION

```python
# Extract struct info from user.o
structs = extractor.extract([Path("user.o")])

# Result:
[
    StructInfo(
        name="UserData",
        size=16,
        members=[
            MemberInfo(name="flag", type="char", size=1, offset=0),
            MemberInfo(name="id", type="int", size=4, offset=4),
            MemberInfo(name="score", type="double", size=8, offset=8),
        ],
        file_path="/src/user.h",
        line=10
    )
]
```

### Stage 2: ANALYSIS

```python
# Analyze padding and create optimization plan
plans = analyzer.analyze(structs)

# Result:
[
    OptimizationPlan(
        struct=structs[0],
        original_order=[flag, id, score],
        optimal_order=[score, id, flag],  # Largest to smallest
        padding_saved=3,  # 3 bytes of internal padding eliminated
        skip_reason=None
    )
]
```

### Stage 3: PLANNING

```python
# Create concrete modification instructions
modifications = planner.plan(plans)

# Result:
[
    SourceModification(
        file_path="/src/user.h",
        struct_name="UserData",
        modifications=[
            Modification(type="reorder_member", ...),
            Modification(type="reorder_initializer", ...),
        ]
    ),
    SourceModification(
        file_path="/src/user.cpp",
        struct_name="UserData",
        modifications=[
            Modification(type="reorder_aggregate", ...),
        ]
    )
]
```

### Stage 4: TRANSFORMATION

```python
# Apply modifications using srcML
transformed = transformer.transform(modifications)

# Result:
[
    TransformedSource(
        file_path="/src/user.h",
        original_content="struct UserData {\n    char flag;\n    int id;\n    double score;\n};",
        new_content="struct UserData {\n    double score;\n    int id;\n    char flag;\n};",
        modifications=[...]
    ),
    TransformedSource(
        file_path="/src/user.cpp",
        original_content="UserData data = {'A', 123, 3.14};",
        new_content="UserData data = {3.14, 123, 'A'};",
        modifications=[...]
    )
]
```

### Stage 5: APPLICATION

```python
# Generate git patches
applied = applicator.apply(transformed)

# Result:
[
    AppliedChange(
        file_path="/src/user.h",
        patch_path="patches/UserData.patch",
        message_path="patches/UserData.msg",
        timestamp=datetime(2026, 1, 16, 12, 0, 0)
    ),
    AppliedChange(
        file_path="/src/user.cpp",
        patch_path="patches/UserData_cpp.patch",
        message_path="patches/UserData_cpp.msg",
        timestamp=datetime(2026, 1, 16, 12, 0, 0)
    )
]
```

### Output: Git patches ready for review

```bash
patches/
├── APPLY_ORDER.txt
├── UserData.patch
├── UserData.msg
├── UserData_cpp.patch
└── UserData_cpp.msg
```

---

## Why This Pipeline Design?

### 1. Separation of Concerns
Each stage has one job:
- Extraction: Get data from binaries
- Analysis: Make decisions
- Planning: Specify changes
- Transformation: Modify source
- Application: Write results

### 2. Testability
Each stage can be tested independently:
- Mock the input
- Verify the output
- No need for real files or tools

### 3. Flexibility
Swap implementations without changing pipeline:
- Use pahole or DWARF for extraction
- Use srcML or line-swap for transformation
- Use file-writer or patch-generator for application

### 4. Parallelizability
Stages can process multiple items in parallel:
- Extract 100 object files concurrently
- Transform 50 source files concurrently
- Generate 50 patches concurrently

### 5. Debuggability
Inspect data between stages:
- Save extraction results to JSON
- Review optimization plans before applying
- Validate transformations before writing

### 6. Extensibility
Add new stages without breaking existing ones:
- Add "Validation" stage after Transformation
- Add "Backup" stage before Application
- Add "Metrics" stage after Application

---

## Key Takeaways

1. **Extraction** = "What does the compiler know?"
2. **Analysis** = "What should we optimize?"
3. **Planning** = "How do we change the code?"
4. **Transformation** = "Make the changes"
5. **Application** = "Save the results"

Each stage is:
- **Independent**: Can be developed and tested separately
- **Swappable**: Multiple implementations via providers
- **Composable**: Stages connect via well-defined interfaces
- **Testable**: Clear inputs and outputs
