"""
poly_roots.py
=============

一个通用求解器，用于求单变量实系数多项式

    p(x) = a[0] + a[1]*x + ... + a[n]*x**n

的全部实根（含重数）。

核心算法（思想未变——牛顿流 + 降次/缩并）：
    1. 预处理：去掉为零的首项系数，并提取 x = 0 处的根
       （两者都是 O(n) 的切片操作），然后归一化为首一多项式。
    2. 反复通过积分连续牛顿流
           dx/dt = -p(x) / p'(x)
       来找到当前多项式的"一个"实根；
       采用显式欧拉离散化，时间步长 h 由基于残差的信赖域规则调整
       （残差下降则接受/放大 h，否则拒绝/缩小 h）。h = 1 即退化为
       经典牛顿迭代。分母中加入 Levenberg 型正则项 lam，使流在
       p'(x) = 0 的点仍然有定义（这就是 GCNMTr 中"广义"的部分）。
    3. 在"原始"多项式上用牛顿迭代精修每个根。当残差安全地高于
       舍入误差下限、且重数估计 m_hat = p'^2/(p'^2 - p*p'') 接近
       整数 m0 >= 2 时，改用修正步
           x <- x - m0 * p / p'
       使重根也能恢复二次收敛。
    4. 通过合成除法（synthetic deflation）确定重数。若计数结果
       模棱两可（停止时的残差比处于临界值）且次数较小，则在
       高精度 Decimal 算术下"认证"该 (位置, 重数) 对：先精修根，
       再通过反复合成除法得到 Taylor 系数 p^(j)(r)/j!，第一个
       非零的 Taylor 系数即给出重数。这使得重数成为"系数"的
       属性，而非嘈杂的降次循环的属性。
    5. 用 (x - r)**m 降次，并继续，直到流从所有起点都停滞
       （剩余根为非实根）或次数 <= 1。
    6. 可选地对输出做规范化：把表示同一个根（数值上被拆开的重根）
       的条目合并，重数相加，并对合并结果重新认证。

复杂度
------
双精度路径下，时间 O(n^2 * k)，k 为小的流迭代常数，空间 O(n)，
与原求解器相同。
可选的 Decimal 认证只在次数 <= 300 且重数模棱两可（或需验证
被拆开的簇）时运行，代价为 O(n * m) 次高精度字操作，从不改变
主路径的渐近复杂度。规范化合并在 r <= n 个输出根上为 O(r log r)。

输出约定
--------
默认（canonical=True）返回一个已排序的"互不相同"的实根列表及其
重数，每个根恰好出现一次。
传入 raw=True / canonical=False 可得到未合并的列表（用于调试）。
"""

import math
import os
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
from dataclasses import dataclass

__all__ = ["poly_real_roots", "poly_eval", "poly_eval_with_deriv"]

# 双精度机器 epsilon（2^-52 的近似值）
_EPS = 2.220446049250313e-16
# Decimal 认证的默认工作精度（十进制位数）
_CERT_DIGITS = 60
# 允许运行 Decimal 认证的最大次数
_CERT_MAX_DEG = 300
# 合并判定的系数 C（乘以 eps^(1/m) 得到容差）
_CANON_C = 50.0
# 合并容差的上限
_CANON_CAP = 1e-3
# 调试开关：环境变量 POLY_DEBUG=1 时打印中间过程
_DEBUG = os.environ.get("POLY_DEBUG") == "1"

@dataclass(frozen=True)
class RootResult:
    roots: list          # 列表[(根, 重数)]
    status: str          # "ok" | "partial" | "unverified" | "input_error"
                         # | "overflow_risk" | "degree_too_high"
    warnings: tuple      # 警告信息元组
    certified: bool      # 结果是否经过认证


def _descartes_changes(q):
    """
    系数序列中的符号变化次数（忽略零）。
    Descartes 规则：V(q) = #{正实根，计重数} + 2m, m >= 0。
    因此 V(q) == 0 是"q 没有正实根"的"证明"。O(n)。
    """
    # 先把每个系数映射为符号：正 -> 1，负 -> -1，零 -> 0
    signs = [1 if c > 0.0 else (-1 if c < 0.0 else 0) for c in q]
    # 去掉零，只保留非零符号
    signs = [s for s in signs if s != 0]
    # 统计相邻符号发生变化的次数
    return sum(1 for a, b in zip(signs, signs[1:]) if a != b)


def _reflect(q):
    """返回 q(-x) 的系数：翻转奇次项的符号。O(n)。"""
    return [c if i % 2 == 0 else -c for i, c in enumerate(q)]


