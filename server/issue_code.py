"""Issue a high-entropy demo code. Plaintext codes only live in private operator files."""
import argparse,hashlib,json,secrets
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('user');a=p.parse_args()
if not a.user.isascii() or not a.user.replace('-','').replace('_','').isalnum():
    raise SystemExit('Use an ASCII user ID containing letters/numbers/_/-')
root=Path(__file__).resolve().parent/'private';root.mkdir(exist_ok=True)
path=root/'config.json'
config=json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else dict(model='',user_daily_limit=10,total_daily_limit=100,users={})
code=secrets.token_urlsafe(32)
config['users'][a.user]=hashlib.sha256(code.encode()).hexdigest()
path.write_text(json.dumps(config,indent=2),encoding='utf-8')
(root/(a.user+'-access.txt')).write_text(code,encoding='utf-8')
print('Code saved in server/private/'+a.user+'-access.txt. Reissuing revokes the old code after server restart.')
