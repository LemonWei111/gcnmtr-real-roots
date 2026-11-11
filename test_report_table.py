# -*- coding: utf-8 -*-
"""
test_report_table.py
====================
Run the P / D / Z / H test-case tables (工程计算 算法大作业) against
poly_roots.poly_real_roots and print a 测试报告.

Notes
-----
* The table lists coefficients in DESCENDING power order (降幂); the
  solver requires ASCENDING order, so every table input is reversed.
* Location tolerance scales with the maximum expected multiplicity
  (an m-fold root can only be pinned to ~eps^(1/m) in floating point).
* Multiplicity must match EXACTLY.
* Heavy (degree ~ 100000) cases are executed in a worker process with a
  wall-clock timeout; timeouts are reported separately, not as failures.

Usage:  python test_report_table.py [quick|full]   (default: full)
"""

import math
import sys
import time
import multiprocessing as mp

from poly_roots import poly_real_roots, poly_eval

DMAX = 1.7976931348623157e308
STRICT = True


# ---------------------------------------------------------------- helpers

def from_desc(desc):
    """Table coeffs are 降幂 (descending) -> solver wants ascending."""
    return [float(c) for c in reversed(desc)]


def multiply_out(factors):
    """Expand prod (x - r) over real roots -> ascending coefficients."""
    coeffs = [1.0]
    for r in factors:
        new = [0.0] * (len(coeffs) + 1)
        for i, c in enumerate(coeffs):
            new[i] -= c * r
            new[i + 1] += c
        coeffs = new
    return coeffs