def _bisect(coeffs, a, b, tol, scale, max_iter=200):
    """
    在存在符号变化的括号上进行二分。返回最终括号的中点，
    若端点不构成有效括号则返回 None。O(n * max_iter)。
    """
    # 计算两端点的函数值
    fa = poly_eval(coeffs, a)
    fb = poly_eval(coeffs, b)
    # 端点本身就是根的情形
    if fa == 0.0:
        return a
    if fb == 0.0:
        return b
    # 两端同号，不能二分
    if fa * fb > 0.0:
        return None
    for _ in range(max_iter):
        # 取中点
        m = 0.5 * (a + b)
        fm = poly_eval(coeffs, m)
        # 中点为根，或区间已足够小
        if fm == 0.0 or abs(b - a) <= tol * max(1.0, abs(m)):
            return m
        # 根据符号决定保留哪一半
        if fa * fm < 0.0:
            b, fb = m, fm
        else:
            a, fa = m, fm
    # 迭代次数用尽，返回最终中点
    return 0.5 * (a + b)


def _sample_probe(coeffs, B, tol, n_samples=16):
    """
    廉价的完整性兜底检查，每次调用 O(n)。

    在 [-B, B] 上采样 n_samples 个点；第一个符号变化就是
    （由介值定理给出的）该处存在实根的"构造性证明"，
    随后用 _bisect 把根求出来。找不到符号变化时返回 None——
    这"不是"不存在的证明，只是说廉价探测没有找到证据。
    """
    if n_samples < 2:
        return None
    # 残差阈值用的归一化因子
    scale = _scale(coeffs)
    # 在 [-B, B] 上均匀取 n_samples 个点
    grid = [-B + 2.0 * B * i / (n_samples - 1) for i in range(n_samples)]
    # 计算所有采样点的函数值
    vals = [poly_eval(coeffs, x) for x in grid]
    for i in range(n_samples - 1):
        a, b = grid[i], grid[i + 1]
        fa, fb = vals[i], vals[i + 1]
        # 采样点本身是根
        if fa == 0.0:
            return a
        if fb == 0.0:
            return b
        # 相邻点符号变化 => 存在根，用二分求出来
        if fa * fb < 0.0:
            root = _bisect(coeffs, a, b, tol, scale)
            if root is not None:
                return root
    return None


def _make_result(roots, status, warnings, certified, diagnostics):
    """向后兼容的返回：默认返回列表，若要求诊断则返回 RootResult。"""
    if diagnostics:
        return RootResult(list(roots), status, tuple(warnings), certified)
    return roots


def poly_eval(coeffs, x):
    """用 Horner 格式在 x 处求多项式值。时间 O(n)。"""
    result = 0.0
    # 从最高次项开始，每次乘 x 再加下一项
    for a in reversed(coeffs):
        result = result * x + a
    return result


def poly_eval_with_deriv(coeffs, x):
    """一次 Horner 扫描同时返回 (p(x), p'(x))。时间 O(n)，空间 O(1)。"""
    p = 0.0   # p 的当前值
    dp = 0.0  # p' 的当前值
    for a in reversed(coeffs):
        # 先更新导数（利用上一轮的 p），再更新 p
        dp = dp * x + p
        p = p * x + a
    return p, dp


def _eval_p_dp_ddp(coeffs, x):
    """一次 Horner 扫描同时返回 (p, p', p'')。时间 O(n)，空间 O(1)。"""
    p = 0.0
    dp = 0.0
    ddp = 0.0
    for a in reversed(coeffs):
        # 依次递推：二阶导 <- 一阶导 <- p
        ddp = ddp * x + dp
        dp = dp * x + p
        p = p * x + a
    return p, dp, ddp


def _deflate(coeffs, r):
    """用 (x - r) 做合成除法；返回商多项式系数。"""
    n = len(coeffs) - 1
    quotient = [0.0] * n
    b = coeffs[n]  # 从最高次项开始
    for i in range(n - 1, -1, -1):
        quotient[i] = b
        b = coeffs[i] + b * r
    return quotient


def _deflate_power(coeffs, r, m):
    """除以 (x - r)**m；O(m * n)。"""
    q = list(coeffs)
    # 连续做 m 次单次降次
    for _ in range(m):
        q = _deflate(q, r)
    return q


def _scale(coeffs):
    """残差阈值用的归一化因子。"""
    return max(1.0, max(abs(c) for c in coeffs))


