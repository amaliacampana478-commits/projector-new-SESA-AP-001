"""Serviço de e-mail transacional (Emergent managed email / Resend).

Dois gatilhos:
  - inscrição realizada  -> build_inscricao_email_html
  - pagamento PIX gerado -> build_pix_email_html

Os destinatários vêm SEMPRE de registros do servidor (e-mail que o próprio
candidato informou na inscrição) e os corpos de e-mail de templates fixos
no servidor. Nunca aceite HTML/recipiente vindo do cliente (G4).
"""
import os
import re
import ipaddress
import logging
import httpx
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Proxy gerenciado da Emergent. É uma CONSTANTE — nunca ler do os.environ.
EMAIL_BASE_URL = "https://integrations.emergentagent.com"
EMAIL_KEY = os.environ["EMERGENT_EMAIL_KEY"]
EMAIL_FROM_NAME = os.environ["EMAIL_FROM_NAME"]
EMAIL_REPLY_TO = os.environ.get("EMAIL_REPLY_TO")

# ----------------------------------------------------------------------------
# Guardrail gate (copiado do playbook — chamar em todo envio)
# ----------------------------------------------------------------------------
_SHORTENERS = ("bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly", "goo.gl", "rebrand.ly")
_CRED_ASK = ("reply with your password", "reply with the code", "send your password", "cvv",
             "send us your password", "enter your password below", "confirm your card number",
             "your full card number", "seed phrase", "recovery phrase", "verify your card",
             "social security number", "confirm your bank details")
_HOSTISH = re.compile(r"\b(?:https?://)?((?:[a-z0-9-]+\.)+[a-z]{2,})", re.I)


def _host_ok(host: str) -> bool:
    if not host or "xn--" in host:
        return False
    try:
        ipaddress.ip_address(host)
        return False
    except ValueError:
        pass
    return not any(host == s or host.endswith("." + s) for s in _SHORTENERS)


def _same_site(shown: str, real: str) -> bool:
    return shown == real or real.endswith("." + shown) or shown.endswith("." + real)


class _EmailScan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.urls, self.anchors = set(), [], []
        self._href, self._text = None, []

    def handle_starttag(self, tag, attrs):
        self.tags.add(tag.lower())
        self.urls += [v for k, v in attrs if k.lower() in ("href", "src") and v]
        if tag.lower() == "a":
            self._href = dict((k.lower(), v) for k, v in attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            self.anchors.append((self._href, "".join(self._text)))
            self._href, self._text = None, []


def _assert_safe_email(subject: str, html: str) -> None:
    scan = _EmailScan()
    scan.feed(html)
    if scan.tags & {"form", "input", "textarea", "select"}:
        raise ValueError("No forms or input fields in email (G2)")
    body = f"{subject}\n{html}".lower()
    for p in _CRED_ASK:
        if p in body:
            raise ValueError(f"Email asks the recipient for credentials: {p!r} (G2)")
    for url in scan.urls:
        low = url.strip().lower()
        if low.startswith(("mailto:", "tel:", "cid:", "#")):
            continue
        if not low.startswith("https://"):
            raise ValueError(f"Email links/assets must be absolute https: {url!r} (G3)")
        host = urlparse(low).hostname or ""
        if not _host_ok(host) or urlparse(low).username is not None:
            raise ValueError(f"Shortened, numeric-host or credential-bearing URL: {url!r} (G3)")
    for href, text in scan.anchors:
        real = urlparse(href.strip().lower()).hostname or ""
        if not real:
            continue
        for m in _HOSTISH.finditer(text):
            if not _same_site(m.group(1).lower(), real):
                raise ValueError(f"Anchor text {m.group(1)!r} != real link host {real!r} (G3)")


# ----------------------------------------------------------------------------
# Envio (assíncrono / não bloqueante)
# ----------------------------------------------------------------------------
async def send_email(*, to: str, subject: str, html: str) -> str | None:
    _assert_safe_email(subject, html)
    payload = {"to": [to], "subject": subject, "html": html, "from_name": EMAIL_FROM_NAME}
    if EMAIL_REPLY_TO:
        payload["contact_email"] = EMAIL_REPLY_TO
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{EMAIL_BASE_URL}/api/v1/email/send",
            headers={"X-Email-Key": EMAIL_KEY},
            json=payload,
        )
    resp.raise_for_status()
    return resp.json().get("id")


async def try_send_email(*, to: str, subject: str, html: str) -> bool:
    """Envia sem quebrar o fluxo principal. Retorna True se enviou."""
    if not to or "@" not in to:
        return False
    try:
        await send_email(to=to, subject=subject, html=html)
        logger.info(f"[email] enviado: {subject!r} -> {to}")
        return True
    except httpx.HTTPStatusError as e:
        try:
            code = e.response.json().get("code", "")
            msg = e.response.json().get("message", "")
        except ValueError:
            code, msg = "", e.response.text
        logger.warning(f"[email] falha {e.response.status_code} {code}: {msg}")
        return False
    except Exception as e:
        logger.error(f"[email] erro: {e}")
        return False


