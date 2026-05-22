# logslice

Fast log filtering and aggregation utility with regex and time-range support.

---

## Installation

```bash
pip install logslice
```

Or install from source:

```bash
git clone https://github.com/youruser/logslice.git && cd logslice && pip install .
```

---

## Usage

```bash
# Filter logs by regex pattern
logslice filter --pattern "ERROR|WARN" app.log

# Filter logs within a time range
logslice filter --start "2024-01-15 08:00:00" --end "2024-01-15 09:00:00" app.log

# Aggregate log levels and count occurrences
logslice aggregate --by level app.log

# Combine regex and time-range filtering
logslice filter --pattern "timeout" --start "2024-01-15 08:00:00" app.log
```

### Python API

```python
from logslice import LogSlicer

slicer = LogSlicer("app.log")
results = slicer.filter(pattern=r"ERROR", start="2024-01-15 08:00:00")

for entry in results:
    print(entry)
```

---

## Features

- ⚡ Fast regex-based log filtering
- 🕐 Time-range filtering with flexible timestamp parsing
- 📊 Log aggregation and frequency counting
- 📂 Supports plain text, gzipped, and rotated log files
- 🔧 Simple CLI and Python API

---

## License

This project is licensed under the [MIT License](LICENSE).