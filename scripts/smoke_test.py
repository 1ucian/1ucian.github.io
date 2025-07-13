import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'InsightMate', 'Scripts')))

import types
sys.modules.setdefault('googleapiclient', types.SimpleNamespace(discovery=types.SimpleNamespace(build=lambda *a, **k: None)))
sys.modules.setdefault('googleapiclient.discovery', types.SimpleNamespace(build=lambda *a, **k: None))
fake_google = types.SimpleNamespace(
    oauth2=types.SimpleNamespace(credentials=types.SimpleNamespace(Credentials=object)),
    auth=types.SimpleNamespace(transport=types.SimpleNamespace(requests=types.SimpleNamespace(Request=object)))
)
sys.modules.setdefault('google', fake_google)
sys.modules.setdefault('google.oauth2', fake_google.oauth2)
sys.modules.setdefault('google.oauth2.credentials', fake_google.oauth2.credentials)
sys.modules.setdefault('google_auth_oauthlib.flow', types.SimpleNamespace(InstalledAppFlow=object))
sys.modules.setdefault('google.auth', fake_google.auth)
sys.modules.setdefault('google.auth.transport', fake_google.auth.transport)
sys.modules.setdefault('google.auth.transport.requests', fake_google.auth.transport.requests)
sys.modules.setdefault('server_common', types.SimpleNamespace(_load_model=lambda: 'qwen3:30b-a3b'))

import assistant_router as ar


def run():
    def dummy_plan(msg, model):
        msg = msg.lower()
        if 'list' in msg and 'email' in msg:
            return [{'type': 'search_email', 'query': 'today'}]
        if 'summarize' in msg:
            return [{'type': 'summarize'}]
        if 'add event' in msg:
            return [{'type': 'schedule_event', 'title': 'demo', 'time': '09:00', 'date': 'tomorrow'}]
        return [{'type': 'chat', 'prompt': "I don't know"}]

    ar.plan_actions = dummy_plan
    ar.chat_completion = lambda model, msgs: 'ok'
    ar.gpt = lambda prompt, model=None, cot_mode=False: 'ok'
    import summarizer
    summarizer.gpt = lambda prompt, model=None: 'ok'
    summarizer.get_selected_model = lambda: 'foo'
    ar.TOOL_REGISTRY['search_email'] = lambda a: [{'subject':'Hi','snippet':'x'}]
    ar.TOOL_REGISTRY['summarize'] = lambda a: 'Summary'
    ar.TOOL_REGISTRY['schedule_event'] = lambda a: 'Event created'

    for q in ["list today's emails", "summarize them", "add event 9 am demo tomorrow"]:
        reply = ar.plan_then_answer(q)
        assert not reply.strip().startswith('⚠️'), reply
        print(q, '->', reply)


if __name__ == '__main__':
    run()