def _fujiwara_bound(coeffs):
    """
    Fujiwara 根界：每个根 r 都满足
        |r| <= 2 * max_{1<=i<=n} |a_{n-i}/a_n|^(1/i)。
    既用于流的 x_bound，也用于分层起点的构造，
    使可达区间随多项式缩放，而不随 x0 缩放。
    """
    n = len(coeffs) - 1
    if n < 1:
        return 1.0
    lead = coeffs[-1]  # 首项系数
    if lead == 0.0:
        return 1.0
    B = 0.0
    for i in range(1, n + 1):
        a = coeffs[n - i]
        if a != 0.0:
            # 取 |a_{n-i}/a_n|^(1/i) 的最大值
            B = max(B, abs(a / lead) ** (1.0 / i))
    return 2.0 * B


def _build_starts(B, count=7):
    """
    分层起点：一小撮固定点（0, ±1, ±0.5）廉价地覆盖常见情形，
    再加上 `count` 个在 [-B, B] 上均匀分布的点，后者随多项式的
    根界缩放，而非随 x0 缩放。去重并裁剪到 [-1.01*B, 1.01*B]。
    """
    B = max(1.0, float(B))
    count = max(1, int(count))
    # 只要一个起点时直接返回 0
    if count == 1:
        return [0.0]
    # 均匀分布点
    pts = [-B + 2.0 * B * i / (count - 1) for i in range(count)]
    # 固定附加点，覆盖常见情形
    extras = [0.0, 1.0, -1.0, 0.5, -0.5]
    out, seen = [], set()
    # 先放固定点，再放均匀点；去重并裁剪范围
    for s in extras + pts:
        s = float(s)
        key = round(s, 12)
        if key in seen or abs(s) > B * 1.01:
            continue
        seen.add(key)
        out.append(s)
    return out


def _flow_root(coeffs, x0, tol=1e-12, max_iter=400):
    """
    GCNMTr（算法 4.4）的标量特化版本。

    保留自 GCNMTr 的部分：
      - rho_k = (|F_k|-|F_{k+1}|) / (|F_k|-|F_k+J_k s_k|)   (式 4.52)
      - 三区间 dt 更新：gamma1=2, eta1=0.25, eta2=0.75, gamma2=0.5
                                                            (式 4.53)
      - 当 rho_k >= eta_a = 1e-6 时接受，否则回滚 x
    标量偏离（已记录，非缺陷）：
      - J = p' 由 Horner 得到；J^T 的 QR 分解平凡（R=|p'|, Q=sign(p')）
      - Levenberg lam 是 p'=0 处的数值保护；它使 s=0（流停滞），
        这是连续牛顿在"非根驻点"处的正确行为，而非为 p'=0 做的修补。
    边界用 Fujiwara 界（非基于 x0），使大根可达。
    返回 (x, reason)，reason 属于
    {converged, stationary, diverged, dt_underflow, near_miss, max_iter}。
    """
    eta_a, eta_1, eta_2 = 1e-6, 0.25, 0.75
    gamma_1, gamma_2 = 2.0, 0.5
    dt = 1.0                  # 标量情形：整步；由式 4.53 缩放
    lam = 1e-10               # Levenberg 正则项初值
    x = float(x0)
    scale = _scale(coeffs)

    # --- 用 Fujiwara 界替代基于 x0 的 x_bound ---
    x_bound = 10.0 * max(1.0, _fujiwara_bound(coeffs))

    # 计算起点的函数值和导数，先判断是否已经在根附近
    p0, dp0 = poly_eval_with_deriv(coeffs, x)
    r0 = abs(p0)
    if r0 <= tol * scale:
        return x, "converged"
    # 若第一步牛顿步会越界，先缩小 dt 以防止过冲
    if dp0 != 0.0:
        sN0 = -p0 / dp0
        if math.isfinite(sN0) and abs(sN0) > x_bound:
            dt = max(1e-2, x_bound / abs(sN0))

    best_x, best_r = x, r0
    for _ in range(max_iter):
        # 当前点的 p 和 p'
        p, dp = poly_eval_with_deriv(coeffs, x)
        r = abs(p)
        # 已足够接近根
        if r <= tol * scale:
            return x, "converged"
        # Levenberg 正则化后的分母
        denom = dp * dp + lam
        if denom == 0.0:
            return best_x, "stationary"
        # 牛顿方向（带正则化）
        sN = -p * dp / denom
        # 按 dt 缩放后的步长
        s = dt / (1.0 + dt) * sN
        if s == 0.0:
            # 区分真正的驻点停滞与 dt 下溢导致的停滞
            if dp == 0.0:
                return best_x, "stationary"
            return best_x, "dt_underflow"
        x_new = x + s
        # 越界或非有限 => 发散
        if not math.isfinite(x_new) or abs(x_new) > x_bound:
            return best_x, "diverged"
        p_new = poly_eval(coeffs, x_new)
        r_new = abs(p_new)

        # --- 比值检验（式 4.52 的标量形式）---
        actual = r - r_new                      # 实际下降量
        pred = r - abs(p + dp * s)              # 线性模型预测下降量
        # 只有实际下降与预测下降都为正时才定义比值
        rho = actual / pred if (actual > 0.0 and pred > 0.0) else -1.0

        # --- 三区间 dt 更新（式 4.53）---
        if abs(1.0 - rho) < eta_1:
            dt = gamma_1 * dt          # 比值很好：放大步长
        elif abs(1.0 - rho) < eta_2:
            pass                        # 比值尚可：保持步长
        else:
            dt = gamma_2 * dt           # 比值差：缩小步长
        # 限制步长上限，防止数值爆炸
        if dt > 1e6:
            dt = 1e6

        # --- 接受 / 拒绝 ---
        if rho >= eta_a:
            x, r = x_new, r_new
            if r_new < best_r:
                best_x, best_r = x_new, r_new
            # 接受后减小正则项（更相信牛顿方向）
            lam = max(lam * 0.3, 1e-14)
            # 即使因舍入使 actual <= 0，只要已到根附近就返回
            if r_new <= tol * scale:
                return x_new, "converged"
        else:
            # 拒绝：增大正则项，缩小步长
            lam = min(lam * 10.0, 1.0)
            if dt < 1e-15:
                return best_x, "dt_underflow"
    # 迭代次数用尽：做最后判断
    if best_r <= max(1e-8, tol * scale):
        return best_x, "converged"
    if best_r < 0.5 * r0:                 # 确有进展，精修可能救回
        return best_x, "near_miss"
    return best_x, "max_iter"


