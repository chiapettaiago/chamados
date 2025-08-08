import os
import requests

SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
SENDGRID_FROM = os.getenv('SENDGRID_FROM', 'no-reply@example.com')

MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN')
MAILGUN_FROM = os.getenv('MAILGUN_FROM', 'no-reply@example.com')

WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')
WHATSAPP_PHONE_ID = os.getenv('WHATSAPP_PHONE_ID')


def send_email_sendgrid(to, subject, html):
    if not SENDGRID_API_KEY:
        return False, 'SENDGRID_API_KEY ausente'
    url = 'https://api.sendgrid.com/v3/mail/send'
    data = {
        'personalizations': [{'to': [{'email': to}]}],
        'from': {'email': SENDGRID_FROM},
        'subject': subject,
        'content': [{'type': 'text/html', 'value': html}]
    }
    headers = {'Authorization': f'Bearer {SENDGRID_API_KEY}', 'Content-Type': 'application/json'}
    r = requests.post(url, json=data, headers=headers, timeout=10)
    return r.ok, r.text


def send_email_mailgun(to, subject, html):
    if not MAILGUN_API_KEY or not MAILGUN_DOMAIN:
        return False, 'MAILGUN config ausente'
    url = f'https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages'
    data = {
        'from': MAILGUN_FROM,
        'to': to,
        'subject': subject,
        'html': html
    }
    r = requests.post(url, auth=('api', MAILGUN_API_KEY), data=data, timeout=10)
    return r.ok, r.text


def send_email(to, subject, html):
    # Tenta SendGrid, cai para Mailgun
    ok, resp = send_email_sendgrid(to, subject, html)
    if ok:
        return True, resp
    return send_email_mailgun(to, subject, html)


def send_whatsapp(to_e164: str, text: str):
    """Envia mensagem via WhatsApp Cloud API. 'to_e164' deve incluir DDI (ex.: 5599999999999)."""
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_ID:
        return False, 'Config WhatsApp ausente'
    url = f'https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_ID}/messages'
    headers = {
        'Authorization': f'Bearer {WHATSAPP_TOKEN}',
        'Content-Type': 'application/json'
    }
    payload = {
        'messaging_product': 'whatsapp',
        'to': to_e164,
        'type': 'text',
        'text': {'body': text}
    }
    r = requests.post(url, json=payload, headers=headers, timeout=10)
    return r.ok, r.text
