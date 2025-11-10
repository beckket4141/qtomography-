from __future__ import annotations

import cmath
from dataclasses import dataclass
from typing import List, Tuple, Optional

import numpy as np


# Optional galois backend
try:
    import galois as _galois  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    _galois = None


def _primitive_root(p: int) -> complex:
    return cmath.exp(2j * cmath.pi / p)


def _is_prime_power(n: int) -> Tuple[int, int]:
    """检查n是否为素数幂，返回(p, k)如果n=p^k，否则返回(0, 0)。
    
    注意：必须p是素数，所以6=6^1不是素数幂（因为6不是素数）。
    """
    # 首先检查p是否为素数
    def _is_prime(p: int) -> bool:
        if p < 2:
            return False
        if p == 2:
            return True
        if p % 2 == 0:
            return False
        # 检查从3到sqrt(p)的奇数因子
        i = 3
        while i * i <= p:
            if p % i == 0:
                return False
            i += 2
        return True
    
    for p in range(2, n + 1):
        if n % p != 0:
            continue
        # 检查p是否为素数
        if not _is_prime(p):
            continue
        k = 0
        m = n
        while m % p == 0:
            m //= p
            k += 1
        if m == 1:
            return p, k
    return 0, 0


class _FieldBackend:
    def __init__(self, d: int) -> None:
        p, k = _is_prime_power(d)
        if p == 0:
            raise ValueError(f"dimension {d} is not a prime power")
        self.d = d
        self.p = p
        self.k = k

    def elements(self) -> List[int]:
        raise NotImplementedError

    def add(self, a: int, b: int) -> int:
        raise NotImplementedError

    def mul(self, a: int, b: int) -> int:
        raise NotImplementedError

    def trace(self, a: int) -> int:
        raise NotImplementedError


class _GaloisBackend(_FieldBackend):
    def __init__(self, d: int) -> None:
        super().__init__(d)
        if _galois is None:
            raise RuntimeError("galois library not available")
        # Construct field; this raises if d is not prime power
        self.GF = _galois.GF(d)
        # Get all elements: GF.Range(0, d) or create array [0, 1, ..., d-1]
        try:
            # Try using Range method (newer API)
            elements_array = self.GF.Range(0, d)
        except (AttributeError, TypeError):
            # Fallback: create array directly
            elements_array = self.GF(list(range(d)))
        self._elements = [int(x) for x in elements_array]
        # Map int -> field element
        self._to_el = {i: self.GF(i) for i in range(d)}

    def elements(self) -> List[int]:
        return list(self._elements)

    def add(self, a: int, b: int) -> int:
        return int(self._to_el[a] + self._to_el[b])

    def mul(self, a: int, b: int) -> int:
        return int(self._to_el[a] * self._to_el[b])

    def trace(self, a: int) -> int:
        # Compute field trace Tr_{GF(p^k)/GF(p)}(a) = sum_{i=0}^{k-1} a^{p^i}
        x = self._to_el[a]
        acc = self.GF(0)
        pp = 1
        for _ in range(self.k):
            acc += x ** pp
            pp *= self.p
        return int(acc)


