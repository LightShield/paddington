# paddingTON

**padding Trimming Optimization eNgine**

A C++ refactoring tool that detects and eliminates redundant padding in structs/classes by reordering members from largest to smallest, while automatically updating constructors and all call sites.

## Dependencies

- Python 3.7+
- libclang
- [logger_python](https://github.com/LightShield/logger_python) - Structured logging

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Analyze

```bash
python -m paddington analyze <path> [-v|-vv|-vvv]
```

Verbosity levels:
- `-v` (default): Show structs with padding waste
- `-vv`: Add location, optimal size, and member details
- `-vvv`: Debug mode with file parsing details

### Optimize (coming soon)

```bash
python -m paddington optimize <path> [options]
```
