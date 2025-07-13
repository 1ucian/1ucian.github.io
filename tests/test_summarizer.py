import InsightMate.Scripts.summarizer as summarizer
import llm_client


def test_model_used(monkeypatch):
    called = {}
    monkeypatch.setattr(summarizer, 'get_selected_model', lambda: 'foo')

    def fake_chat_completion(model, messages):
        called['model'] = model
        return 'ok'

    monkeypatch.setattr(llm_client, 'chat_completion', fake_chat_completion)
    summarizer.summarize_text('hello')
    assert called.get('model') == 'foo'


