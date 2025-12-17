# J-=2 compiler
Educational compiler for a tiny language, targeting Jasmin assembly and Java bytecode on the JVM.

```
# install python, jdk and jasmin
# https://adoptium.net/temurin/releases/
# https://sourceforge.net/projects/jasmin/

# Create a virtual environment (run once)
#   python -m venv venv

# Activate the virtual environment
#   Windows (PowerShell):
#     venv\Scripts\Activate.ps1
#
#   Windows (cmd):
#     venv\Scripts\activate
#
#   Linux / macOS:
#     source venv/bin/activate

# Upgrade pip
#   python -m pip install --upgrade pip

# Install anytree
#   pip install anytree

# compile: python3 j-=2.py .\examples\nesting.j-=2 --ast
# run: java -cp out nesting  (runs out/nesting.class)

# Hex dump of .class files

# Windows (PowerShell)
#   Format-Hex Main.class

# Windows (CMD)
#   certutil -dump Main.class

# Linux / macOS
#   hexdump -C Main.class
```

## Third-party notice

This repository bundles `jasmin.jar`, the Jasmin Java bytecode assembler.

Jasmin is a separate project distributed under a permissive license.

- Project homepage: https://sourceforge.net/projects/jasmin/
- Jasmin is used unchanged and only for assembling generated `.j` files into `.class` files.

All rights and credit for Jasmin belong to its original authors.
