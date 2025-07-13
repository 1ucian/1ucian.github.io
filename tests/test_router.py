import json
import InsightMate.Scripts.assistant_router as ar


def test_normalise():
    action = {" tool": "search_email"}
    assert ar._normalise(action) == {"type": "search_email"}


def test_string_plan():
    plan_str = '[{"tool":"search_email"}]'
    out = [ar._normalise(item) for item in json.loads(plan_str)]
    assert out == [{"type": "search_email"}]

