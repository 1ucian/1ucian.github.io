import os
import json
import requests
import msal

CLIENT_ID = os.getenv('MS_CLIENT_ID')
TENANT_ID = os.getenv('MS_TENANT_ID', 'common')
SCOPES = ['Files.Read']
TOKEN_FILE = 'ms_token.json'

token_cache = msal.SerializableTokenCache()
if os.path.exists(TOKEN_FILE):
    token_cache.deserialize(open(TOKEN_FILE).read())

app = msal.PublicClientApplication(
    CLIENT_ID,
    authority=f"https://login.microsoftonline.com/{TENANT_ID}",
    token_cache=token_cache
)

def get_token():
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
    else:
        flow = app.initiate_device_flow(scopes=SCOPES)
        print(flow['message'])
        result = app.acquire_token_by_device_flow(flow)
    if 'access_token' in result:
        with open(TOKEN_FILE, 'w') as f:
            f.write(token_cache.serialize())
        return result['access_token']
    raise RuntimeError('Failed to acquire token')

def list_recent_files(limit=5):
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}
    url = 'https://graph.microsoft.com/v1.0/me/drive/recent'
    resp = requests.get(url, headers=headers)
    items = resp.json().get('value', [])[:limit]
    return [{'name': i.get('name'), 'id': i.get('id')} for i in items]

if __name__ == '__main__':
    print(list_recent_files())
