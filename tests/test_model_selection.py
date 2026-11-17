import io
import json
import urllib.error
import pytest
from fitguide import ai_provider as provider


def model(name, methods=None):
    return dict(name='models/'+name,supportedGenerationMethods=methods or ['generateContent'])


def test_discovery_paginates_and_prefers_stable_text_flash(monkeypatch):
    pages=[dict(models=[model('gemini-9-flash-preview'),model('gemini-9-pro'),
                        model('gemini-9-flash-image'),model('gemini-9-flash-tts'),
                        model('gemini-9-flash-live'),model('gemini-9-embedding',['embedContent'])],nextPageToken='next/page'),
           dict(models=[model('gemini-3.6-flash'),model('gemini-3.8-flash'),model('gemini-3.8-flash-lite')])]
    requests=[]
    def urlopen(request,timeout):
        requests.append(request)
        assert request.get_header('X-goog-api-key')=='private-key'
        assert 'private-key' not in request.full_url
        return io.BytesIO(json.dumps(pages.pop(0)).encode())
    monkeypatch.setattr(provider.urllib.request,'urlopen',urlopen)
    assert provider.select_model('private-key')=='gemini-3.8-flash'
    assert 'pageToken=next%2Fpage' in requests[1].full_url


def test_no_text_models_has_safe_diagnostic(monkeypatch):
    monkeypatch.setattr(provider.urllib.request,'urlopen',lambda *a,**k:io.BytesIO(b'{"models":[]}'))
    with pytest.raises(provider.ProviderError,match='MODEL_NOT_FOUND'):
        provider.select_model('secret')


def test_model_discovery_auth_error_does_not_expose_provider_body(monkeypatch):
    def fail(*a,**kw):
        raise urllib.error.HTTPError('https://example.invalid',400,'secret',{},
            io.BytesIO(b'{"error":{"message":"private-key","details":[{"reason":"API_KEY_INVALID"}]}}'))
    monkeypatch.setattr(provider.urllib.request,'urlopen',fail)
    with pytest.raises(provider.ProviderError) as exc:
        provider.select_model('private-key')
    assert exc.value.code=='API_KEY_INVALID' and 'private-key' not in str(exc.value)
