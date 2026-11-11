"""
solve_p5.py
===========
Driver for the course assignment: solve

    p5(x) = x^5 - 6x^3 - x^2 - 5x + 5

with the general solver in poly_roots.py, then verify the result by
(1) per-root residuals, (2) Vieta's relations, (3) numpy.roots as an
independent cross-check.
"""

from poly_roots import poly_real_roots, poly_eval

# Coefficients in ascending order: 5 - 5x - x^2 - 6x^3 + 0*x^4 + x^5
COEFFS = [-246, 2, 0, 0, 0, 32]


def main():
    roots = poly_real_roots(COEFFS, tol=1e-12)

    print("p5(x) = x^5 - 6x^3 - x^2 - 5x + 5")
    print("=" * 52)
    print("real roots found: %d (degree 5)" % len(roots))
    print("-" * 52)
    print("%4s  %20s  %4s  %12s" % ("#", "root", "mult", "residual"))
    for i, (r, m) in enumerate(roots, 1):
        print("%4d  %20.12f  %4d  %12.3e" % (i, r, m, abs(poly_eval(COEFFS, r))))
    print("-" * 52)

    # Vieta: sum of all roots (with multiplicity) must equal -a4/a5.
    total = sum(r * m for r, m in roots)
    print("Vieta check: sum of real roots = %.15f (target -a4/a5 = 0)" % total)
    print("(a nonzero sum indicates the missing complex pair's real part)")

    try:
        import numpy as np
        all_roots = np.roots(COEFFS[::-1])      # numpy wants descending
        real_ref = sorted(r.real for r in all_roots if abs(r.imag) < 1e-9)
        print("-" * 52)
        print("numpy.roots cross-check (real roots):")
        for r in real_ref:
            print("    %.12f" % r)
        match = len(real_ref) == len(roots) and all(
            abs(a - b) < 1e-8 for a, b in zip(real_ref, [r for r, _ in roots])
        )
        print("agreement with our solver:", match)
        complex_pair = [r for r in all_roots if abs(r.imag) >= 1e-9]
        print("remaining complex pair:")
        for r in complex_pair:
            print("    %.12f %+.12fi" % (r.real, r.imag))
    except ImportError:
        pass


if __name__ == "__main__":
    main()
