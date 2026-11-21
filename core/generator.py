"""
generator.py
Handles password generation and strength checking for the password generator UI.
"""

import secrets
import string

# Password generation with options for character types and strength checking
LOWERCASE = string.ascii_lowercase   # a-z
UPPERCASE = string.ascii_uppercase   # A-Z
DIGITS    = string.digits            # 0-9
SYMBOLS   = "!@#$%^&*()-_=+[]{}|;:,.<>?"


# Generate a random password with the specified options.
def generate_password(
    length:      int  = 16,
    use_lower:   bool = True,
    use_upper:   bool = True,
    use_digits:  bool = True,
    use_symbols: bool = True,
) -> str:
  
    # Build the pool of allowed characters
    pool     = ""
    required = []

    if use_lower:
        pool += LOWERCASE
        required.append(secrets.choice(LOWERCASE))

    if use_upper:
        pool += UPPERCASE
        required.append(secrets.choice(UPPERCASE))

    if use_digits:
        pool += DIGITS
        required.append(secrets.choice(DIGITS))

    if use_symbols:
        pool += SYMBOLS
        required.append(secrets.choice(SYMBOLS))

    # Must have at least one category selected
    if not pool:
        raise ValueError("At least one character type must be selected")

    # Enforce minimum length
    length = max(length, 8)

    # Fill remaining slots with random chars from pool
    remaining = [secrets.choice(pool) for _ in range(length - len(required))]

    # Combine required + remaining then shuffle
    password_chars = required + remaining
    secrets.SystemRandom().shuffle(password_chars)

    return "".join(password_chars)


# Check the strength of a password and return a score, label, and colour for UI display.
def check_strength(password: str) -> tuple:

    score = 0

    # Length scoring
    if len(password) >= 8:  score += 1
    if len(password) >= 12: score += 1
    if len(password) >= 16: score += 1

    # Character variety scoring
    has_lower  = any(c in LOWERCASE for c in password)
    has_upper  = any(c in UPPERCASE for c in password)
    has_digit  = any(c in DIGITS    for c in password)
    has_symbol = any(c in SYMBOLS   for c in password)

    if has_lower and has_upper: score += 1
    if has_digit:               score += 1
    if has_symbol:              score += 1

    # Map score 0-6 down to 0-4
    score = min(score, 4)

    # Labels and colours for the UI
    levels = [
        (0, "Very weak", "#E24B4A"),   # red
        (1, "Weak",      "#F0883E"),   # orange
        (2, "Fair",      "#EF9F27"),   # amber
        (3, "Good",      "#3FB950"),   # green
        (4, "Strong",    "#58D4C8"),   # teal
    ]

    score_val, label, colour = levels[score]
    return score, label, colour


#  Quick test 
if __name__ == "__main__":

    print("=" * 50)
    print("STEP 1 — Generate with all options on")
    pw = generate_password(length=16)
    print(f"Password         : {pw}")
    print(f"Length           : {len(pw)}")

    has_lower  = any(c in LOWERCASE for c in pw)
    has_upper  = any(c in UPPERCASE for c in pw)
    has_digit  = any(c in DIGITS    for c in pw)
    has_symbol = any(c in SYMBOLS   for c in pw)
    print(f"Has lowercase    : {has_lower}")
    print(f"Has uppercase    : {has_upper}")
    print(f"Has digit        : {has_digit}")
    print(f"Has symbol       : {has_symbol}")

    print()
    print("=" * 50)
    print("STEP 2 — Generate with only letters")
    pw2 = generate_password(length=12, use_lower=True,
                             use_upper=True, use_digits=False,
                             use_symbols=False)
    print(f"Password         : {pw2}")
    print(f"Has digit        : {any(c in DIGITS   for c in pw2)}")
    print(f"Has symbol       : {any(c in SYMBOLS  for c in pw2)}")

    print()
    print("=" * 50)
    print("STEP 3 — Generate with only digits")
    pw3 = generate_password(length=8, use_lower=False,
                             use_upper=False, use_digits=True,
                             use_symbols=False)
    print(f"Password         : {pw3}")
    print(f"All digits       : {all(c in DIGITS for c in pw3)}")

    print()
    print("=" * 50)
    print("STEP 4 — Strength checker")
    test_passwords = [
        "abc",
        "password",
        "Password1",
        "P@ssw0rd!",
        "P@ssw0rd!VaultKey2026",
    ]
    for p in test_passwords:
        score, label, colour = check_strength(p)
        print(f"  {p:25} → {label:10} (score {score}/4)")

    print()
    print("=" * 50)
    print("STEP 5 — No categories selected raises error")
    try:
        generate_password(use_lower=False, use_upper=False,
                          use_digits=False, use_symbols=False)
    except ValueError as e:
        print(f"Error caught correctly : {e}")

    print()
    print("=" * 50)
    print("STEP 6 — Minimum length enforced")
    pw4 = generate_password(length=2)
    print(f"Requested length 2, got : {len(pw4)} (minimum 8 enforced)")

    print()
    print("All generator tests passed!")