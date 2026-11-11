"""
test_poly_roots.py -- correctness tests on polynomials with KNOWN roots.

Run:  python test_poly_roots.py
Every test prints PASS/FAIL; exit code is nonzero if any test fails.
"""

import itertools

from poly_roots import poly_real_roots, poly_eval


def multiply_out(factors):
    """Expand prod (x - r) into ascending-order coefficients."""
    coeffs = [1.0]
    for r in factors:
        new = [0.0] * (len(coeffs) + 1)
        for i, c in enumerate(coeffs):
            new[i] -= c * r
            new[i + 1] += c
        coeffs = new
    return coeffs


def check(name, coeffs, expected, tol=1e-7):
    """expected: dict {root: multiplicity}."""
    got = poly_real_roots(coeffs)
    ok = len(got) == len(expected)
    if ok:
        for r, m in got:
            hit = min(expected, key=lambda e: abs(e - r))
            if abs(hit - r) > tol or expected[hit] != m:
                ok = False
                break
    residual = max((abs(poly_eval(coeffs, r)) for r, _ in got), default=0.0)
    scale = max(1.0, max(abs(c) for c in coeffs))
    status = "PASS" if ok and residual < 1e-8 * scale else "FAIL"
    print("%-4s %-34s roots=%s max|p(root)|/scale=%.2e"
          % (status, name, ["%.6f(x%d)" % (r, m) for r, m in got],
             residual / scale))
    return status == "PASS"


def main():
    results = []

    # 1. the assignment polynomial
    results.append(check(
        "assignment p5",
        [5.0, -5.0, -1.0, -6.0, 0.0, 1.0],
        {-2.579714343403: 1, 0.634113250651: 1, 2.614244150443: 1}))

    # 2. five spread simple roots: (x-1)(x-2)(x-3)(x-4)(x-5)
    results.append(check(
        "five simple roots",
        multiply_out([1, 2, 3, 4, 5]),
        {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}))

    # 3. multiple roots: (x-2)^3 (x+1)^2
    #    An m-fold root is only computable to ~eps**(1/m) in floating
    #    point (eps^(1/3) ~ 6e-6), hence the looser location tolerance.
    results.append(check(
        "triple + double root",
        multiply_out([2, 2, 2, -1, -1]),
        {2: 3, -1: 2},
        tol=1e-4))

    # 4. no real roots: x^2 + 1 and x^4 + 1
    results.append(check("x^2 + 1 (no real roots)", [1.0, 0.0, 1.0], {}))
    results.append(check("x^4 + 1 (no real roots)", [1.0, 0, 0, 0, 1.0], {}))

    # 5. roots at zero: 3x^3 + 2x^2 = x^2 (3x + 2)
    results.append(check(
        "roots at zero",
        [0.0, 0.0, 2.0, 3.0],
        {0.0: 2, -2.0 / 3.0: 1}))

    # 6. symmetric with zero crossing: x^3 - x, roots -1, 0, 1
    results.append(check(
        "x^3 - x",
        [0.0, -1.0, 0.0, 1.0],
        {-1.0: 1, 0.0: 1, 1.0: 1}))

    # 7. Wilkinson-style mildly ill-conditioned: roots 1..10
    results.append(check(
        "roots 1..10",
        multiply_out(range(1, 11)),
        {float(i): 1 for i in range(1, 11)},
        tol=1e-4))

    # 8. large/small coefficient scale
    results.append(check(
        "scaled coefficients",
        [c * 1e6 for c in multiply_out([-3, 0.5, 7])],
        {-3.0: 1, 0.5: 1, 7.0: 1}))

    # 9. a root at the Cauchy bound edge region, mixed signs
    results.append(check(
        "mixed signs cubic",
        multiply_out([-100.0, 0.25, 9.0]),
        {-100.0: 1, 0.25: 1, 9.0: 1}))

    print("-" * 60)
    passed = sum(results)
    print("%d/%d tests passed" % (passed, len(results)))
    raise SystemExit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