def _polish_root(coeffs, x, tol=1e-13, max_iter=50):
    """
    在"原始"多项式上精修一个根。

    第一阶段是原求解器的普通牛顿迭代（因此单根精度完全不变）。
    第二阶段仅在重数估计接近整数 m0 >= 2 且 |p| 安全地高于舍入
    下限时进入，使用修正步
    x <- x - m0 * p / p'  （重根下二次收敛）。
    """
    xx = float(x)
    # ---- 第一阶段：带回溯的牛顿迭代（绝不跳到另一个根）----
    # 只有在 |p| 下降时才走纯牛顿步；当流已停在舍入下限时，
    # 不接受任何步，保留当前点（跳跃会污染降次）。
    best_x = xx
    best_r = abs(poly_eval(coeffs, xx))
    for _ in range(max_iter):
        f, df = poly_eval_with_deriv(coeffs, xx)
        if df == 0.0:
            break
        step = f / df
        # 步长非有限或过大则终止
        if not math.isfinite(step) or abs(step) > 10.0 * max(1.0, abs(xx)):
            break
        lam = 1.0
        xn = xx - step
        rn = abs(poly_eval(coeffs, xn))
        tries = 0
        # 回溯：不断折半步长，直到残差下降
        while rn >= best_r and tries < 40:
            lam *= 0.5
            tries += 1
            xn = xx - lam * step
            rn = abs(poly_eval(coeffs, xn))
        if rn >= best_r:
            break
        xx = xn
        best_x, best_r = xn, rn
        # 步长已足够小，收敛
        if abs(lam * step) <= tol * max(1.0, abs(xx)):
            break

    # ---- 第二阶段：重数加速精修（用于重根）----
    scale = _scale(coeffs)
    floor = 1e3 * _EPS * scale
    p, dp, ddp = _eval_p_dp_ddp(coeffs, xx)
    m0 = None
    # 只在导数非零且残差高于舍入下限时估计重数
    if dp != 0.0 and abs(p) > floor:
        den = dp * dp - 2.0 * p * ddp
        if den > 0.0:
            mh = dp * dp / den
            k = round(mh)
            # 估计值接近整数 k（>=2）才采用修正步
            if 2 <= k <= 500 and abs(mh - k) <= 0.02 * k:
                m0 = k
    if m0 is None:
        return xx

    best_x, best_r = xx, abs(p)
    for _ in range(60):
        p, dp, ddp = _eval_p_dp_ddp(coeffs, xx)
        if dp == 0.0 or not math.isfinite(p):
            break
        # 重数修正步
        step = m0 * p / dp
        if not math.isfinite(step) or abs(step) > 10.0 * max(1.0, abs(xx)):
            break
        xn = xx - step
        if not math.isfinite(xn):
            break
        rn = abs(poly_eval(coeffs, xn))
        # 残差明显上升则终止，避免跳到别处
        if rn > 10.0 * best_r + floor:
            break
        xx = xn
        if rn < best_r:
            best_x, best_r = xn, rn
        # 步长已足够小，收敛
        if abs(step) <= tol * max(1.0, abs(xx)):
            break
    return best_x


# ------------------------------------------------------------------ Decimal