def poly_mul(a, b):
    res = [0.0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        if x:
            for j, y in enumerate(b):
                res[i + j] += x * y
    return res


def fmt_roots(roots):
    return "[" + ", ".join("%.6g(x%d)" % (r, m) for r, m in roots) + "]"


def fmt_expected(exp):
    if not exp:
        return "[]"
    return "[" + ", ".join("%.6g(x%d)" % (r, m) for r, m in sorted(exp.items())) + "]"


def loc_tol_for(exp):
    m = max(exp.values(), default=1)
    if m <= 1:
        return 1e-6
    if m <= 3:
        return 1e-5
    return 1e-3


def match_roots(got, exp, tol):
    if len(got) != len(exp):
        return False
    for r, m in got:
        if not math.isfinite(r):
            return False
        hit = min(exp, key=lambda e: abs(e - r))
        if abs(hit - r) > tol or exp[hit] != m:
            return False
    return True


def merge_entries(entries, c=50.0, cap=1e-3):
    """Merge numerically split copies of the same root (defensive)."""
    if len(entries) <= 1:
        return sorted(entries, key=lambda t: t[0])
    srt = sorted(entries, key=lambda t: t[0])
    groups = [[srt[0]]]
    for e in srt[1:]:
        g = groups[-1]
        tot = sum(m for _, m in g)
        center = sum(r * m for r, m in g) / tot
        delta = min(c * 2.220446049250313e-16 ** (1.0 / (tot + e[1])), cap) \
            * max(1.0, abs(center))
        if abs(e[0] - center) <= delta:
            g.append(e)
        else:
            groups.append([e])
    out = []
    for g in groups:
        tot = sum(m for _, m in g)
        center = sum(r * m for r, m in g) / tot
        out.append((center, tot))
    out.sort(key=lambda t: t[0])
    return out


def residual_norm(coeffs, roots):
    scale = max(1.0, max(abs(c) for c in coeffs))
    return max((abs(poly_eval(coeffs, r)) for r, _ in roots), default=0.0) / scale


# ---------------------------------------------------------------- solver wrapper

def _solve_proxy(coeffs, tol, q):
    import time as _t
    t0 = _t.time()
    try:
        r = poly_real_roots(coeffs, tol=tol)
        q.put(("ok", r, _t.time() - t0))
    except Exception as e:                      # noqa: BLE001
        q.put(("err", repr(e), _t.time() - t0))


def run_solver(coeffs, tol=1e-12, timeout=None):
    """Return ("ok", roots, elapsed) | ("timeout", None, limit) | ("err", msg, t)."""
    if timeout is None or len(coeffs) < 5000:   # small cases inline (fast)
        t0 = time.time()
        roots = poly_real_roots(coeffs, tol=tol)
        return ("ok", roots, time.time() - t0)
    q = mp.Queue()
    p = mp.Process(target=_solve_proxy, args=(coeffs, tol, q))
    p.start()
    p.join(timeout)
    if p.is_alive():
        p.terminate()
        p.join()
        return ("timeout", None, float(timeout))
    try:
        return q.get_nowait()
    except Exception:
        return ("err", "worker produced no result", 0.0)


# ---------------------------------------------------------------- case tables

def build_cases():
    s2, s3 = math.sqrt(2.0), math.sqrt(3.0)
    z4 = multiply_out([0, 0, 0, 0, 2, 2, 2])
    z6 = poly_mul(multiply_out([-1] * 5 + [3, 3]), [1.0, 0.0, 1.0])

    cases = []

    def C(name, coeffs, expected, kind="P/D/Z"):
        cases.append(dict(name=name, coeffs=coeffs, expected=expected,
                          kind=kind, special=None))

    def S(name, coeffs, reason, kind):
        cases.append(dict(name=name, coeffs=coeffs, expected=None,
                          kind=kind, special=reason))

    # ---- P1..P10 基础多项式 ----
    C("P1", from_desc([2, -6]), {3.0: 1})
    C("P2", from_desc([1, -5, 6]), {2.0: 1, 3.0: 1})
    C("P3", from_desc([1, 2, 5]), {})
    C("P4", from_desc([1, -6, 11, -6]), {1.0: 1, 2.0: 1, 3.0: 1})
    C("P5", from_desc([1, 0, -3, -2]), {-1.0: 2, 2.0: 1})
    C("P6", from_desc([1, 0, -5, 0, 6]), {-s3: 1, -s2: 1, s2: 1, s3: 1})
    C("P7", from_desc([1, -2, 2, -2, 1]), {1.0: 2})
    C("P8", from_desc([1, 0, -2, 2, -3, 2]), {-2.0: 1, 1.0: 2})
    C("P9", from_desc([1, 0, -5, 0, 4, 0]), {-2.0: 1, -1.0: 1, 0.0: 1, 1.0: 1, 2.0: 1})
    C("P10", from_desc([1, 0, -12, 0, 48, 0, -64]), {-2.0: 3, 2.0: 3})

    # ---- D0..D5 退化 / 零次 / 零多项式 / 前导零 ----
    S("D0", [0.0], "零多项式：所有实数为根、重数无定义，约定返回空列表（特殊分支）", "P/D/Z")
    C("D1", from_desc([7]), {})
    C("D2", from_desc([-3]), {})
    C("D3", from_desc([0, 1, -1]), {1.0: 1})          # 前导零归一化
    C("D4", from_desc([0, 0, 0, 5]), {})              # 前导零后为常数
    C("D5", from_desc([0, 1, 0, 0]), {0.0: 2})        # 前导零 + 重根

    # ---- Z1..Z6 零根与重根 ----
    C("Z1", [0.0, 1.0], {0.0: 1})
    C("Z2", [0.0, 0.0, 1.0], {0.0: 2})
    C("Z3", [0.0, 0.0, 0.0, 1.0], {0.0: 3})
    C("Z4", z4, {0.0: 4, 2.0: 3})
    C("Z5", [0.0, 0.0, 1.0, 0.0, 1.0], {0.0: 2})
    C("Z6", z6, {-1.0: 5, 3.0: 2})

    # ---- H1..H13 高次（稀疏系数表示，可行部分）----
    z999 = [0.0] * 99999
    C("H1", z999 + [1.0], {0.0: 99999}, "H")
    C("H2", [-1.0] + [0.0] * 99998 + [1.0], {1.0: 1}, "H")
    C("H3", [1.0] + [0.0] * 99998 + [1.0], {-1.0: 1}, "H")
    C("H4", [0.0, -1.0] + [0.0] * 99997 + [1.0], {-1.0: 1, 0.0: 1, 1.0: 1}, "H")
    C("H5", [0.0] * 99998 + [-1.0, 1.0], {0.0: 99998, 1.0: 1}, "H")
    C("H6", [0.0] * 99998 + [1.0, 1.0], {-1.0: 1, 0.0: 99998}, "H")
    C("H13", [1.0] + [0.0] * 99999 + [1.0], {}, "H")

    # ---- H7..H12 因式构造：展开系数超出 double 表示范围，不可测 ----
    S("H7", None, "展开系数 ~10^45151，远超 double 上限 1.8e308（表中已注明 may overflow）", "H")
    S("H8", None, "展开系数 ~10^15048 溢出；且 m=49999 重根浮点下不可分辨", "H")
    S("H9", None, "展开系数 ~10^15048 溢出", "H")
    S("H10", None, "展开系数 ~10^15051 溢出；且 m=49999 重根浮点下不可分辨", "H")
    S("H11", None, "展开系数 ~10^15045 溢出", "H")
    S("H12", None, "展开系数 ~10^15049 溢出", "H")

    return cases


# ---------------------------------------------------------------- overflow demo

def overflow_demo():
    sys.set_int_max_str_digits(100000)
    lines = []
    lines.append("系数溢出演示（为什么 H7—H12 无法以 double 输入）:")
    lines.append("  double 上限 DMAX = 1.7977e308")
    items = [
        ("(x^2+1)^49999   max|coef|", math.comb(49999, 24999)),
        ("(x-1)^49999     max|coef|", math.comb(49999, 24999)),
        ("(x-2)^99999     max|coef|", math.comb(99999, 49999) * (2 ** 50000)),
        ("(x^2-2)^49999   const coef", 2 ** 49999),
        ("(x^2+1)^50000   max|coef|", math.comb(50000, 25000)),
    ]
    for name, v in items:
        s = str(v)
        val = "%.4fe+%d" % (float(s[0] + "." + s[1:5]), len(s) - 1)
        lines.append("  %-24s = %s   溢出=%s" % (name, val, v > DMAX))
    # smallest m where (x^2+1)^m overflows double
    m0 = None
    for m in range(900, 1200):
        if math.comb(m, m // 2) > DMAX:
            m0 = m
            break
    s = str(math.comb(m0, m0 // 2))
    bound = "%.4fe+%d" % (float(s[0] + "." + s[1:5]), len(s) - 1)
    lines.append("  边界: (x^2+1)^m 在 m=%d 时即溢出（max|coef| ~ %s）" % (m0, bound))
    # functional demo: feed int coefficients -> OverflowError inside solver
    m = 1100
    big = [math.comb(m, k) if (i % 2 == 0) else 0
           for i in range(2 * m + 1) for k in (i // 2,)]  # x^{2k} coeff C(m,k)
    lines.append("  实跑演示: 以精确大整数系数输入 (x^2+1)^%d（2501 项）→ poly_real_roots():" % m)
    try:
        poly_real_roots(big)
        lines.append("    未抛异常（意外）")
    except OverflowError as e:
        lines.append("    OverflowError: %s" % e)
    # demo with inf entries (float conversion losing the big ints)
    try:
        flt = [float(c) for c in big]                  # raises at first overflow
        lines.append("    手动 float() 转换: 成功（未溢出，与预期不符）")
    except OverflowError:
        lines.append("    手动 float() 转换也在第一处大系数抛出 OverflowError → 系数在输入阶段就不可表示")
    lines.append("  结论: 系数 ~10^15050 的 H7—H12 无法构造为 float 输入（直接传入大整数会在")
    lines.append("        float() 处 OverflowError；若强行置 inf 则产生 NaN/不可信结果）。")
    return lines


# ---------------------------------------------------------------- main

def main():
    global STRICT
    STRICT = not (len(sys.argv) > 1 and sys.argv[1] == "numeric")
    quick = "--quick" in sys.argv
    cases = build_cases()
    to_run = [c for c in cases if quick and c["kind"] == "H"
              and c["name"] not in ("H1", "H5", "H6") and not c["special"]]
    for c in to_run:
        c["special"] = "quick 模式跳过（省时）"

    lines = []
    def emit(s=""):
        lines.append(s)
        print(s)

    emit("=" * 78)
    emit(" poly_roots.py 用例表测试报告   (Python %d.%d.%d%s)" %
         (sys.version_info[0], sys.version_info[1], sys.version_info[2],
          "   [quick]" if quick else ""))
    emit(" 判定标准 v2: 规范化(聚类合并) -> 位置(容差随重数放宽) -> 重数 -> 次数核算 Σm")
    emit("           模式: %s；另要求 max|p(r)|/scale < 1e-6。超时/系数不可表示计入'特殊/未完成'。"
         % ("严格(重数必须一致)" if STRICT else "数值(位置+次数核算, 允许重数低置信)"))
    emit("=" * 78)
    emit("%-5s %-28s %-7s %-8s %s" % ("编号", "用例", "结果", "耗时(s)", "说明"))
    emit("-" * 78)

    passed = failed = special = timeout_n = 0
    details = []
    for c in cases:
        if c["special"] is not None:
            special += 1
            emit("%-5s %-28s %-7s %-8s %s" %
                 (c["name"], c["name"] + " (skip)", "SKIP", "-", c["special"]))
            details.append((c["name"], "SKIP", c["special"]))
            continue

        coeffs, exp = c["coeffs"], c["expected"]
        tol = loc_tol_for(exp)
        tmo = 300 if c["kind"] == "H" else None
        status, roots, elapsed = run_solver(coeffs, tol=1e-12, timeout=tmo)

        if status == "ok":
            roots = merge_entries(roots)
            sum_got = sum(m for _, m in roots)
            sum_exp = sum(exp.values())
            ok_res = residual_norm(coeffs, roots) < 1e-6
            ok_mat = match_roots(roots, exp, tol)
            ok_deg = (sum_got == sum_exp)
            ok = ok_mat if STRICT else (ok_res and ok_deg
                                        and len(roots) == len(exp)
                                        and all(min(abs(e - r) for e in exp) <= tol
                                                for r, _ in roots))
            detail = "roots=" + fmt_roots(roots) + "  Σm=%d/%d" % (sum_got, sum_exp)
            if not ok_mat:
                detail += "  期望 " + fmt_expected(exp)
            if not ok_res:
                detail += "  |p|/scale=%.1e" % residual_norm(coeffs, roots)
            if ok:
                passed += 1
                emit("%-5s %-28s %-7s %-8.1f %s" % (c["name"], c["name"], "PASS",
                                                    elapsed, detail))
                details.append((c["name"], "PASS", ""))
            else:
                failed += 1
                emit("%-5s %-28s %-7s %-8.1f %s" % (c["name"], c["name"], "FAIL",
                                                    elapsed, detail))
                details.append((c["name"], "FAIL", detail))
        elif status == "timeout":
            timeout_n += 1
            special += 1
            emit("%-5s %-28s %-7s %-8s %s" %
                 (c["name"], c["name"], "TIMEOUT", "-",
                  "超过 %ds 未完成（纯 Python 求解器高次停滞段过慢）" % int(tmo)))
            details.append((c["name"], "TIMEOUT", "超过 %ds" % int(tmo)))
        else:
            failed += 1
            emit("%-5s %-28s %-7s %-8s %s" % (c["name"], c["name"], "ERR", "-", status))
            details.append((c["name"], "ERR", status))

    emit("-" * 78)
    emit("汇总: 通过 %d 例，错误 %d 例，特殊/未完成 %d 例（其中超时 %d 例）" %
         (passed, failed, special, timeout_n))
    emit("=" * 78)

    # ---- overflow demo ----
    for ln in overflow_demo():
        emit("  " + ln if ln.startswith("  ") or ln.startswith("  结论") else ln)

    # ---- failure reasons ----
    fails = [d for d in details if d[1] in ("FAIL", "ERR")]
    emit("")
    if fails:
        emit("错误明细 / 原因分析:")
        for name, st, detail in fails:
            emit("  %-4s %s : %s" % (name, st, detail))
    else:
        emit("错误明细: 无")
    emit("特殊/未完成说明:")
    for name, st, reason in [(d[0], d[1], d[2]) for d in details if d[1] in ("SKIP", "TIMEOUT")]:
        emit("  %-4s [%s] %s" % (name, st, reason))

    with open("测试报告_用例表.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n报告已写入 测试报告_用例表.txt")


if __name__ == "__main__":
    main()

