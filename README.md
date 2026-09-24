# decompile-jar

A cross-platform Python script that decompiles JAR files into readable Java source code. Automatically installs Java and the CFR decompiler if they're missing.

## Features

- Decompiles `.jar` and `.class` files to Java source
- Auto-installs a JDK if Java isn't found (Linux, macOS, Windows)
- Auto-downloads CFR decompiler on first run
- Outputs to the current working directory by default
- Optional recursive mode for nested/fat JARs
- No external Python dependencies (uses only the standard library)

## Requirements

- Python 3.6+
- Internet connection on first run (to download CFR, and Java if missing)

Java is installed automatically if not present. If auto-install fails, install a JDK manually from https://adoptium.net/ and re-run.

## Usage

```bash
python decompile_jar.py <file.jar|file.class> [output_dir] [--recursive]
