import os
import sys
from typing import List
import subprocess

import parser as p
from parser import AST

class Codegen:
    def __init__(self):
        self.locals = {}
        self.next_slot = 1  # 0 is args
        self.lines: List[str] = []
        self.max_stack_guess = 32
        self.lbl = 0

    def new_label(self, base="L") -> str:
        self.lbl += 1
        return f"{base}{self.lbl}"

    def slot_of(self, name: str) -> int:
        if name not in self.locals:
            self.locals[name] = self.next_slot
            self.next_slot += 1
        return self.locals[name]

    def emit(self, s: str) -> None:
        self.lines.append(s)

    def emit_iload(self, slot: int) -> None:
        self.emit(f"  iload_{slot}" if 0 <= slot <= 3 else f"  iload {slot}")

    def emit_istore(self, slot: int) -> None:
        self.emit(f"  istore_{slot}" if 0 <= slot <= 3 else f"  istore {slot}")

    def gen_expr(self, node: AST) -> None:
        kind = node[0]

        if kind == "Int":
            v = node[1]
            self.emit(f"  sipush {v}")
            return

        if kind == "Var":
            slot = self.slot_of(node[1])
            self.emit_iload(slot)
            return

        if kind == "Bin":
            op, a, b = node[1], node[2], node[3]
            self.gen_expr(a)
            self.gen_expr(b)
            if op == "PLUS": self.emit("  iadd")
            elif op == "MINUS": self.emit("  isub")
            elif op == "MUL": self.emit("  imul")
            elif op == "DIV": self.emit("  idiv")
            else:
                raise ValueError(f"Unknown binop {op}")
            return

        if kind == "Cmp":
            op, a, b = node[1], node[2], node[3]
            self.gen_expr(a)
            self.gen_expr(b)

            Ltrue = self.new_label("Cmp_true_")
            Lend  = self.new_label("Cmp_end_")

            jmp = {
                "LT":   "if_icmplt",
                "LE":   "if_icmple",
                "GT":   "if_icmpgt",
                "GE":   "if_icmpge",
                "EQEQ": "if_icmpeq",
                "NE":   "if_icmpne",
            }[op]

            self.emit(f"  {jmp} {Ltrue}")
            self.emit("  iconst_0")
            self.emit(f"  goto {Lend}")
            self.emit(f"{Ltrue}:")
            self.emit("  iconst_1")
            self.emit(f"{Lend}:")
            return

        raise ValueError(f"Unknown expr node {node}")

    def gen_stmt(self, node: AST) -> None:
        kind = node[0]

        if kind == "Let":
            _, name, e = node
            self.gen_expr(e)
            slot = self.slot_of(name)
            self.emit_istore(slot)
            return

        if kind == "Print":
            _, e = node
            self.emit("  getstatic java/lang/System/out Ljava/io/PrintStream;")
            self.gen_expr(e)
            self.emit("  invokevirtual java/io/PrintStream/println(I)V")
            return

        if kind == "While":
            _, cond, body = node
            Ltest = self.new_label("Loop_test_")
            Lend  = self.new_label("Loop_end_")

            self.emit(f"{Ltest}:")
            self.gen_expr(cond)
            self.emit(f"  ifeq {Lend}")

            for s in body:
                self.gen_stmt(s)

            self.emit(f"  goto {Ltest}")
            self.emit(f"{Lend}:")
            return

        if kind == "IfChain":
            _, branches, else_block = node
            Lend = self.new_label("If_end_")

            for (cond, block) in branches:
                Lnext = self.new_label("If_next_")
                self.gen_expr(cond)
                self.emit(f"  ifeq {Lnext}")
                for s in block:
                    self.gen_stmt(s)
                self.emit(f"  goto {Lend}")
                self.emit(f"{Lnext}:")

            if else_block is not None:
                for s in else_block:
                    self.gen_stmt(s)

            self.emit(f"{Lend}:")
            return

        raise ValueError(f"Unknown stmt node {node}")

    def gen(self, ast: AST, class_name: str = "Main") -> str:
        self.emit(f".class public {class_name}")
        self.emit(".super java/lang/Object")
        self.emit("")
        self.emit(".method public <init>()V")
        self.emit("  aload_0")
        self.emit("  invokespecial java/lang/Object/<init>()V")
        self.emit("  return")
        self.emit(".end method")
        self.emit("")
        self.emit(".method public static main([Ljava/lang/String;)V")
        self.emit(f"  .limit stack {self.max_stack_guess}")
        self.emit("  .limit locals 64")

        for st in ast[1]:
            self.gen_stmt(st)

        self.emit("  return")
        self.emit(".end method")
        return "\n".join(self.lines)

def compile_to_jasmin(src: str, class_name: str = "Main") -> str:
    ast = p.parse(src)
    return Codegen().gen(ast, class_name=class_name)

def jasmin_to_bytecode(j_file: str, class_name: str):
    out_dir = "out"
    os.makedirs(out_dir, exist_ok=True)
    subprocess.run(
        ["java", "-jar", "../jasmin.jar", f"../{j_file}"],
        cwd=out_dir, # from out/
        check=True
    )
    print(f"Wrote {out_dir}/{class_name}.class")


def main():
    if len(sys.argv) < 2:
        print("usage: j-=2.py <filepath> [--ast]")
        sys.exit(1)

    inp_path = sys.argv[1]
    dump_ast = ("--ast" in sys.argv)

    src = open(inp_path, "r", encoding="utf-8").read()
    cls = os.path.basename(inp_path).rsplit(".")[0]

    ast = p.parse(src)
    if dump_ast:
        p.print_ast(ast)

    out_j = "j/" + cls + ".j"
    jas = Codegen().gen(ast, class_name=cls)

    os.makedirs("j", exist_ok=True)
    with open(out_j, "w", encoding="utf-8", newline="\n") as f:
        f.write(jas)
    # must write utf-8 to .j

    print(f"Wrote {out_j}")

    jasmin_to_bytecode(out_j, cls)
    

if __name__ == "__main__":
    main()

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

# Dissasemble java bytecode to textual java bytecode
# javap -c -classpath out <program_name>
