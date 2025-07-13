import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'InsightMate', 'Scripts'))

# Stub heavy google libraries so tests run without dependencies
import types
sys.modules.setdefault('googleapiclient', types.SimpleNamespace(discovery=types.SimpleNamespace(build=lambda *a, **k: None)))
sys.modules.setdefault('googleapiclient.discovery', types.SimpleNamespace(build=lambda *a, **k: None))
fake_google = types.SimpleNamespace(oauth2=types.SimpleNamespace(credentials=types.SimpleNamespace(Credentials=object)))
fake_google.auth = types.SimpleNamespace(transport=types.SimpleNamespace(requests=types.SimpleNamespace(Request=object)))
sys.modules.setdefault('google', fake_google)
sys.modules.setdefault('google.oauth2', fake_google.oauth2)
sys.modules.setdefault('google.oauth2.credentials', fake_google.oauth2.credentials)
sys.modules.setdefault('google_auth_oauthlib.flow', types.SimpleNamespace(InstalledAppFlow=object))
sys.modules.setdefault('google.auth', fake_google.auth)
sys.modules.setdefault('google.auth.transport', fake_google.auth.transport)
sys.modules.setdefault('google.auth.transport.requests', fake_google.auth.transport.requests)
