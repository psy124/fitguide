"""Personal Gemini settings and in-process requests; no external gateway needed."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import threading
from .auto_ai import protect
from .ai_provider import explain

_lock = threading.Lock()
DAILY_LIMIT = 10
MODEL_ID = 'gemini-3.1-flash-lite'


def root():
    return Path(os.environ.get('FITGUIDE_DESKTOP_DATA') or Path(os.environ['LOCALAPPDATA'])/'FitGuide')


def load_settings():
    path=root()/'personal-ai.dpapi'
    if not path.exists():return None
    try:
        value=json.loads(protect(path.read_bytes(),decrypt=True))
        # Older versions saved a user-entered model and limit. Retain the key;
        # the key-only UI uses the fixed model and the app's default limit.
        value['model']=MODEL_ID
        value['daily_limit']=DAILY_LIMIT
        validate(value['key'],value['model'],value['daily_limit'])
        return value
    except Exception:
        raise ValueError('저장한 AI 설정을 읽을 수 없습니다. 이 Windows 계정에서 API 키를 다시 저장하세요.') from None


def validate(key,model,limit):
    if not isinstance(key,str) or not key.strip() or len(key)>500 or any(c.isspace() for c in key.strip()):
        raise ValueError('Gemini API 키를 확인하세요.')
    if model != MODEL_ID:
        raise ValueError('Gemini 모델 설정을 확인하세요.')
    if type(limit) is not int or not 1<=limit<=1000:raise ValueError('일일 요청 한도는 1~1000회로 설정하세요.')


def save_settings(key):
    model=MODEL_ID;limit=DAILY_LIMIT
    if not key.strip():
        old=load_settings()
        key=old['key'] if old else ''
    key=key.strip();validate(key,model,limit)
    encrypted=protect(json.dumps(dict(key=key,model=model,daily_limit=limit)).encode())
    directory=root();directory.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=directory,suffix='.tmp')
    try:
        with os.fdopen(fd,'wb') as f:f.write(encrypted)
        os.replace(tmp,directory/'personal-ai.dpapi')
    finally:
        if Path(tmp).exists():Path(tmp).unlink()


def delete_settings():
    (root()/'personal-ai.dpapi').unlink(missing_ok=True)


def request(payload):
    from server.gateway import Gateway,GatewayError
    settings=load_settings()
    if not settings:raise ValueError('먼저 내 Gemini API 설정을 저장하세요.')
    if not _lock.acquire(blocking=False):raise ValueError('다른 AI 요청을 처리 중입니다. 잠시 후 다시 시도하세요.')
    try:
        # Keep quotas across key/model changes; namespace cached responses by configuration.
        identity=hashlib.sha256((settings['model']+'\0'+settings['key']).encode()).hexdigest()
        gateway=Gateway(root()/'personal-ai-usage.sqlite3',{'personal':hashlib.sha256(identity.encode()).hexdigest()},
                        lambda p:explain(settings['key'],settings['model'],p),settings['daily_limit'],settings['daily_limit'])
        data=dict(payload,request_id=hashlib.sha256((identity+payload['request_id']).encode()).hexdigest()[:32])
        return gateway.request('Bearer '+identity,data)
    except GatewayError as exc:
        suffix=(' ['+exc.diagnostic+']') if exc.diagnostic else ''
        raise ValueError(exc.message+suffix) from None
    finally:
        _lock.release()


def render_settings():
    import streamlit as st
    if st.session_state.pop('personal_clear_key',False):
        st.session_state['personal_api_key']=''
    try:settings=load_settings()
    except ValueError as exc:st.error(str(exc));settings=None
    with st.expander('내 Gemini API 설정',expanded=settings is None):
        st.caption('내 API 키로 이 PC에서 Gemini에 직접 요청합니다. 별도 서버·Python 설치는 필요 없습니다.')
        st.caption('키는 현재 Windows 계정으로 암호화하여 저장합니다. 같은 계정 권한의 프로그램까지 차단하지는 않습니다.')
        with st.form('personal_ai_settings'):
            key=st.text_input('Gemini API 키',type='password',key='personal_api_key',help='저장된 키는 표시하지 않습니다. 기존 키를 유지하려면 비워 두세요.')
            st.caption('API 키만 입력하세요. Gemini 3.1 Flash-Lite 모델을 사용합니다. 하루 최대 10회 요청할 수 있습니다.')
            st.caption('Google API 사용량·요금은 본인 프로젝트에 적용됩니다. 한국 시간 자정 기준이며 실패한 AI 호출도 차감될 수 있습니다.')
            if st.form_submit_button('API 설정 저장'):
                try:
                    save_settings(key)
                    st.session_state['personal_clear_key']=True
                    st.session_state.pop('ai_latest',None)
                    st.session_state.pop('ai_pending',None)
                    st.rerun()
                except ValueError as exc:st.error(str(exc))
                except OSError:st.error('설정을 저장하지 못했습니다. 저장 폴더 권한을 확인하세요.')
        if settings:
            st.caption('API 키가 저장되었습니다. 다음 실행부터 다시 입력하지 않아도 됩니다. 연결은 추천 생성 시 확인합니다.')
            confirm=st.checkbox('저장된 API 설정을 삭제합니다.',key='personal_delete_confirm')
            if st.button('API 설정 삭제',disabled=not confirm):
                delete_settings();st.session_state.pop('ai_pending',None);st.rerun()
    return settings
