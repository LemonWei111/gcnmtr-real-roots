import sys, math
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from poly_roots import _deflate, _fujiwara_bound, _scale, poly_eval, poly_eval_with_deriv

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 10.5
plt.rcParams['axes.linewidth'] = 0.9
plt.rcParams['savefig.bbox'] = 'tight'

coeffs = [5.0, -5.0, -1.0, -6.0, 0.0, 1.0]
roots = [-2.5797143434027817, 0.6341132506507355, 2.6142441504434344]
crit = [-1.9141469335102235, 2.0114711356526772]

def p(x):
    return x**5 - 6*x**3 - x**2 - 5*x + 5

def dp(x):
    return 5*x**4 - 18*x**2 - 2*x - 5

# ---------------- Figure 1: function and derivative ----------------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.2, 6.8), sharex=True)
xs = np.linspace(-3.25, 3.25, 1200)
ys = p(xs)
ax1.plot(xs, ys, color='#1f4e79', lw=1.8, label=r'$p_5(x)$')
ax1.axhline(0, color='0.35', lw=0.9, ls='-')
for i, r in enumerate(roots, 1):
    ax1.plot([r], [0], 'o', ms=7, mfc='#c00000', mec='white', mew=1.0, zorder=5)
    ax1.axvline(r, color='#c00000', lw=0.8, ls='--', alpha=0.45)
ax1.plot(crit, p(np.array(crit)), '^', ms=7, mfc='#7f7f7f', mec='white', mew=0.8, zorder=5)
ax1.annotate(r'$x_1=-2.5797$', xy=(roots[0], 0), xytext=(-22, 76),
             textcoords='offset points', fontsize=9.5, color='#c00000',
             arrowprops=dict(arrowstyle='->', lw=0.8, color='#c00000', shrinkA=0, shrinkB=4))
ax1.annotate(r'$x_2=0.6341$', xy=(roots[1], 0), xytext=(8, 40),
             textcoords='offset points', fontsize=9.5, color='#c00000',
             arrowprops=dict(arrowstyle='->', lw=0.8, color='#c00000', shrinkA=0, shrinkB=4))
ax1.annotate(r'$x_3=2.6142$', xy=(roots[2], 0), xytext=(-100, 75),
             textcoords='offset points', fontsize=9.5, color='#c00000',
             arrowprops=dict(arrowstyle='->', lw=0.8, color='#c00000', shrinkA=0, shrinkB=4))
ax1.annotate(r'$p(-1.9141)=27.29$', xy=(crit[0], p(crit[0])), xytext=(-15, 26),
             textcoords='offset points', fontsize=8.8, color='0.30',
             arrowprops=dict(arrowstyle='->', lw=0.7, color='0.45', shrinkA=0, shrinkB=4))
ax1.annotate(r'$p(2.0115)=-25.01$', xy=(crit[1], p(crit[1])), xytext=(-18, -32),
             textcoords='offset points', fontsize=8.8, color='0.30',
             arrowprops=dict(arrowstyle='->', lw=0.7, color='0.45', shrinkA=0, shrinkB=4))
ax1.set_ylabel(r'$p_5(x)$')
ax1.set_ylim(-78, 155)
ax1.grid(True, ls=':', lw=0.55, alpha=0.55)
ax1.legend(loc='upper left', frameon=False)
ax1.set_title('(a) 多项式函数与三个实根', loc='left', fontsize=11, fontweight='bold')

ys2 = dp(xs)
ax2.plot(xs, ys2, color='#2e7d32', lw=1.6, label=r"$p_5'(x)$")
ax2.axhline(0, color='0.35', lw=0.9)
for c in crit:
    ax2.plot([c], [0], 'o', ms=6.5, mfc='#7f7f7f', mec='white', mew=0.8, zorder=5)
    ax2.axvline(c, color='#7f7f7f', lw=0.8, ls='--', alpha=0.55)
ax2.text(-3.12, 250, r"$p_5'>0$", fontsize=9, color='#2e7d32')
ax2.text(-0.95, -60, r"$p_5'<0$", fontsize=9, color='#2e7d32')
ax2.text(2.18, 250, r"$p_5'>0$", fontsize=9, color='#2e7d32')
ax2.annotate(r'$-1.9141$', xy=(crit[0], 0), xytext=(-8, -22), textcoords='offset points',
             fontsize=8.8, color='0.30', ha='center')
ax2.annotate(r'$2.0115$', xy=(crit[1], 0), xytext=(6, -22), textcoords='offset points',
             fontsize=8.8, color='0.30', ha='center')
