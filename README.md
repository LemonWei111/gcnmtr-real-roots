# gcnmtr-real-roots

A hybrid solver for **all real roots with multiplicities** of a univariate
real-coefficient polynomial

\[
p(x)=a_0+a_1x+\cdots+a_nx^n .
\]

The engine is a scalar specialization of **GCNMTr** (Generalized Continuous
Newton Method with residual-trust adaptive time step), wrapped in a
deflation loop, a Decimal multiplicity certifier, a Descartes completeness
gate, and a status-aware output contract.

The design target is **honest completeness under a fixed complexity budget**:
no-real-root cases are *proved*, found roots are *certified where possible*,
and anything the algorithm cannot prove is returned as `unverified` instead
of being silently treated as "no root".

---

## Features

- **GCNMTr scalar engine** — ratio test `rho`, three-interval time-step
  update, explicit rollback; Levenberg guard at `p' = 0` returns
  `stationary` (correct continuous-Newton behaviour), not a fake fix.
- **Deflation loop** — one root at a time, re-polished on the original
  polynomial before each deflation to limit error accumulation.
- **Multiplicity handling** — estimate `p'^2/(p'^2 - p p'')`, modified
  Newton `x <- x - m0*p/p'`, and high-precision **Decimal certification**
  of the multiplicity when it is ambiguous.
- **Descartes completeness gate** — `V(q) = V(q(-x)) = 0` is a *proof*
  that no real root remains; `O(n)` per round, absorbed by the main path.
- **Sample probe backstop** — if every flow start stalls but Descartes
  allows roots, a 16-point sign-change probe gives a constructive
  intermediate-value evidence, or the result is marked `unverified`.
- **Status-aware contract** — `ok` / `partial` / `unverified` /
  `verified_no_real_roots` / `input_error` / `overflow_risk` /
  `degree_too_high`, with warnings and a `certified` flag.
- **Canonical output** — numerically split copies of the same multiple
  root are merged with multiplicity-scaled tolerance; failed merges keep
  the original entries and emit a warning.

---

## Complexity

| Path | Time | Space |
|---|---|---|
| Main path (`completeness="fast"`, default) | `O(n^2 * k)` | `O(n)` |
| Descartes gate | `O(n^2)` | `O(1)` |
| Adaptive starts (<= 32) | constant factor <= 4.6x | `O(1)` |
| Sample probe | `O(n^2 log(1/eps))`, absorbed by `k` | `O(1)` |
| Decimal certification | `O(n*m)` high-precision words, only when `n <= 300` and multiplicity is ambiguous | `O(n)` |
| Canonical merge | `O(r log r)`, `r <= n` | `O(r)` |

The asymptotic complexity of the main path is **not** increased by the
completeness layers; they are constant-factor or absorbed by `k`.

---

## Install

No third-party dependencies (standard library only; Python 3.9+).

```bash
git clone https://github.com/<your-name>/gcnmtr-real-roots.git
cd gcnmtr-real-roots
```

---

## Usage

Coefficients are in **ascending** order: `coeffs[i]` multiplies `x**i`.

```python
from poly_roots import poly_real_roots

# x^3 - 6x^2 + 11x - 6 = (x-1)(x-2)(x-3)
roots = poly_real_roots([-6, 11, -6, 1])
print(roots)          # [(1.0, 1), (2.0, 1), (3.0, 1)]

# (x+1)^2 (x-2)
roots = poly_real_roots([-2, -3, 0, 1])
print(roots)          # [(-1.0, 2), (2.0, 1)]

# no real roots
print(poly_real_roots([1, 0, 1]))   # []
```

Diagnostics / status contract:

```python
res = poly_real_roots([1, 0, 1], diagnostics=True)
print(res.status)      # "verified_no_real_roots" (Descartes proof)
print(res.roots)       # []
print(res.warnings)    # ()
print(res.certified)   # True
```

Explicit overflow handling:

```python
res = poly_real_roots([1.0, 0.0, 1e400], diagnostics=True)
print(res.status)      # "overflow_risk"
```

`strict=True` turns `input_error` / `overflow_risk` into exceptions:

```python
poly_real_roots([], strict=True)          # ValueError
poly_real_roots([0.0, 0.0], strict=True)  # ValueError: zero polynomial
```

Raw (un-merged) output for debugging:

```python
poly_real_roots(coeffs, raw=True)
```

---

## Status values

| `status` | Meaning | Determinism |
|---|---|---|
| `ok` | all roots found, multiplicities certified where applicable | high |
| `partial` | roots found, some multiplicity not certified | medium |
| `unverified` | roots may remain; no proof of absence | low, explicit |
| `verified_no_real_roots` | Descartes proved no real root remains | **deterministic** |
| `input_error` | empty / zero polynomial / non-finite coefficient | rejected |
| `overflow_risk` | coefficient exceeds double range | rejected + hint |
| `degree_too_high` | degree exceeds `max_degree` | rejected + estimate |

---

## What this solver does *not* claim

- It does **not** give a mathematical proof of "no root missed" when
  roots exist. That requires Sturm sequences or a full VCA isolation;
  a `completeness="verified"` upgrade path is reserved for that.
- It is **not** suitable for `n ~ 1e5` dense polynomials: the main path
  is `O(n^2 k)` and deflation error accumulates with `n`.
- Coefficients that overflow `double` cannot be represented; pass a
  factored form or reduce the degree instead of expanding.

---

## Design notes

The engine is a **scalar specialization** of GCNMTr. The QR factorization
and finite-difference Jacobian of the original multi-dimensional algorithm
degenerate for a scalar polynomial; the analytic derivative by Horner is
strictly better there. What is kept from GCNMTr is the ratio test, the
three-interval time-step update, the accept/rollback rule, and the
residual-trust spirit. The Levenberg term is documented as a numerical
guard at `p' = 0`, not as a fix for the stationary point.

Completeness is layered:

1. Descartes `V = 0` proves absence.
2. Adaptive multi-start covers the Fujiwara root bound.
3. A 16-point sign-change probe gives constructive evidence when flow
   stalls.
4. Everything else is marked `unverified` with a warning.

---

## License

MIT (or your preferred license). See `LICENSE`.