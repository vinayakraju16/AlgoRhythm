#!/usr/bin/env python3
"""Extract every endpoint referenced in templates/ and verify a route exists.

Static check: scans templates/ for URL literals (href/action attributes, JS
string ``...`` templates and single/double-quoted paths), removes Jinja
placeholders, then asserts a matching Flask rule exists in app.py.

Run: python3 tools/check_routes.py
"""
import os
import re
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
TEMPLATES = os.path.join(BASE, 'templates')

# Route rules declared in app.py:  @app.route('/x/<y>', methods=[...])
rule_re = re.compile(r"@app\.route\(\s*['\"]([^'\"]+)['\"]\s*(?:,\s*methods\s*=\s*\[([^\]]*)\])?")
with open(os.path.join(BASE, 'app.py'), encoding='utf-8') as fh:
    app_src = fh.read()

rules = []
for path, methods in rule_re.findall(app_src):
    verbs = re.findall(r"['\"](\w+)['\"]", methods) if methods else ['GET']
    rules.append((path, verbs))

def to_regex(rule):
    """Turn a Flask rule into a regex, treating <converter:name> as [^/]+."""
    pattern = re.sub(r'<[^>]+>', r'[^/]+', rule)
    return re.compile('^' + re.escape(pattern).replace(r'\[\^/\]\+', '[^/]+') + '$')

rule_res = [(r, m, to_regex(r)) for r, m in rules]

# Collect URL literals used in templates.
candidate_re = re.compile(
    r'(?:href|action)\s*=\s*["\']([^"\']+)["\']'   # html attributes
    r'|`(/[^`]*)`'                                  # js backtick templates
    r'|["\'](/[A-Za-z0-9_./<>?=&${}:-]*)["\']'      # js plain string paths
)

referenced = {}
for name in sorted(os.listdir(TEMPLATES)):
    if not name.endswith('.html'):
        continue
    with open(os.path.join(TEMPLATES, name), encoding='utf-8') as fh:
        src = fh.read()
    # strip html comments so dead/commented links do not count
    src = re.sub(r'<!--.*?-->', '', src, flags=re.S)
    for m in candidate_re.finditer(src):
        url = next(g for g in m.groups() if g)
        if not url.startswith('/') or url.startswith('//'):
            continue
        path = url.split('?', 1)[0]
        path = re.sub(r'\{\{.*?\}\}', 'OP000000000000', path)  # jinja value
        path = re.sub(r'\$\{[^}]*\}', 'OP000000000000', path)  # js template value
        path = re.sub(r'<[^>]*>', 'OP000000000000', path)
        referenced.setdefault(path, set()).add(name)

ok = True
print(f"{'ENDPOINT':<45} {'MATCHED RULE':<40} TEMPLATES")
print('-' * 110)
for path in sorted(referenced):
    match = None
    for rule, methods, rx in rule_res:
        if rx.match(path):
            match = f"{rule} [{','.join(methods)}]"
            break
    if match:
        print(f"{path:<45} {match:<40} {', '.join(sorted(referenced[path]))}")
    else:
        ok = False
        print(f"{path:<45} {'*** NO ROUTE ***':<40} {', '.join(sorted(referenced[path]))}")

print('-' * 110)
print(f"Declared routes: {len(rules)}")
print('RESULT:', 'PASS - every referenced endpoint has a route' if ok else 'FAIL - missing routes above')
sys.exit(0 if ok else 1)
