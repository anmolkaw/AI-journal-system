import base64

from app.security import hash_password, verify_password
from app.utils.hash import hash_text, normalize_text


def test_password_hashes_are_salted_and_verifiable():
    password = "correct-horse-battery-staple"
    first = hash_password(password)
    second = hash_password(password)

    assert first != second
    assert password not in first
    assert verify_password(password, first)
    assert verify_password(password, second)
    assert not verify_password("wrong-password", first)


def test_malformed_password_hashes_fail_closed():
    malformed = ["", "missing-separator", "%%%$%%%", "a$b$c"]
    assert all(not verify_password("password", value) for value in malformed)


def test_password_hash_contains_expected_salt_and_digest_sizes():
    salt_text, digest_text = hash_password("valid-password").split("$", 1)
    assert len(base64.urlsafe_b64decode(salt_text)) == 16
    assert len(base64.urlsafe_b64decode(digest_text)) == 64


def test_text_hash_normalization_is_stable():
    variants = [
        "A Calm Walk",
        "  a calm walk  ",
        "a   calm\nwalk",
        "A CALM WALK",
    ]
    assert normalize_text(variants[0]) == "a calm walk"
    assert len({hash_text(value) for value in variants}) == 1
    assert hash_text("a different walk") != hash_text(variants[0])
