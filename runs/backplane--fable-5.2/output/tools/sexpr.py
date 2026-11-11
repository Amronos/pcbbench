"""Minimal KiCad s-expression reader/writer."""
class Q(str):
    """quoted string"""
    pass

def parse(text):
    i = 0; n = len(text); stack = [[]]
    while i < n:
        c = text[i]
        if c in ' \t\r\n':
            i += 1
        elif c == '(':
            stack.append([]); i += 1
        elif c == ')':
            l = stack.pop(); stack[-1].append(l); i += 1
        elif c == '"':
            j = i + 1; out = []
            while text[j] != '"':
                if text[j] == '\\':
                    nx = text[j+1]
                    out.append({'n': '\n', 't': '\t', 'r': '\r'}.get(nx, nx)); j += 2
                else:
                    out.append(text[j]); j += 1
            stack[-1].append(Q(''.join(out))); i = j + 1
        else:
            j = i
            while j < n and text[j] not in ' \t\r\n()"':
                j += 1
            stack[-1].append(text[i:j]); i = j
    return stack[0][0]

def _atom(a):
    if isinstance(a, Q):
        return '"' + a.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'
    if isinstance(a, float):
        s = ('%.6f' % a).rstrip('0').rstrip('.')
        return s if s not in ('-0', '') else '0'
    return str(a)

def dump(e, ind=0):
    if not isinstance(e, list):
        return _atom(e)
    if all(not isinstance(x, list) for x in e):
        return '(' + ' '.join(_atom(x) for x in e) + ')'
    out = ['(' + _atom(e[0])]
    k = 1
    while k < len(e) and not isinstance(e[k], list):
        out[0] += ' ' + _atom(e[k]); k += 1
    pad = '\t' * (ind + 1)
    for x in e[k:]:
        out.append(pad + dump(x, ind + 1))
    out.append('\t' * ind + ')')
    return '\n'.join(out)

def find(e, name):
    for x in e:
        if isinstance(x, list) and x and x[0] == name:
            return x
    return None

def findall(e, name):
    return [x for x in e if isinstance(x, list) and x and x[0] == name]
