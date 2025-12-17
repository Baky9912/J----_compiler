import re
from typing import Any, List, Optional, Tuple
from anytree import Node, RenderTree

TOK = [
    ("INT",   r"\d+"),
    ("ID",    r"[A-Za-z_]\w*"),

    ("LE",    r"<="),
    ("GE",    r">="),
    ("EQEQ",  r"=="),
    ("NE",    r"!="),

    ("LT",    r"<"),
    ("GT",    r">"),

    ("EQ",     r"="),
    ("SEMIC",  r";"),
    ("LP",     r"\("),
    ("RP",     r"\)"),
    ("LBR",    r"\{"),
    ("RBR",    r"\}"),

    ("PLUS",  r"\+"),
    ("MINUS", r"-"),
    ("MUL",   r"\*"),
    ("DIV",   r"/"),

    ("WS",    r"[ \t\r\n]+"),
]

TOKEN_REGEX = re.compile("|".join(f"(?P<{n}>{p})" for n, p in TOK))

class Token:
    __slots__ = ("t", "v")
    def __init__(self, t: str, v: str):
        self.t, self.v = t, v
    def __repr__(self) -> str:
        return f"Token({self.t},{self.v})"

def lex(s: str) -> List["Token"]:
    KW = {
        "let": "LET",
        "print": "PRINT",
        "while": "WHILE",
        "if": "IF",
        "else": "ELSE",
    }

    out: List[Token] = []
    for m in TOKEN_REGEX.finditer(s):
        t = m.lastgroup
        v = m.group()
        if t == "WS":
            continue
        if t == "ID" and v in KW:
            t = KW[v]
        out.append(Token(t, v))

    return out + [Token("EOF", "")]

AST = Any

class Parser:
    def __init__(self, toks: List[Token]):
        self.toks = toks
        self.i = 0

    def cur(self) -> Token:
        return self.toks[self.i]

    def eat(self, kind: str) -> None:
        if self.cur().t != kind:
            raise SyntaxError(f"Expected {kind}, got {self.cur().t} ({self.cur().v})")
        self.i += 1

    def program(self) -> AST:
        stmts = []
        while self.cur().t != "EOF":
            stmts.append(self.stmt())
        return ("Program", stmts)

    def block(self) -> List[AST]:
        self.eat("LBR")
        body = []
        while self.cur().t != "RBR":
            body.append(self.stmt())
        self.eat("RBR")
        return body

    def if_stmt(self) -> AST:
        # ("IfChain", [(cond, block), ...], else_block_or_None)
        self.eat("IF")
        self.eat("LP")
        c0 = self.expr()
        self.eat("RP")
        b0 = self.block()

        branches: List[Tuple[AST, List[AST]]] = [(c0, b0)]
        else_block: Optional[List[AST]] = None

        while self.cur().t == "ELSE":
            self.eat("ELSE")
            if self.cur().t == "IF":
                self.eat("IF")
                self.eat("LP")
                c = self.expr()
                self.eat("RP")
                b = self.block()
                branches.append((c, b))
            else:
                else_block = self.block()
                break

        return ("IfChain", branches, else_block)

    def stmt(self) -> AST:
        if self.cur().t == "LET":
            self.eat("LET")
            name = self.cur().v
            self.eat("ID")
            self.eat("EQ")
            e = self.expr()
            self.eat("SEMIC")
            return ("Let", name, e)

        if self.cur().t == "PRINT":
            self.eat("PRINT")
            e = self.expr()
            self.eat("SEMIC")
            return ("Print", e)

        if self.cur().t == "WHILE":
            self.eat("WHILE")
            self.eat("LP")
            cond = self.expr()
            self.eat("RP")
            body = self.block()
            return ("While", cond, body)

        if self.cur().t == "IF":
            return self.if_stmt()

        raise SyntaxError(f"Bad statement at {self.cur()}")

    def expr(self) -> AST:
        return self.equality()

    def equality(self) -> AST:
        node = self.relational()
        while self.cur().t in ("EQEQ", "NE"):
            op = self.cur().t
            self.i += 1
            rhs = self.relational()
            node = ("Cmp", op, node, rhs)
        return node

    def relational(self) -> AST:
        node = self.additive()
        while self.cur().t in ("LT", "GT", "LE", "GE"):
            op = self.cur().t
            self.i += 1
            rhs = self.additive()
            node = ("Cmp", op, node, rhs)
        return node

    def additive(self) -> AST:
        node = self.term()
        while self.cur().t in ("PLUS", "MINUS"):
            op = self.cur().t
            self.i += 1
            rhs = self.term()
            node = ("Bin", op, node, rhs)
        return node

    def term(self) -> AST:
        node = self.factor()
        while self.cur().t in ("MUL", "DIV"):
            op = self.cur().t
            self.i += 1
            rhs = self.factor()
            node = ("Bin", op, node, rhs)
        return node

    def factor(self) -> AST:
        if self.cur().t == "INT":
            v = int(self.cur().v)
            self.eat("INT")
            return ("Int", v)

        if self.cur().t == "ID":
            name = self.cur().v
            self.eat("ID")
            return ("Var", name)

        if self.cur().t == "LP":
            self.eat("LP")
            e = self.expr()
            self.eat("RP")
            return e

        raise SyntaxError(f"Bad factor at {self.cur()}")

def parse(src: str) -> AST:
    return Parser(lex(src)).program()

def _ast_to_anytree(node: AST, parent: Optional[Node] = None) -> None:
    if isinstance(node, tuple):
        tag = node[0]
        n = Node(tag, parent=parent)

        if tag == "Program":
            for st in node[1]:
                _ast_to_anytree(st, n)

        elif tag == "Let":
            Node(f"name={node[1]}", parent=n)
            _ast_to_anytree(node[2], n)

        elif tag == "Print":
            _ast_to_anytree(node[1], n)

        elif tag in ("Bin", "Cmp"):
            Node(f"op={node[1]}", parent=n)
            _ast_to_anytree(node[2], n)
            _ast_to_anytree(node[3], n)

        elif tag == "While":
            c = Node("cond", parent=n)
            _ast_to_anytree(node[1], c)
            b = Node("body", parent=n)
            for st in node[2]:
                _ast_to_anytree(st, b)

        elif tag == "IfChain":
            branches, else_block = node[1], node[2]
            for i, (cond, block) in enumerate(branches):
                br = Node(f"branch[{i}]", parent=n)
                cc = Node("cond", parent=br)
                _ast_to_anytree(cond, cc)
                bb = Node("body", parent=br)
                for st in block:
                    _ast_to_anytree(st, bb)
            if else_block is not None:
                e = Node("else", parent=n)
                for st in else_block:
                    _ast_to_anytree(st, e)

        elif tag == "Int":
            Node(str(node[1]), parent=n)

        elif tag == "Var":
            Node(str(node[1]), parent=n)

        else:
            for x in node[1:]:
                _ast_to_anytree(x, n)

    elif isinstance(node, list):
        for x in node:
            _ast_to_anytree(x, parent)
    else:
        Node(repr(node), parent=parent)

def print_ast(ast: AST) -> None:
    root = Node("AST")
    _ast_to_anytree(ast, root)
    for pre, _, node in RenderTree(root):
        print(pre + node.name)