def _dec_eval3(cd, x):
    """Decimal 版本的 Horner：同时返回 (p, p', p'')。"""
    p = Decimal(0)
    dp = Decimal(0)
    ddp = Decimal(0)
    for a in reversed(cd):
        ddp = ddp * x + dp
        dp = dp * x + p
        p = p * x + a
    return p, dp, ddp


def _dec_eval(cd, x):
    """Decimal 版本的 Horner 求值。"""
    p = Decimal(0)
    for a in reversed(cd):
        p = p * x + a
    return p


def _certify_at(coeffs, r, max_mult, digits):
    """
    在指定精度下认证根位置与重数。
    通过局部对数斜率（相邻点函数值之比的对数）估计重数。
    """
    with localcontext() as ctx:
        ctx.prec = digits                          # 设定工作精度
        cd = [Decimal(c) for c in coeffs]          # 系数转 Decimal
        n = len(cd) - 1
        if n < 1:
            return (float(r), None, False)
        # 判断"噪声"水平的阈值
        tiny = Decimal(10) ** (-(digits - 15))
        x = Decimal(r)
        best_x, best_p = x, abs(_dec_eval(cd, x))

        # ---- 带回溯的牛顿迭代，且考虑重数 ----
        for _ in range(150):
            p, dp, ddp = _dec_eval3(cd, x)
            if dp == 0:
                break
            mult = Decimal(1)                      # 默认按单根处理
            den = dp * dp - 2 * p * ddp
            if den > 0:
                mh = dp * dp / den
                # 重数估计四舍五入到最近整数
                m0 = int(mh.to_integral_value(rounding=ROUND_HALF_EVEN))
                # 若接近整数（>=2）则用修正步
                if 2 <= m0 <= 2000 and abs(mh - m0) <= Decimal("0.02") * m0:
                    mult = Decimal(m0)
            step = mult * p / dp
            lam = Decimal(1)
            xn = x - step
            rn = abs(_dec_eval(cd, xn)) if xn.is_finite() else None
            tries = 0
            # 回溯，直到残差下降
            while rn is None or rn > best_p:
                lam /= 2
                tries += 1
                if tries > 30:
                    break
                xn = x - lam * step
                rn = abs(_dec_eval(cd, xn)) if xn.is_finite() else None
            if rn is None or rn >= best_p:
                break                      # 无法继续下降
            best_x, best_p = xn, rn
            x = xn
            if abs(step * lam) <= tiny * max(Decimal(1), abs(x)):
                break
        x = best_x

        # ---- 通过局部对数斜率确定重数 ----
        base = max(Decimal(1), abs(x))
        scale = Decimal(0)                     # 用于估计噪声水平
        pw = Decimal(1)
        for i in range(n + 1):
            scale += abs(cd[i]) * pw
            pw *= base
        noise = scale * Decimal(10) ** (-(digits - 8))
        ln2 = Decimal(2).ln()
        first_slope = None
        m_bound = max(1, min(max_mult, n))
        last = None
        run = 0                                # 连续一致估计的计数
        m_found = None
        # 在 8 个不同 eta 尺度下探测（base*1e-9 .. base*1e-2）
        for k in range(0, 8):
            eta = base * Decimal(10) ** (-9 + k)
            p1 = _dec_eval(cd, x + eta)
            p2 = _dec_eval(cd, x + 2 * eta)
            if p1 == 0 or p2 == 0:
                run = 0
                continue
            a1, a2 = abs(p1), abs(p2)
            # 低于噪声水平的样本不可信
            if a1 < noise or a2 < noise:
                run = 0
                continue
            # 用 log2 比值估计局部幂次（即重数）
            slope = (a2 / a1).ln() / ln2
            if first_slope is None:
                first_slope = slope
            cand = int(slope.to_integral_value(rounding=ROUND_HALF_EVEN))
            # 接近整数且在界内则视为候选
            if 1 <= cand <= m_bound and abs(slope - cand) <= Decimal("0.02") * cand:
                if cand == last:
                    run += 1
                else:
                    last, run = cand, 1
                # 连续两次一致才确认
                if run >= 2:
                    m_found = cand
                    break
            else:
                last, run = None, 0
        if m_found is None:
            # 样本良好但局部斜率 ~ 0：该点不是根
            if first_slope is not None and abs(first_slope) < Decimal("0.4"):
                return (float(x), 0, False)
            return (float(x), None, False)
        return (float(x), m_found, True)


