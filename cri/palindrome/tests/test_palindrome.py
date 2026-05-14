import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from palindrome import is_palindrome


def test_simple_palindrome():
    assert is_palindrome("racecar") is True


def test_simple_non_palindrome():
    assert is_palindrome("hello") is False


def test_mixed_case_with_punctuation():
    assert is_palindrome("A man, a plan, a canal: Panama") is True


def test_empty_string():
    assert is_palindrome("") is True


def test_single_character():
    assert is_palindrome("a") is True
