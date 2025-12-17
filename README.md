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

# compile: python3 j-=2.py .\examples\<classname>.j-=2 --ast
# run: java -cp out <program_name>  (runs out/<program_name>.class)


# Hex dump / hex view of .class files

# Windows (PowerShell)
#   Format-Hex <program_name>.class

# Windows (CMD)
#   certutil -dump <program_name>.class

# Linux / macOS
#   hexdump -C <program_name>.class

# View the textual JVM bytecode
# javap -c -classpath out <program_name>
```

## Third-party notice

This repository bundles `jasmin.jar`, the Jasmin Java bytecode assembler.

Jasmin is a separate project distributed under a permissive license.

- Project homepage: https://sourceforge.net/projects/jasmin/
- Jasmin is used unchanged and only for assembling generated `.j` files into `.class` files.

All rights and credit for Jasmin belong to its original authors.