def _certify_root(coeffs, r, max_mult):
    """
    高精度下认证 (位置, 重数)，并自适应工作精度。
    返回 (r_float, m, ok)。
    """
    # 依次尝试 1x, 2x, 4x 默认精度，直到认证成功
    for digits in (_CERT_DIGITS, 2 * _CERT_DIGITS, 4 * _CERT_DIGITS):
        r_c, m_c, ok = _certify_at(coeffs, r, max_mult, digits)
        if ok:
            return (r_c, m_c, True)
        if m_c == 0:                      # 被认证为"不是根"
            return (r_c, 0, False)
    return (float(r), None, False)


# --------------------------------------------------------------- canonical

def _canonicalize(entries, coeffs, allow_certify, cluster_tol=None):
    """
    合并代表同一个（数值上被拆开的）根的条目。

    返回 (merged_entries, merge_warnings)。一个足够接近、应当合并、
    但其合并后的重数无法认证的簇，"不会"在没有提示的情况下被
    静默保留为拆开的条目：保留原始条目并发出警告。
    """
    if len(entries) <= 1:
        return sorted(entries, key=lambda t: t[0]), []

    def delta_of(m, center):
        """根据重数 m 与中心位置给出合并容差。"""
        if cluster_tol is not None:
            return float(cluster_tol)
        if allow_certify:
            # 重数越大，容差越大（eps^(1/m)）
            return min(_CANON_C * _EPS ** (1.0 / m), _CANON_CAP) * max(1.0, abs(center))
        return 1e-9 * max(1.0, abs(center))

    srt = sorted(entries, key=lambda t: t[0])
    # 按位置排序后，贪心地构造簇
    groups = [[srt[0]]]
    for e in srt[1:]:
        g = groups[-1]
        tot = sum(mm for _, mm in g)
        # 以重数加权中心作为簇的代表位置
        center = sum(rr * mm for rr, mm in g) / tot
        m_tot = tot + e[1]
        delta = delta_of(m_tot, center)
        # 若与当前簇中心足够接近则并入
        if abs(e[0] - center) <= delta:
            g.append(e)
        else:
            groups.append([e])

    out = []
    merge_warnings = []
    for g in groups:
        # 单元素簇直接保留
        if len(g) == 1:
            out.append(g[0])
            continue
        tot = sum(mm for _, mm in g)
        center = sum(rr * mm for rr, mm in g) / tot
        accepted = False
        # 尝试用 Decimal 认证合并后的 (位置, 重数)
        if allow_certify and coeffs is not None:
            r_c, m_c, ok = _certify_root(coeffs, center, len(coeffs) - 1)
            if (ok and m_c is not None and 1 <= m_c <= len(coeffs) - 1
                    and abs(r_c - center) <= 5.0 * delta_of(m_tot, center)):
                out.append((r_c, m_c))
                accepted = True
        # 认证失败：不静默合并，保留原始条目并发出警告
        if not accepted:
            merge_warnings.append(
                "cluster near r=%r (sum m=%d) not merged: "
                "certification failed; original entries kept" % (center, tot))
            out.extend(g)
    out.sort(key=lambda t: t[0])
    return out, merge_warnings


