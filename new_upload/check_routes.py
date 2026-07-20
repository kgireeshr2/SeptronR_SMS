import json, re, subprocess, glob, os

# Get backend routes
result = subprocess.run(['curl.exe', '-s', 'http://localhost:8000/openapi.json'], capture_output=True, text=True)
spec = json.loads(result.stdout)
backend = set()
for p in spec['paths']:
    norm = re.sub(r'\{[^}]+\}', '{id}', p.replace('/api/v1',''))
    backend.add(norm)

print(f"Backend has {len(backend)} unique route patterns")

# Read all frontend API calls
missing = []
for f in glob.glob('frontend/src/api/*.ts'):
    with open(f) as fh:
        content = fh.read()
    matches = re.findall(r"[`'](/[a-z][a-zA-Z0-9/_-]*)", content)
    for m in matches:
        norm = re.sub(r'\$\{[^}]+\}', '{id}', m)
        norm = re.sub(r'\?.*', '', norm)
        if norm not in backend:
            missing.append((os.path.basename(f), m, norm))

seen = set()
for f, m, norm in missing:
    if norm not in seen:
        seen.add(norm)
        print(f"  MISSING  {f}: {m}")
