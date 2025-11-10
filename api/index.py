# api/index.py
# simple entrypoint for Vercel Python runtime
# it must expose a variable named `app` (a WSGI/ASGI app)

from app import app

# `app` is now the WSGI application Vercel will run.
# No additional code required.