# ----------------------------------------------------------------------------
# Templates (HTML inline, layout em tabela)
# ----------------------------------------------------------------------------
def _fmt_valor(valor) -> str:
    try:
        v = float(valor or 0)
    except Exception:
        v = 0.0
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _shell(inner: str) -> str:
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="background:#f4f7fb;padding:24px 0;font-family:Arial,Helvetica,sans-serif">'
        '<tr><td align="center">'
        '<table role="presentation" width="600" cellpadding="0" cellspacing="0" '
        'style="max-width:600px;background:#ffffff;border:1px solid #e6eaf1;border-radius:10px;overflow:hidden">'
        '<tr><td style="background:#174d87;padding:20px 28px">'
        f'<span style="color:#fff;font-size:18px;font-weight:bold">{escape(EMAIL_FROM_NAME)}</span>'
        '</td></tr>'
        f'<tr><td style="padding:28px">{inner}</td></tr>'
        '<tr><td style="padding:18px 28px;border-top:1px solid #eef1f6">'
        f'<p style="margin:0;font-size:12px;color:#8a96a8;line-height:1.5">'
        f'Enviado por {escape(EMAIL_FROM_NAME)}. Este é um e-mail automático de confirmação. '
        'Nunca pedimos senha, código ou dados de cartão por e-mail.'
        '</p></td></tr>'
        '</table></td></tr></table>'
    )


def _row(label: str, value: str) -> str:
    return (
        '<tr>'
        f'<td style="padding:8px 0;font-size:13px;color:#111;font-weight:bold;white-space:nowrap;vertical-align:top">{escape(label)}</td>'
        f'<td style="padding:8px 0 8px 10px;font-size:14px;color:#2b3a4d;vertical-align:top">{escape(value)}</td>'
        '</tr>'
    )


def build_inscricao_email_html(*, nome: str, cpf: str, protocolo: str, cargo: str,
                               concurso: str, valor) -> str:
    rows = _row("Número da inscrição:", protocolo or "-")
    rows += _row("Nome:", nome or "-")
    rows += _row("CPF:", cpf or "-")
    if cargo:
        rows += _row("Cargo:", cargo)
    if concurso:
        rows += _row("Concurso:", concurso)
    rows += _row("Valor da inscrição:", _fmt_valor(valor))
    inner = (
        f'<p style="margin:0 0 14px;font-size:16px;color:#111">Olá, {escape((nome or "candidato(a)").split()[0] if nome else "candidato(a)")}!</p>'
        '<p style="margin:0 0 18px;font-size:14px;color:#2b3a4d;line-height:1.6">'
        'Sua <strong>inscrição foi realizada com sucesso</strong>. Veja o resumo abaixo:'
        '</p>'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="border:1px solid #e6eaf1;border-radius:8px;padding:6px 16px">'
        f'{rows}</table>'
        '<p style="margin:18px 0 0;font-size:14px;color:#2b3a4d;line-height:1.6">'
        'Para concluir, realize o <strong>pagamento da taxa de inscrição via PIX</strong>. '
        'Você receberá um e-mail separado com os dados do PIX ao gerar o pagamento.'
        '</p>'
    )
    return _shell(inner)


def build_pix_email_html(*, nome: str, cpf: str, cargo: str, valor, pix_code: str) -> str:
    rows = _row("Nome:", nome or "-")
    rows += _row("CPF:", cpf or "-")
    if cargo:
        rows += _row("Cargo:", cargo)
    rows += _row("Valor:", _fmt_valor(valor))
    inner = (
        f'<p style="margin:0 0 14px;font-size:16px;color:#111">Olá, {escape((nome or "candidato(a)").split()[0] if nome else "candidato(a)")}!</p>'
        '<p style="margin:0 0 18px;font-size:14px;color:#2b3a4d;line-height:1.6">'
        'Aqui está o <strong>pagamento PIX</strong> da sua inscrição. Resumo:'
        '</p>'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="border:1px solid #e6eaf1;border-radius:8px;padding:6px 16px">'
        f'{rows}</table>'
        '<p style="margin:20px 0 8px;font-size:13px;color:#111;font-weight:bold">PIX copia e cola:</p>'
        '<div style="background:#f4f7fb;border:1px dashed #9fb3cc;border-radius:8px;padding:14px;'
        'font-family:Consolas,monospace;font-size:13px;color:#174d87;word-break:break-all;line-height:1.5;'
        '-webkit-user-select:all;user-select:all">'
        f'{escape(pix_code)}'
        '</div>'
        '<p style="margin:10px 0 0;font-size:12px;color:#8a96a8;line-height:1.5">'
        'Toque e segure (celular) ou clique e selecione (computador) o código acima para copiar '
        'e cole no app do seu banco, na opção PIX &gt; Copia e Cola.'
        '</p>'
    )
    return _shell(inner)
