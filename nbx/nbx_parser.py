# AUTOGENERATED! DO NOT EDIT! File to edit: ../notebooks/06_nbx_parser.ipynb.

# %% auto 0
__all__ = ['fail', 'item', 'seed', 'tag_rx', 'flagname_rx', 'parse_tagged_line', 'is_nbx', 'TEMPLATES', 'include_rx',
           'is_jl_include', 'Parser', 'result', 'result_or_none', 'seq', 'compr', 'many', 'many1', 'parse_any_tag',
           'rx_parser', 'parse_flagname', 'starts_with_flag', 'parse_flags', 'is_nbx_cell', 'get_nbx_cells',
           'get_nbx_cells_src', 'Line', 'TaggedLine', 'EmptyLine', 'tokenize_src', 'Block', 'parse_into_nbx_blocks',
           'create_script', 'relpath', 'parse_jl_include', 'transform_jl_include', 'nbx_block_to_file',
           'create_jl_from_nb']

# %% ../notebooks/06_nbx_parser.ipynb 2
from collections import defaultdict


class Parser(object):
    """
    For us a parser is a callable with signature
    ```
        Iterable -> (a, Iterable) or None
    ```
    where `a` is the parser result. 
    Bindable functions have the signature 
    ```
        a -> Parser a
    ```
    """
    def __init__(self, f = lambda line: (None, line)): 
        """Wraps a fn with signature `line -> (a, line)` into a parser."""
        self.func = f
        
        
    def __call__(self, line): 
        return self.func(line)
    

    def bind(self, f): 
        """Monadic bind. Binds functions `a -> Parser a` to the parser."""
        def q(line):
            """The new parser func."""
            try: b, rest = self(line)
            except: return None
            return f(b)(rest)
        
        return Parser(q)
    
    
    def __rshift__(self, f):
        """Shorthand for 'bind'"""
        return self.bind(f)
    
    
    def __or__(self, q):
        """Creates a new parser that tries `q` if `self` fails."""
        def p(line):
            try: 
                a,rest = self(line)
                return (a, rest)
            except:
                return q(line)
            
        return Parser(p)
    
    
    def __eq__(self, val):
        """Creates a new parser that checks if result equals a given value."""
        def check(a, val):
            if isinstance(val, dict):
                for k, v in val.items(): 
                    if a[k] != v: return False
                return True
            else:
                return a == val

        return self.bind(lambda a: result(a) if check(a, val) else fail)
    
    
    def __ne__(self, val):
        """Checks if result does not equal a given value."""
        def check(a, val):
            if isinstance(val, dict):
                equal = True
                for k, v in val.items(): 
                    if a[k] != v: return True
            else:
                return a != val

        return self.bind(lambda a: result(a) if check(a, val) else fail)
    
        
    def __matmul__(self, key):      
        """
        Returns a bindable function `f(a)` that applies 
        the parser `self` and updates the given result dict `a` 
        with `self`'s results.
        """                
        def f(a):
            def p(line):
                try: b, rest = self(line)
                except: return None
                if key is None: return (a, rest)
                a[key] = b
                return (a, rest)
            
            return p
            
        return f
         

# A couple of useful atomic parsers 
def result(a): return Parser(lambda line: (a, line))
fail = Parser(lambda line: None)
item = Parser(lambda line: (line[0], line[1:]) if len(line)>0 else None)
seed = Parser(lambda line: ({}, line))

# %% ../notebooks/06_nbx_parser.ipynb 3
def result_or_none(y:"parser return"):
    """Returns None or the parser result (without the rest)."""
    if y is None: return None
    else: return y[0]

# %% ../notebooks/06_nbx_parser.ipynb 4
def seq(p, q): 
    return p >> (lambda a: (q >> (lambda b: result([a, b]))))

# %% ../notebooks/06_nbx_parser.ipynb 5
def compr(*ps, f = lambda *x: list(x)):
    def q(line):
        A = []
        rest = line
        for p in ps:
            try: a, rest = p(rest)
            except: return None
            A.append(a)
        return f(*A), rest
    return Parser(q)

# %% ../notebooks/06_nbx_parser.ipynb 7
def many(q):
    """Apply `q` ZERO or MORE times."""
    def wrapper(line):
        a = []
        def p(line):
            if len(line) == 0: return (a, line)
            try: b, rest = q(line)
            except: return (a, line)
            a.append(b)
            return p(rest)
        
        return p(line)
    return Parser(wrapper)