ax2.set_ylabel(r"$p_5'(x)$")
ax2.set_xlabel(r'$x$')
ax2.set_ylim(-95, 360)
ax2.grid(True, ls=':', lw=0.55, alpha=0.55)
ax2.legend(loc='upper left', frameon=False)
ax2.set_title("(b) 导函数符号与单调区间", loc='left', fontsize=11, fontweight='bold')
ax2.xaxis.set_major_locator(MultipleLocator(0.5))
fig.tight_layout(h_pad=1.4)
fig.savefig('report_assets/fig1_p5_function.png', dpi=240, facecolor='white')
plt.close(fig)

# ---------------- Figure 2: flow convergence ----------------
def flow_trace(coeffs, x0, tol=1e-12, max_iter=400):
    eta_a, eta_1, eta_2 = 1e-6, 0.25, 0.75
    gamma_1, gamma_2 = 2.0, 0.5
    dt = 1.0
    lam = 1e-10
    x = float(x0)
    scale = _scale(coeffs)
    x_bound = 10.0 * max(1.0, _fujiwara_bound(coeffs))
    p0, dp0 = poly_eval_with_deriv(coeffs, x)
    r0 = abs(p0)
    rec = [(0, r0)]
    if r0 <= tol * scale:
        return rec, 'converged', x
    if dp0 != 0.0:
        sN0 = -p0 / dp0
        if math.isfinite(sN0) and abs(sN0) > x_bound:
            dt = max(1e-2, x_bound / abs(sN0))
    best_x, best_r = x, r0
    for it in range(1, max_iter + 1):
        p, dpp = poly_eval_with_deriv(coeffs, x)
        r = abs(p)
        if r <= tol * scale:
            return rec, 'converged', x
        denom = dpp * dpp + lam
        if denom == 0.0:
            return rec, 'stationary', best_x
        sN = -p * dpp / denom
        s = dt / (1.0 + dt) * sN
        if s == 0.0:
            return rec, ('stationary' if dpp == 0.0 else 'dt_underflow'), best_x
        x_new = x + s
        if not math.isfinite(x_new) or abs(x_new) > x_bound:
            return rec, 'diverged', best_x
        p_new = poly_eval(coeffs, x_new)
        r_new = abs(p_new)
        actual = r - r_new
        pred = r - abs(p + dpp * s)
        rho = actual / pred if (actual > 0.0 and pred > 0.0) else -1.0
        if abs(1.0 - rho) < eta_1:
            dt = gamma_1 * dt
        elif abs(1.0 - rho) < eta_2:
            pass
        else:
            dt = gamma_2 * dt
        if dt > 1e6:
            dt = 1e6
        if rho >= eta_a:
            x, r = x_new, r_new
            rec.append((it, r))
            if r_new < best_r:
                best_x, best_r = x_new, r_new
            lam = max(lam * 0.3, 1e-14)
            if r_new <= tol * scale:
                return rec, 'converged', x_new
        else:
            lam = min(lam * 10.0, 1.0)
            if dt < 1e-15:
                return rec, 'dt_underflow', best_x
    return rec, 'max_iter', best_x

q1 = [5.0, -5.0, -1.0, -6.0, 0.0, 1.0]
q2 = _deflate(q1, 0.6341132506507355)
q3 = _deflate(q2, -2.579714343402782)
cases = [
    (q1, 0.0, '第 1 阶段（5 次，$x_0=0$）', '#1f4e79'),
    (q2, -_fujiwara_bound(q2), '第 2 阶段（4 次，$x_0=-4.7320$）', '#c55a11'),
    (q3, -_fujiwara_bound(q3) / 3.0, '第 3 阶段（3 次，$x_0=-1.2971$）', '#2e7d32'),
]
fig, ax = plt.subplots(figsize=(7.2, 3.0))
for q, x0, lab, color in cases:
    rec, reason, x = flow_trace(q, x0)
    its = [it for it, _ in rec]
    vals = [max(r, 1e-16) for _, r in rec]
    ax.semilogy(its, vals, '-o', ms=4.2, lw=1.5, color=color, label=lab)
    ax.annotate('%.1e' % vals[-1], xy=(its[-1], vals[-1]), xytext=(5, 0),
                textcoords='offset points', fontsize=8, color=color, va='center')
ax.set_xlabel('已接受的流迭代步数')
ax.set_ylabel(r'$|q_k(x_k)|$')
ax.set_xlim(-0.4, 13.6)
ax.set_ylim(1e-16, 1e3)
ax.grid(True, which='major', ls=':', lw=0.55, alpha=0.55)
ax.grid(True, which='minor', ls=':', lw=0.35, alpha=0.35)
ax.legend(loc='upper right', frameon=False, fontsize=9)
fig.tight_layout()
fig.savefig('report_assets/fig2_convergence.png', dpi=240, facecolor='white')
plt.close(fig)
print('figures written')