class _MinimalGFBackend(_FieldBackend):
    """Minimal GF(p^k) for fallback. Matches previous implementation semantics."""

    def __init__(self, d: int) -> None:
        super().__init__(d)
        # choose fixed irreducible polynomials for limited cases
        p, k = self.p, self.k
        if k == 1:
            self._poly = None
        elif p == 2 and k == 2:
            self._poly = [1, 1, 1]  # x^2 + x + 1
        elif p == 2 and k == 4:
            self._poly = [1, 0, 0, 1, 1]  # x^4 + x + 1
        elif p == 3 and k == 2:
            self._poly = [1, 0, 1]  # x^2 + 1
        else:
            raise NotImplementedError("GF(p^k) not implemented for given (p,k) in fallback backend")

    def elements(self) -> List[int]:
        return list(range(self.d))

    def add(self, a: int, b: int) -> int:
        if self.k == 1:
            return (a + b) % self.p
        res = 0
        carry = 1
        for _ in range(self.k):
            da = (a // carry) % self.p
            db = (b // carry) % self.p
            dc = (da + db) % self.p
            res += dc * carry
            carry *= self.p
        return res

    def _int_to_poly(self, x: int) -> List[int]:
        coeffs = []
        for _ in range(self.k):
            coeffs.append(x % self.p)
            x //= self.p
        return coeffs

    def _poly_to_int(self, coeffs: List[int]) -> int:
        x = 0
        base = 1
        for c in coeffs:
            x += (c % self.p) * base
            base *= self.p
        return x

    def _poly_mul(self, a: List[int], b: List[int]) -> List[int]:
        p = self.p
        res = [0] * (len(a) + len(b) - 1)
        for i, ai in enumerate(a):
            for j, bj in enumerate(b):
                res[i + j] = (res[i + j] + ai * bj) % p
        return res

    def _poly_mod(self, a: List[int], mod_poly_low_to_high: List[int]) -> List[int]:
        p = self.p
        a = a[:]
        md = len(mod_poly_low_to_high) - 1
        # Convert low->high to high->low for leading coefficient operations
        mod_high = list(reversed(mod_poly_low_to_high))
        while len(a) >= len(mod_poly_low_to_high):
            # remove leading zeros
            while a and a[-1] == 0:
                a.pop()
            if len(a) < len(mod_poly_low_to_high):
                break
            factor = a[-1]
            deg = len(a) - len(mod_poly_low_to_high)
            # subtract factor * x^deg * mod_poly
            for i, c in enumerate(mod_high):
                ai = deg + (len(mod_high) - 1 - i)
                a[ai] = (a[ai] - factor * c) % p
        while len(a) and a[-1] == 0:
            a.pop()
        while len(a) < md:
            a.append(0)
        return a

    def mul(self, a: int, b: int) -> int:
        if self.k == 1:
            return (a * b) % self.p
        A = self._int_to_poly(a)
        B = self._int_to_poly(b)
        prod = self._poly_mul(A, B)
        mod_poly = list(reversed(self._poly))  # store low->high for mod
        prod = self._poly_mod(prod, mod_poly)
        return self._poly_to_int(prod)

    def _frobenius(self, a: int) -> int:
        # a^p in GF(p^k)
        # fast exponent
        def pow_mul(x: int, n: int) -> int:
            r = 1
            b = x
            while n:
                if n & 1:
                    r = self.mul(r, b)
                b = self.mul(b, b)
                n >>= 1
            return r
        return pow_mul(a, self.p)

    def trace(self, a: int) -> int:
        if self.k == 1:
            return a % self.p
        acc = 0
        ap = a
        for _ in range(self.k):
            acc = self.add(acc, ap)
            ap = self._frobenius(ap)
        return acc % self.p


def _get_field_backend(d: int) -> _FieldBackend:
    # Prefer galois backend; fallback to minimal backend if not available
    if _galois is not None:
        try:
            return _GaloisBackend(d)
        except Exception:
            pass
    return _MinimalGFBackend(d)


@dataclass
class MUBDesign:
    dimension: int
    projectors: np.ndarray  # (m, d, d)
    groups: np.ndarray  # (m,)
    measurement_matrix: np.ndarray  # (m, d*d)


def _build_bases_ff(d: int, gf: _FieldBackend) -> List[np.ndarray]:
    """Finite-field quadratic/linear phase formula; valid and recommended only for p>2."""
    if gf.p == 2:
        raise ValueError("Finite-field formula is not valid for p=2; use method='wh'")
    omega = _primitive_root(gf.p)
    def chi(x: int) -> complex:
        return omega ** gf.trace(x)
    comp_basis = np.eye(d, dtype=complex)
    bases: List[np.ndarray] = [comp_basis.T]
    for c in gf.elements():
        vecs = np.zeros((d, d), dtype=complex)
        for gamma in gf.elements():
            amp = np.zeros(d, dtype=complex)
            for alpha in gf.elements():
                a2 = gf.mul(alpha, alpha)
                term1 = gf.mul(c, a2)
                term2 = gf.mul(gamma, alpha)
                phase = gf.add(term1, term2)
                amp[alpha] = chi(phase)
            amp = amp / np.linalg.norm(amp)
            vecs[:, gamma] = amp
        bases.append(vecs)
    return bases


def _build_bases_wh(d: int, gf: _FieldBackend) -> List[np.ndarray]:
    """Weyl-Heisenberg/Pauli (symplectic) style construction.

    Builds d+1 bases: B_infty (computational) and B_c as eigenbasis of W_c = Z_c X_1.
    This approach is valid for all prime powers; for p=2 this aligns with stabilizer-style MUBs.
    """
    omega = _primitive_root(gf.p)
    def chi(x: int) -> complex:
        return omega ** gf.trace(x)

    # Computational basis (columns)
    comp_basis = np.eye(d, dtype=complex).T
    bases: List[np.ndarray] = [comp_basis]

    elements = gf.elements()
    # Build index mapping: element int -> column index
    idx_of = {a: i for i, a in enumerate(elements)}

    # X_1: shift by field +1
    one = 1  # element '1' is int 1 in our encoding for both backends
    X1 = np.zeros((d, d), dtype=complex)
    for a in elements:
        i_in = idx_of[a]
        a1 = gf.add(a, one)
        i_out = idx_of[a1]
        X1[i_out, i_in] = 1.0

    # Z_c diagonal operators
    Z_ops: List[np.ndarray] = []
    for c in elements:
        Zc = np.zeros((d, d), dtype=complex)
        for a in elements:
            i = idx_of[a]
            Zc[i, i] = chi(gf.mul(c, a))
        Z_ops.append(Zc)

    # Bases for each c as eigenspaces of W_c = Z_c X_1
    for c_idx, Zc in enumerate(Z_ops):
        Wc = Zc @ X1
        eigvals, eigvecs = np.linalg.eig(Wc)
        # Orthonormalize columns
        q, _ = np.linalg.qr(eigvecs)
        bases.append(q)
    return bases


def _int_to_bits(x: int, nbits: int) -> np.ndarray:
    """Convert integer x to length-nbits binary vector (LSB -> index 0)."""
    bits = np.zeros(nbits, dtype=int)
    for i in range(nbits):
        bits[i] = (x >> i) & 1
    return bits


def _pauli_from_uv(u_bits: np.ndarray, v_bits: np.ndarray) -> np.ndarray:
    """Construct Hermitian Pauli operator P(u,v) on N qubits.

    - u_bits, v_bits: length-N arrays over {0,1}
    - Single-qubit mapping:
        (0,0) -> I
        (1,0) -> X
        (0,1) -> Z
        (1,1) -> i * Z @ X   (ensures Hermitian with eigenvalues +-1)
    """
    I = np.eye(2, dtype=complex)
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)

    N = len(u_bits)
    op = 1
    for q in range(N):
        u = int(u_bits[q])
        v = int(v_bits[q])
        if u == 0 and v == 0:
            m = I
        elif u == 1 and v == 0:
            m = X
        elif u == 0 and v == 1:
            m = Z
        else:  # u == 1 and v == 1
            m = 1j * (Z @ X)
        op = np.kron(op, m) if isinstance(op, np.ndarray) else m
    return op


def _build_bases_pow2_stabilizer(d: int, gf: _FieldBackend) -> List[np.ndarray]:
    """Stabilizer/Pauli construction for d = 2^k using symplectic spread.

    Key idea: Work over GF(2^k) with the trace bilinear form B(x,y)=Tr(xy).
    Let G be the Gram matrix of B in the polynomial basis {1, x, x^2, ...}:
        G[i,j] = Tr(e_i * e_j) in GF(2).
    For each field element a, define the linear map M(a): v -> a*v (as N×N matrix
    over GF(2)), and set S(a) = G @ M(a). Then S(a) is symmetric over GF(2)
    because multiplication is self-adjoint w.r.t. B. Further, for a≠b,
    S(a)-S(b) = G @ M(a-b) is invertible. The commuting set for slope "a" is
    generated by N Hermitian Pauli operators labeled by (u, S(a) u) where u is
    the standard basis vector. This yields d bases plus the computational Z-basis,
    totaling d+1 MUBs.
    """
    if gf.p != 2:
        raise ValueError("_build_bases_pow2_stabilizer requires characteristic 2")

    N = gf.k  # d = 2^N
    bases: List[np.ndarray] = []

    # Basis 0: computational Z-basis (columns)
    bases.append(np.eye(d, dtype=complex).T)

    # Precompute basis elements e_j as ints (1, x, x^2, ...)
    e_ints = [(1 << j) for j in range(N)]

    # Build Gram matrix G over GF(2)
    G = np.zeros((N, N), dtype=np.uint8)
    for i in range(N):
        for j in range(N):
            G[i, j] = gf.trace(gf.mul(e_ints[i], e_ints[j])) & 1

    # RNG for projection method
    rng = np.random.default_rng(12345)

    # Iterate over field elements a to produce the remaining d bases
    for a in gf.elements():
        # Build multiplication matrix M(a) in polynomial basis: columns are bits of a*e_j
        M = np.zeros((N, N), dtype=np.uint8)
        for j in range(N):
            prod = gf.mul(a, e_ints[j])
            M[:, j] = _int_to_bits(prod, N)
        # Symmetric matrix S(a) over GF(2)
        S = (G @ M) % 2

        # Generators: N commuting Hermitian Pauli operators labeled by (u, S u)
        generators: List[np.ndarray] = []
        for j in range(N):
            u_bits = np.zeros(N, dtype=int)
            u_bits[j] = 1
            v_bits = (S @ u_bits) % 2
            generators.append(_pauli_from_uv(u_bits, v_bits))

        # Build eigenvectors via projection onto common eigenspaces of generators
        seed = rng.normal(size=d) + 1j * rng.normal(size=d)
        vecs = np.zeros((d, d), dtype=complex)
        for s in range(d):
            b = _int_to_bits(s, N)  # eigenvalue pattern
            v = seed.copy()
            for j in range(N):
                lam = 1.0 if b[j] == 0 else -1.0
                v = 0.5 * (v + lam * (generators[j] @ v))
            nrm = np.linalg.norm(v)
            if nrm < 1e-12:
                v = rng.normal(size=d) + 1j * rng.normal(size=d)
                for j in range(N):
                    lam = 1.0 if b[j] == 0 else -1.0
                    v = 0.5 * (v + lam * (generators[j] @ v))
                nrm = np.linalg.norm(v)
                if nrm < 1e-12:
                    w, U = np.linalg.eigh(generators[0])
                    v = U[:, 0]
                    nrm = np.linalg.norm(v)
            vecs[:, s] = v / (nrm if nrm != 0 else 1.0)

        # Orthonormalize columns
        q, _ = np.linalg.qr(vecs)
        bases.append(q)

    return bases


def build_mub_projectors(
    dimension: int,
    method: str = "wh",
    variant: str = "compact",  # "compact" -> d^2 projectors, "full" -> d(d+1)
) -> MUBDesign:
    """Build (d+1) groups of MUB projectors.

    Parameters:
        dimension: 希尔伯特空间维度，必须是素数幂 d = p^k（p是素数，k≥1）
        method: 构造方法
            - 'wh': Weyl-Heisenberg/Pauli构造（默认）
                * 奇数特征 (p>2): 使用有限域二次相位公式
                * 特征2 (p=2): 使用Stabilizer/Pauli构造
                * 支持所有素数幂维度（安装galois库后）
            - 'ff': 有限域二次相位公式
                * 仅支持奇数特征 (p>2)
                * 不支持特征2 (p=2)
        variant: 投影算符数量
            - 'compact': 返回 d^2 个投影（选择d组线性无关的基）
            - 'full': 返回 d(d+1) 个投影（全部d+1组基）

    Returns:
        MUBDesign: 包含投影算符、分组和测量矩阵的设计对象

    Raises:
        ValueError: 如果dimension不是素数幂，或method/variant参数无效
        NotImplementedError: 如果未安装galois库且维度不在_MinimalGFBackend支持范围内

    Note:
        - 强烈建议安装galois库以获得完整的维度支持: ``pip install galois``
        - 未安装galois库时，仅支持：所有素数维度，d=4, d=9, d=16
        - 安装galois库后，支持所有素数幂维度：2, 3, 4, 5, 7, 8, 9, 11, 13, 16, 25, 27, 32...

    Examples:
        >>> # 基本使用
        >>> design = build_mub_projectors(dimension=5)
        >>> print(len(design.projectors))  # 25 (compact模式)
        
        >>> # 使用完整MUB集合
        >>> design = build_mub_projectors(dimension=5, variant='full')
        >>> print(len(design.projectors))  # 30
        
        >>> # 使用有限域公式（仅奇数特征）
        >>> design = build_mub_projectors(dimension=9, method='ff')
    """
    d = dimension
    gf = _get_field_backend(d)

    if method not in {"wh", "ff"}:
        raise ValueError("method must be 'wh' or 'ff'")
    if variant not in {"compact", "full"}:
        raise ValueError("variant must be 'compact' or 'full'")

    if method == "ff" and gf.p == 2:
        raise ValueError("method='ff' is invalid for characteristic 2; use method='wh'")

    if method == "wh":
        # Odd characteristic: robust finite-field quadratic-phase construction
        if gf.p % 2 == 1:
            bases_full = _build_bases_ff(d, gf)
        else:
            # Characteristic 2 (d=2^k): use stabilizer/Pauli construction
            bases_full = _build_bases_pow2_stabilizer(d, gf)
    else:
        # Finite-field formula (only valid for p>2)
        bases_full = _build_bases_ff(d, gf)

    # 构建完整 d+1 组的投影与测量矩阵
    projectors_full: List[np.ndarray] = []
    groups_full: List[int] = []
    for g, basis in enumerate(bases_full):
        for i in range(d):
            v = basis[:, i]
            P = np.outer(v, v.conj())
            projectors_full.append(P)
            groups_full.append(g)

    proj_full = np.stack(projectors_full, axis=0)
    groups_full_arr = np.array(groups_full, dtype=int)
    meas_full = proj_full.reshape(proj_full.shape[0], -1)

    if variant == "full":
        projectors_arr = proj_full
        groups_arr = groups_full_arr
        meas = meas_full
    else:
        # 选择恰好 d^2 个线性无关的测量（行选择）
        m, n = meas_full.shape
        selected: List[int] = []
        if n != d * d:
            raise RuntimeError("internal error: measurement matrix width mismatch")
        M_sel = np.zeros((0, n), dtype=complex)
        for i in range(m):
            row = meas_full[i:i+1, :]
            if M_sel.shape[0] == 0:
                M_try = row
                rank_sel = 0
            else:
                M_try = np.vstack([M_sel, row])
                rank_sel = np.linalg.matrix_rank(M_sel)
            if np.linalg.matrix_rank(M_try) > rank_sel:
                selected.append(i)
                M_sel = M_try
                if len(selected) == n:
                    break
        if len(selected) != n:
            raise RuntimeError("failed to select d^2 independent MUB projectors")
        idx = np.array(selected, dtype=int)
        projectors_arr = proj_full[idx]
        # 紧凑模式：选子集后各组不再构成 POVM，改为单组归一化以匹配线性重构流程
        groups_arr = np.zeros(len(idx), dtype=int)
        meas = meas_full[idx]
    return MUBDesign(dimension=d, projectors=projectors_arr, groups=groups_arr, measurement_matrix=meas)
