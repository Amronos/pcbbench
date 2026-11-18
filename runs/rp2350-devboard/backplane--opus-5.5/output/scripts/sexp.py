"""Minimal S-expression parser/writer for KiCad files."""
import re

class Sym(str):
    """Unquoted atom."""
    pass

_tok = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|(\|[^|]*\|)|([^\s()"|]+))', re.S)

def parse(text):
    stack = [[]]
    pos = 0
    n = len(text)
    while pos < n:
        m = _tok.match(text, pos)
        if not m:
            if text[pos:].strip() == '':
                break
            raise ValueError("parse error at %d: %r" % (pos, text[pos:pos+50]))
        pos = m.end()
        if m.group(1):
            stack.append([])
        elif m.group(2):
            lst = stack.pop()
            stack[-1].append(lst)
        elif m.group(3) is not None:
            s = m.group(3)
            s = s.replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')
            stack[-1].append(s)
        elif m.group(4) is not None:
            stack[-1].append(Sym(m.group(4)))
        else:
            stack[-1].append(Sym(m.group(5)))
    return stack[0][0] if len(stack[0]) == 1 else stack[0]

def q(s):
    s = str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    return '"' + s + '"'

def fmt_atom(a):
    if isinstance(a, Sym):
        return str(a)
    if isinstance(a, bool):
        return 'yes' if a else 'no'
    if isinstance(a, int):
        return str(a)
    if isinstance(a, float):
        s = ('%.6f' % a).rstrip('0').rstrip('.')
        if s == '-0':
            s = '0'
        return s
    return q(a)

def dumps(x, indent=0):
    if not isinstance(x, list):
        return fmt_atom(x)
    # short lists on one line
    simple = all(not isinstance(e, list) for e in x)
    if simple:
        return '(' + ' '.join(fmt_atom(e) for e in x) + ')'
    out = '(' + ' '.join(fmt_atom(e) for e in x if not isinstance(e, list))
    # keep order: atoms first assumed at head
    parts = []
    head_done = False
    res = '('
    first = True
    for e in x:
        if isinstance(e, list):
            res += '\n' + '\t' * (indent + 1) + dumps(e, indent + 1)
        else:
            res += ('' if first else ' ') + fmt_atom(e)
        first = False
    res += '\n' + '\t' * indent + ')'
    return res

def find(node, key):
    for e in node:
        if isinstance(e, list) and e and e[0] == key:
            return e
    return None

def findall(node, key):
    return [e for e in node if isinstance(e, list) and e and e[0] == key]
