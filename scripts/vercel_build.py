"""Production database preparation. Vercel collects static assets automatically."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
def run(*args):
    subprocess.run([sys.executable, str(ROOT / 'manage.py'), *args], cwd=ROOT, check=True)

if __name__ == '__main__':
    run('check', '--deploy')
    # Preview deployments must have their own database; never migrate production from a preview.
    if os.environ.get('VERCEL_ENV') == 'production' or os.environ.get('VERCEL_RUN_MIGRATIONS') == 'true':
        run('migrate', '--noinput')
        run('seed_catalog')
        run('bootstrap_admin')