def many1(q):
    """Apply `q` ONE or MORE times."""
    def p(line):
        try: a, rest_ = q(line)
        except: return None
        b, rest = many(q)(rest_)
        
        return ([a] + b,rest) 

    return Parser(p)

# %% ../notebooks/06_nbx_parser.ipynb 11
import re
tag_rx = re.compile(r"^\s*#([a-zA-Z_]+)\s*(.*)$")

@Parser
def parse_any_tag(line):
    """
    Splits off a tag (eg. `#MyTAg`) 
    at the beginning of the line. 
    """
    m = tag_rx.match(line)
    if m is not None: return m.groups()
    else: return None

# %% ../notebooks/06_nbx_parser.ipynb 14
def rx_parser(rx):
    def p(line):
        m = rx.match(line)
        if m is not None: 
            d = m.groupdict()
            return (d, d.pop("rest", ""))
        else: return None
        
    return Parser(p)

# %% ../notebooks/06_nbx_parser.ipynb 17
import re
flagname_rx = re.compile(r"\s*(?:[\-]+)(?P<name>[a-zA-Z_\-]+)=?(.*)?$")

def parse_flagname(line):
    """
    Splits off the name of a flag iff 
    there is one at the beginning.
    """
    m = flagname_rx.match(line)
    if m is not None: 
        n,r = m.groups()
        if r is None: r = ""
        return (n,r.lstrip())
    else: return None
    
def starts_with_flag(line): return parse_flagname(line) is not None

# %% ../notebooks/06_nbx_parser.ipynb 19
from collections import defaultdict
import shlex 

@Parser
def parse_flags(line):
    """Extracts flag keys and value pairs"""
    d    = dict()
    last = None
    rest = [] # not a flag-key nor a value 
    for s in shlex.split(line):
        try:
            n, v = parse_flagname(s)
            v = v.strip()
            if v == "":
                d[n] = None
                last = n
            else:
                d[n] = v
                last = None
        except: 
            if last is not None: 
                d[last] = s
                last    = None
            else:
                rest.append(s)
         
    return (d, rest)


parse_tagged_line = seq(parse_any_tag, parse_flags)

# %% ../notebooks/06_nbx_parser.ipynb 22
from typing import Union, List, Tuple
from .utils import listmap
import json
from .utils import Bunch, load_nb
from pathlib import Path

# %% ../notebooks/06_nbx_parser.ipynb 23
is_nbx = parse_any_tag == "nbx"


def is_nbx_cell(cell):
    """Checks first of cell source for nbx tag."""
    if cell['cell_type'] != 'code': return False
    if not cell['source']: return False
    line0 = cell['source'][0]
    return is_nbx(line0)


def get_nbx_cells(nb):
    return list(filter(is_nbx_cell, nb.cells))


def get_nbx_cells_src(nb):
    return list(map(lambda c: c["source"] ,filter(is_nbx_cell, nb.cells)))

# %% ../notebooks/06_nbx_parser.ipynb 25
class Line(object):
    def __init__(self, src=""):
        self.name = None
        self.src  = src
        
    def __eq__(self, other): return self.name == other
    def __ne__(self, other): return self.name != other
    def __str__(self) : return f"``{self.src}''"
    def __repr__(self): return f"{self.__class__.__name__}('{self.src}')"
    
    
class TaggedLine(Line):
    def __init__(self, tag, flags, src = ""): 
        super().__init__(src=src)
        self.name  = tag
        self.flags = flags
        
    def __str__(self): 
        flags = "".join([f" --{k}=``{v}''" for k,v in self.flags.items()])
        return f"<{self.name}{flags}/>"
    
    def __repr__(self): return f"TaggedLine('{self.name}', '{self.src}')"
    
    
class EmptyLine(Line): 
    def __init__(self,): 
        super().__init__(src="")
        self.name = "empty"
        
    def __str__(self) : return u"\u2205" # "empty set" symbol

# %% ../notebooks/06_nbx_parser.ipynb 26
def tokenize_src(src, tags=None):
    """
    Converts each line of the src 
    into their corresponding `Line` object.
    
    If the `tags` argument is set, only its keys are
    considered valid tags when forming tagged lines.
    """
    parsed = []
    for line in src:
        line = line.rstrip()
        try: 
            (tag, flags), _ = parse_tagged_line(line.rstrip())
            if tags is None or tag in tags:
                parsed.append(TaggedLine(tag, flags, line))
            else:
                parsed.append(Line(line))

        except: 
            if line.strip() == "": parsed.append(EmptyLine())
            else:                  parsed.append(Line(line))
            
    return parsed

