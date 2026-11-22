import base64
import os
import sys
from types import SimpleNamespace

import pytest
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import sendemail  # noqa: E402

TOKEN = 'test-token-not-a-secret-123'
MIB = 1024 * 1024


class FakeResponse:
    def __init__(self, status=200, payload=None, raw_error=None):
        self.status_code = status
        self._payload = payload
        self._raw_error = raw_error

    def json(self):
        if self._raw_error:
            raise ValueError('bad json')
        return self._payload


def ok_payload(delivered=(), queued=(), message_id='msg-1'):
    return {
        'success': True,
        'errors': [],
        'result': {
            'delivered': list(delivered),
            'queued': list(queued),
            'permanent_bounces': [],
            'message_id': message_id,
        },
    }


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv('CLOUDFLARE_ACCOUNT_ID', 'acct123')
    monkeypatch.setenv('CLOUDFLARE_EMAIL_API_TOKEN', TOKEN)
    monkeypatch.setenv('SENDER_EMAIL', 'orders@example.com')
    monkeypatch.setenv('RECIPIENT_EMAIL', 'a@example.com,b@example.com')
    monkeypatch.delenv('SENDGRID_API_KEY', raising=False)


@pytest.fixture
def post(monkeypatch):
    calls = []
    state = {'response': FakeResponse(200, ok_payload(['a@example.com', 'b@example.com'])), 'exc': None}

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append({'url': url, 'headers': headers, 'json': json, 'timeout': timeout})
        if state['exc']:
            raise state['exc']
        return state['response']

    monkeypatch.setattr(sendemail.requests, 'post', fake_post)
    return SimpleNamespace(calls=calls, state=state)


def test_success(post):
    ok = sendemail.send_email(['a@example.com', 'b@example.com'], 'Subj', '<p>hi</p>')
    assert ok is True
    call = post.calls[0]
    assert call['url'] == 'https://api.cloudflare.com/client/v4/accounts/acct123/email/sending/send'
    assert call['headers']['Authorization'] == f'Bearer {TOKEN}'
    assert call['json']['to'] == ['a@example.com', 'b@example.com']
    assert call['json']['from'] == 'orders@example.com'
    assert 'attachments' not in call['json']
    assert call['timeout'] == 30


def test_queued_recipients_count_as_success(post):
    post.state['response'] = FakeResponse(200, ok_payload(['a@example.com'], ['B@Example.com']))
    assert sendemail.send_email(['a@example.com', 'b@example.com'], 's', 'h') is True


def test_bounced_or_suppressed_recipient_is_failure(post, caplog):
    post.state['response'] = FakeResponse(200, ok_payload(['a@example.com']))
    assert sendemail.send_email(['a@example.com', 'b@example.com'], 's', 'h') is False
    assert TOKEN not in caplog.text


def test_success_false(post, caplog):
    post.state['response'] = FakeResponse(
        400, {'success': False, 'errors': [{'code': 10001, 'message': 'domain not verified'}], 'result': None}
    )
    assert sendemail.send_email(['a@example.com'], 's', 'h') is False
    assert '10001' in caplog.text


def test_http_2xx_but_success_false(post):
    post.state['response'] = FakeResponse(200, {'success': False, 'errors': [], 'result': ok_payload(['a@example.com'])['result']})
    assert sendemail.send_email(['a@example.com'], 's', 'h') is False


@pytest.mark.parametrize('resp', [
    FakeResponse(200, raw_error=True),
    FakeResponse(200, ['not', 'an', 'object']),
    FakeResponse(200, {'success': True, 'result': 'weird'}),
    FakeResponse(200, {'success': True}),
])
def test_malformed_body(post, resp):
    post.state['response'] = resp
    assert sendemail.send_email(['a@example.com'], 's', 'h') is False


def test_timeout(post):
    post.state['exc'] = requests.Timeout('slow')
    assert sendemail.send_email(['a@example.com'], 's', 'h') is False


def test_transport_error_does_not_leak_token(post, caplog):
    post.state['exc'] = requests.ConnectionError(f'failed with {TOKEN}')
    assert sendemail.send_email(['a@example.com'], 's', 'h') is False
    assert TOKEN not in caplog.text


def test_attachment_encoding_and_timeout(post):
    data = b'%PDF-1.4 \x00\xff binary'
    post.state['response'] = FakeResponse(200, ok_payload(['a@example.com']))
    ok = sendemail.send_email(['a@example.com'], 's', 'h', [('x.pdf', 'application/pdf', data)])
    assert ok is True
    att = post.calls[0]['json']['attachments']
    assert att == [{
        'content': base64.b64encode(data).decode('ascii'),
        'filename': 'x.pdf',
        'type': 'application/pdf',
        'disposition': 'attachment',
    }]
    assert post.calls[0]['timeout'] == 120


def test_size_budget_applies_to_combined_attachments():
    a = b'a' * (10 * MIB)
    b = b'b' * (10 * MIB)
    assert len(a) <= sendemail.MAX_ATTACHMENT_BYTES and len(b) <= sendemail.MAX_ATTACHMENT_BYTES
    kept, omitted = sendemail.budget_attachments([('l.pdf', 'application/pdf', a), ('o.zip', 'application/zip', b)])
    assert [k[0] for k in kept] == ['l.pdf']
    assert omitted == ['o.zip']


def test_size_budget_boundary():
    exact = b'a' * sendemail.MAX_ATTACHMENT_BYTES
    kept, omitted = sendemail.budget_attachments([('x', 'application/pdf', exact)])
    assert kept and not omitted
    kept, omitted = sendemail.budget_attachments([('x', 'application/pdf', exact + b'a')])
    assert not kept and omitted == ['x']


def test_send_email_refuses_over_budget(post):
    big = [('a', 'application/pdf', b'a' * (10 * MIB)), ('b', 'application/zip', b'b' * (10 * MIB))]
    assert sendemail.send_email(['a@example.com'], 's', 'h', big) is False
    assert post.calls == []


def _order_objs():
    order = SimpleNamespace(
        purchase_order_number='PO1', attachment=None, shipping_method='Ground',
        created_at=__import__('datetime').datetime(2026, 1, 1),
    )
    addr = SimpleNamespace(
        email='cust@example.com', companyName='Co', addressLine1='1 St', addressLine2='',
        city='X', state='Y', zipCode='1', phone='2',
    )
    return order, addr


def test_order_email_omits_second_attachment_and_says_so(post):
    post.state['response'] = FakeResponse(200, ok_payload(['a@example.com', 'b@example.com', 'cust@example.com']))
    order, addr = _order_objs()
    items = [{'sku': 's', 'product': 'p', 'size': 'z', 'flavor': 'f', 'quantity': 1}]
    pdf = b'p' * (10 * MIB)
    zipd = b'z' * (10 * MIB)
    assert sendemail.send_order_confirmation_email(order, addr, items, pdf, zipd) is True
    sent = post.calls[0]['json']
    assert [a['filename'] for a in sent['attachments']] == ['shipping_labels_PO_PO1.pdf']
    assert 'original_labels_PO_PO1.zip' in sent['html'] and 'omitted' in sent['html']
    assert 'cust@example.com' in sent['to']


def test_sendgrid_fallback_when_cloudflare_vars_missing(monkeypatch, post):
    monkeypatch.delenv('CLOUDFLARE_EMAIL_API_TOKEN')
    assert sendemail.use_cloudflare() is False
    # No SendGrid key either: refuses without any network call
    assert sendemail.send_email(['a@example.com'], 's', 'h') is False
    assert post.calls == []
