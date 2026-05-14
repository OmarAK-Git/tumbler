def is_palindrome(s: str) -> bool:
    """Return True if s reads the same forwards and backwards, ignoring case and non-alphanumeric characters."""
    cleaned = "".join(c.lower() for c in s if c.isalnum())
    return cleaned == cleaned[::-1]


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python palindrome.py <string>")
        sys.exit(1)
    result = is_palindrome(sys.argv[1])
    print(f"{sys.argv[1]!r}: {'palindrome' if result else 'not a palindrome'}")