# %% ../notebooks/06_nbx_parser.ipynb 29
class Block(object):
    def __init__(self, fname=None, nbpath=None, src=[]):
        self.fname  = fname
        self.nbpath = nbpath
        self.src    = src
        
    def __str__(self):
        s = f"<Block fname = \"{self.fname}\", nbpath= \"{self.nbpath}\"/>\n"
        for l in block.src: s+=f"\n\t{l}"
        s += "\n"
        return s

# %% ../notebooks/06_nbx_parser.ipynb 30
def parse_into_nbx_blocks(nbpath):
    """
    Parses a notebook into "nbx blocks", a new block is started when 
    an nbx line contains a different filename than the last one.
    
    Typically there is only one block.
    """
    nbpath = Path(nbpath)
    nb     = load_nb(nbpath)
    nbx_cells = get_nbx_cells(nb)
    
    # Convert to Line tokens
    lines = []
    for cell in nbx_cells:
        cell_lines = tokenize_src(cell["source"])
        lines.extend(cell_lines)
        
    # Split into nbx blocks, typically just one.
    last_fname = None
    blocks = []
    for line in lines:
        if line == "nbx" and "fname" in line.flags:
                fname = line.flags["fname"]
                if fname != last_fname:
                    blocks.append(Block(fname=fname, nbpath=nbpath, src=[]))
                    last_fname = fname
        blocks[-1].src.append(line)
        
    return blocks

# %% ../notebooks/06_nbx_parser.ipynb 32
from .utils import nbx_lib
from .templ import *
import os

TEMPLATES = nbx_lib()/"templates"

def create_script(fname, tpl, vdict={}):
    """Create script from template and value dict""" 
    return create_file_from_template(TEMPLATES/tpl, fname, vdict)

# %% ../notebooks/06_nbx_parser.ipynb 34
def relpath(source, target):
    """Returns `source`'s path relative to `target`"""
    source = Path(source)
    target = Path(target)
    cwd = Path(os.getcwd())        
    return Path(os.path.relpath(cwd/source, cwd/target))

# %% ../notebooks/06_nbx_parser.ipynb 37
import re
include_rx = re.compile(r"^include\([\"\'\s]+([^\)]*)[\"\'\s]+\)(.*)")

@Parser
def parse_jl_include(line):
    m = include_rx.match(line)
    if m is not None: 
        file, rest = m.groups()
        return (str(Path(file)), rest)
    else: return None

# %% ../notebooks/06_nbx_parser.ipynb 39
is_jl_include= lambda line: parse_jl_include(line) is not None

# %% ../notebooks/06_nbx_parser.ipynb 40
def transform_jl_include(line, target, rel):
    """Replace the include path by relative path from new origin"""
    
    if not is_jl_include(line): return line
    old, _ = parse_jl_include(line)
    file = old
    if not os.path.isabs(file):
        file = relpath(rel.parent/file, rel.parent/target.parent)
        
    new_line = f"include(\"{file}\"); # autogenerated from: \"{old}\""
    return new_line

# %% ../notebooks/06_nbx_parser.ipynb 42
def nbx_block_to_file(block):
    nbpath = Path(block.nbpath)
    fname  = Path(block.fname)
    (nbpath.parent/fname.parent).mkdir(parents=True, exist_ok=True)
    lines = []

    for line in block.src:
        line.src = transform_jl_include(line.src, fname, nbpath)
        lines.append(line)
        
    # exclude nbx tags and get the actual line strings
    lines = filter(lambda l: l !="nbx",lines)
    lines =  listmap(lambda l: l.src, lines)
    
    create_script(fname=nbpath.parent/fname, tpl="nbxlines.tpl", vdict=dict(lines=lines, nbname=nbpath))
    
    return os.path.normpath(nbpath.parent/fname)


# %% ../notebooks/06_nbx_parser.ipynb 44
from .cli import add_argparse

@add_argparse
def create_jl_from_nb(nb_path):
    nbpath = Path(nb_path)
    created = []
    for block in parse_into_nbx_blocks(nbpath):
        fname = nbx_block_to_file(block)
        created.append(fname)
    
    print("\nExported julia-files:")
    for file in created:
        print(">>", f"\"{file}\"")
    print("\n")
    
    return created   