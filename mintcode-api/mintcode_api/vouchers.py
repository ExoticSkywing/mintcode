from __future__ import annotations

import hmac
import secrets
from hashlib import sha256
from typing import Optional


_CROCKFORD32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _encode_crockford32(data: bytes) -> str:
    bits = 0
    value = 0
    out: list[str] = []
    for b in data:
        value = (value << 8) | b
        bits += 8
        while bits >= 5:
            idx = (value >> (bits - 5)) & 0x1F
            out.append(_CROCKFORD32[idx])
            bits -= 5
    if bits:
        idx = (value << (5 - bits)) & 0x1F
        out.append(_CROCKFORD32[idx])
    return "".join(out)


def _random_code(length: int) -> str:
    if length <= 0:
        raise ValueError("length must be > 0")
    nbytes = (length * 5 + 7) // 8
    s = _encode_crockford32(secrets.token_bytes(nbytes))
    return s[:length]


def _label_tag(label: str, secret: str, length: int) -> str:
    if length <= 0:
        raise ValueError("label_length must be > 0")
    mac = hmac.new(secret.encode("utf-8"), label.encode("utf-8"), sha256).digest()
    s = _encode_crockford32(mac)
    return s[:length]


def generate_voucher_codes(
    *,
    count: int,
    length: int = 32,
    label: Optional[str] = None,
    secret: Optional[str] = None,
    label_length: int = 6,
    label_pos: int = 8,
) -> list[str]:
    if count <= 0:
        raise ValueError("count must be > 0")
    if length < 12:
        raise ValueError("length must be >= 12")

    tag: Optional[str] = None
    if label is not None:
        if not secret:
            raise ValueError("secret is required when label is provided")
        tag = _label_tag(label, secret, label_length)
        if label_pos < 0 or label_pos > length:
            raise ValueError("label_pos out of range")
        if length + label_length > 128:
            raise ValueError("result length too long")

    out: set[str] = set()
    while len(out) < count:
        base = _random_code(length)
        if tag is None:
            out.add(base)
            continue
        code = f"{base[:label_pos]}{tag}{base[label_pos:]}"
        out.add(code)

    return sorted(out)
