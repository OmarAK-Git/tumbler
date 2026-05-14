# Palindrome Checker

A command-line tool that checks whether a string is a palindrome.

## What it does

`is_palindrome(s)` returns `True` if `s` reads the same forwards and backwards after:
- lowercasing all characters
- removing all non-alphanumeric characters

Examples:
- `"racecar"` → True
- `"A man, a plan, a canal: Panama"` → True
- `"hello"` → False
- `""` → True (empty string is a palindrome by convention)

## Run it

```
python palindrome.py "racecar"
```

Prints `'racecar': palindrome` or `'racecar': not a palindrome`.

## Run tests

```
pytest tests/
```