def poly_real_roots(coeffs, tol=1e-12, *, canonical=True,
                    cluster_tol=None, precision="auto", raw=False,
                    diagnostics=False, max_degree=None,
                    completeness="fast", strict=False):
    """
    Compute all real roots of p(x) = sum(coeffs[i] * x**i).

    Completeness budget (completeness="fast", default):
      1. Descartes gate, O(n) per round:
           V(q) == 0 is a *proof* that q has no positive real root;
           V(q(-x)) == 0 likewise for negative roots.  Both zero
           (and q(0) != 0) certifies "no real roots remain".
      2. Adaptive starts, <= 32, O(1) extra factor:
           n_starts = max(7, min(V+ + V-, 32)).
      3. Sample probe, O(n) per round:
           if every flow start stalls but V+ + V- > 0, sample 16
           points on [-B, B]; a sign change is a constructive proof
           and _bisect recovers the root.
      4. Status, O(1):
           "ok" / "partial" / "unverified" / "input_error" /
           "overflow_risk" / "degree_too_high".

    completeness="verified" is reserved for a future optional
    VCA/Sturm backstop on the residual; it is accepted here but
    currently behaves the same as "fast".
    """
    # 参数合法性检查：precision 只能是 auto/double/high
    if precision not in ("auto", "double", "high"):
        raise ValueError("precision must be 'auto', 'double' or 'high'")
    # 参数合法性检查：completeness 只能是 fast/verified
    if completeness not in ("fast", "verified"):
        raise ValueError("completeness must be 'fast' or 'verified'")
    # raw=True 时强制关闭规范化输出
    if raw:
        canonical = False

    # ---- input guard -------------------------------------------------
    # 输入保护：coeffs 为 None 时按 strict 决定抛错还是返回错误结果
    if coeffs is None:
        if strict:
            raise ValueError("coeffs is None")
        return _make_result([], "input_error", ("coeffs is None",),
                            False, diagnostics)
    # 把系数统一转换成 float
    try:
        a = [float(c) for c in coeffs]
    except OverflowError:
        # 系数超出 double 表示范围
        if strict:
            raise
        return _make_result(
            [], "overflow_risk",
            ("coefficient exceeds double range; pass factored form "
             "or reduce degree",), False, diagnostics)
    except (TypeError, ValueError) as e:
        # 存在非数值系数
        if strict:
            raise ValueError("non-numeric coefficient: %s" % e)
        return _make_result([], "input_error",
                            ("non-numeric coefficient: %s" % e,),
                            False, diagnostics)
    # 逐个检查系数是否为有限值（排除 nan/inf）
    for i, c in enumerate(a):
        if not math.isfinite(c):
            if strict:
                raise ValueError("non-finite coefficient at index %d" % i)
            return _make_result([], "input_error",
                                ("non-finite coefficient at index %d" % i,),
                                False, diagnostics)
    # 零多项式：所有实数都是根，无法给出有限根表
    if all(c == 0.0 for c in a):
        if strict:
            raise ValueError("zero polynomial: every real is a root")
        return _make_result([], "input_error",
                            ("zero polynomial: every real is a root",),
                            False, diagnostics)

    # ---- preprocessing (unchanged) -----------------------------------
    # 去掉末尾的高阶零系数（即降低名义次数）
    hi = len(a)
    while hi > 1 and a[hi - 1] == 0.0:
        hi -= 1
    a = a[:hi]
    # 统计低阶零系数个数，即 x=0 作为根的重数
    lo = 0
    while lo < len(a) - 1 and a[lo] == 0.0:
        lo += 1
    mult_zero = lo
    # 去掉低阶零系数（把 x 的因子整体提出）
    a = a[lo:]
    # 实际（去零后）多项式的次数
    n = len(a) - 1
    # 次数超过用户设定的上限时直接返回
    if max_degree is not None and n > max_degree:
        if strict:
            raise ValueError("degree %d exceeds max_degree %d"
                             % (n, max_degree))
        return _make_result(
            [], "degree_too_high",
            ("degree %d exceeds max_degree %d; O(n^2 k) expected"
             % (n, max_degree),), False, diagnostics)
    # 常数多项式：只有零根（若前面统计到重数）
    if n < 1:                      # constant polynomial
        roots = [(0.0, mult_zero)] if mult_zero else []
        return _make_result(roots, "ok", (), True, diagnostics)
    # 归一化：把首项系数化为 1，改善数值稳定性
    lead = a[-1]
    if lead != 1.0:
        a = [c / lead for c in a]
    # 保存归一化后的原始系数，用于后续抛光与验证
    original = list(a)

    # 根列表：先把 x=0 的根（含重数）放进去
    roots = [(0.0, mult_zero)] if mult_zero else []
    # q 是当前待求根的工作多项式（会随收缩 deflation 变化）
    q = list(a)
    # 是否启用根的重数认证（精度非 double 且次数不超过阈值）
    certify_ok = ((precision != "double")
                  and (len(original) - 1 <= _CERT_MAX_DEG))
    # 整体结果是否已被认证
    certified = True
    # 警告信息收集
    warnings_list = []
    # 是否存在未能验证的剩余根
    unverified = False

    # ---- main loop ---------------------------------------------------
    # 主循环：只要工作多项式次数 >= 2 就继续找根
    while len(q) - 1 >= 2:
        # Layer 1: Descartes gate, O(n).  V+ == V- == 0 is a proof.
        # 第一层：Descartes 符号变化数门控，O(n)
        V_pos = _descartes_changes(q)          # 正根符号变化数上界
        V_neg = _descartes_changes(_reflect(q))  # 负根（q(-x)）符号变化数上界
        # 正负符号变化数都为 0 且常数项非零，则证明已无实根
        if V_pos == 0 and V_neg == 0 and q[0] != 0.0:
            if _DEBUG:
                print("[descartes] certified no real roots remain")
            break

        # Layer 2: adaptive starts, O(1) factor.
        # 第二层：自适应起点数，依据 Fujiwara 界 B 构造起点
        B = max(1.0, _fujiwara_bound(q))
        # 起点数量随符号变化数自适应，限制在 [7, 32]
        n_starts = max(7, min(V_pos + V_neg, 32))
        starts = _build_starts(B, n_starts)

        # reason-routed multi-start
        # 多起点流式求根，并按返回原因路由处理
        found = None
        near_miss = None
        for s in starts:
            r_cand, reason = _flow_root(q, s, tol)
            if _DEBUG:
                print("[flow] start=%r reason=%s x=%r" % (s, reason, r_cand))
            # 成功收敛，直接采用
            if reason == "converged":
                found = r_cand
                break
            # 近似命中，先记录第一个，后续再抛光验证
            if reason == "near_miss" and near_miss is None:
                near_miss = r_cand
        # 若没有收敛结果但有近似命中，则用原始多项式抛光并校验残差
        if found is None and near_miss is not None:
            r_pol = _polish_root(original, near_miss)
            if abs(poly_eval(original, r_pol)) <= 1e-8 * _scale(original):
                found = r_pol
            elif _DEBUG:
                print("[flow] near_miss rejected: |p|=%.3e"
                      % abs(poly_eval(original, r_pol)))

        # Layer 3: sample probe, O(n) per round.
        # 第三层：若流式方法全部失败，则在 [-B, B] 上采样探测变号
        if found is None:
            probe = _sample_probe(q, B, tol)
            if probe is not None:
                found = probe
                warnings_list.append(
                    "flow stalled (V+=%d, V-=%d); root recovered "
                    "by sample probe" % (V_pos, V_neg))
            else:
                # 采样也找不到变号：剩余根无法验证，终止主循环
                unverified = True
                warnings_list.append(
                    "flow stalled at all %d starts (V+=%d, V-=%d); "
                    "sample probe found no sign change; remaining "
                    "roots unverified" % (len(starts), V_pos, V_neg))
                break

        # polish + multiplicity + deflate (unchanged in spirit)
        # 抛光根、确定重数、并做多项式收缩（deflation）
        r = _polish_root(original, found)
        if _DEBUG:
            print("[loop] flow=%r polished=%r |p|=%.3e"
                  % (found, r, abs(poly_eval(q, r))))
        # 保存收缩前的 q，便于重数认证失败时回退
        q_save = q
        # 先按一次重数收缩
        q = _deflate(q, r)
        m = 1
        qs = _scale(q)
        # 若 r 仍是收缩后多项式的近似根，则继续累加重数
        while len(q) > 1 and abs(poly_eval(q, r)) < 1e-6 * qs:
            q = _deflate(q, r)
            m += 1
            qs = _scale(q)
        # rho 衡量 r 在收缩后多项式上的相对残差
        rho = (abs(poly_eval(q, r)) / qs
               if (len(q) > 1 and qs) else math.inf)

        # 在需要且允许的情况下，对重数做认证
        if certify_ok and (m >= 2 or rho < 1e-2
                           or not math.isfinite(rho)):
            r_c, m_c, ok_c = _certify_root(original, r, len(original) - 1)
            if _DEBUG:
                print("[cert] r_c=%r m_c=%s ok=%s" % (r_c, m_c, ok_c))
            # 认证结果合理则采纳认证后的根与重数，并重新收缩
            if (ok_c and m_c is not None
                    and 1 <= m_c <= len(q_save) - 1
                    and abs(r_c - r) <= 0.1 * max(1.0, abs(r))
                    and m_c <= 2 * m + 2):
                r, m = r_c, m_c
                q = _deflate_power(q_save, r, m)
            elif m >= 2:
                # 认证失败但重数 >= 2：标记为未完全认证
                certified = False
                warnings_list.append(
                    "multiplicity of root %r not certified" % r)
        elif m >= 2 and not certify_ok:
            # 不满足认证条件但重数 >= 2：同样标记为未完全认证
            certified = False
            warnings_list.append(
                "multiplicity of root %r not certified "
                "(degree > %d or precision='double')"
                % (r, _CERT_MAX_DEG))

        # 记录该根及其重数
        roots.append((r, m))

    # ---- linear remainder --------------------------------------------
    # 剩余一次多项式：直接用 -b/a 求根并抛光
    if len(q) - 1 == 1:
        r = _polish_root(original, -q[0] / q[1])
        roots.append((r, 1))

    # ---- canonical output (warning-aware) ----------------------------
    # 规范化输出：合并近似重复根、排序，并收集相关警告
    if canonical:
        roots, merge_warns = _canonicalize(
            roots, original, certify_ok, cluster_tol)
        if merge_warns:
            warnings_list.extend(merge_warns)
            certified = False
    else:
        # 非规范化模式：只按根值排序
        roots.sort(key=lambda item: item[0])

    # ---- status ------------------------------------------------------
    # 根据是否未验证 / 是否完全认证决定最终状态
    if unverified:
        status = "unverified"
    elif not certified:
        status = "partial"
    else:
        status = "ok"

    # 组装并返回结果对象
    return _make_result(roots, status, tuple(warnings_list),
                        certified, diagnostics)

