# 四维空间中的完整 5 组相互无偏基（MUBs）

在四维空间（标准计算基 \((|0\rangle,|1\rangle,|2\rangle,|3\rangle)\)）中，一组**完整的 5 组 MUBs**定义如下：

- 每个态均已归一化；
- 不同基之间任意两态的重叠模平方均为 \(\frac{1}{4}\)；
- 该组 MUB 与 Pauli/stabilizer 方法得到的结果等价（仅差整体相位或基矢重标记）。

## 第 0 组基：计算基（computational basis）

\(\mathcal{B}_0 = \{|0\rangle,|1\rangle,|2\rangle,|3\rangle\}\)

其中各基矢的向量形式（按 \((|0\rangle,|1\rangle,|2\rangle,|3\rangle)\) 顺序的列向量）为：

\(|0\rangle = \begin{pmatrix} 1 \\ 0 \\ 0 \\ 0 \end{pmatrix}, \quad |1\rangle = \begin{pmatrix} 0 \\ 1 \\ 0 \\ 0 \end{pmatrix}, \quad |2\rangle = \begin{pmatrix} 0 \\ 0 \\ 1 \\ 0 \end{pmatrix}, \quad |3\rangle = \begin{pmatrix} 0 \\ 0 \\ 0 \\ 1 \end{pmatrix}\)

## 第 1 组基（\(\mathcal{B}_1\)）

用标准计算基的线性组合表示为：

\(\begin{aligned} |b^{(1)}_0\rangle &= \tfrac{1}{2}\big(|0\rangle - |1\rangle + |2\rangle - |3\rangle\big) \\ |b^{(1)}_1\rangle &= \tfrac{1}{2}\big(|0\rangle + |1\rangle - |2\rangle - |3\rangle\big) \\ |b^{(1)}_2\rangle &= \tfrac{1}{2}\big(|0\rangle - |1\rangle - |2\rangle + |3\rangle\big) \\ |b^{(1)}_3\rangle &= \tfrac{1}{2}\big(|0\rangle + |1\rangle + |2\rangle + |3\rangle\big) \end{aligned}\)

对应的向量形式：

\(\mathcal{B}_1 = \left\{ \frac{1}{2}\begin{pmatrix} 1 \\ -1 \\ 1 \\ -1 \end{pmatrix}, \ \frac{1}{2}\begin{pmatrix} 1 \\ 1 \\ -1 \\ -1 \end{pmatrix}, \ \frac{1}{2}\begin{pmatrix} 1 \\ -1 \\ -1 \\ 1 \end{pmatrix}, \ \frac{1}{2}\begin{pmatrix} 1 \\ 1 \\ 1 \\ 1 \end{pmatrix} \right\}\)

## 第 2 组基（\(\mathcal{B}_2\)）

含虚数相位（\(i^2=-1\)），线性组合表示为：

\(\begin{aligned} |b^{(2)}_0\rangle &= \tfrac{1}{2}\big(|0\rangle - i|1\rangle + i|2\rangle + |3\rangle\big) \\ |b^{(2)}_1\rangle &= \tfrac{1}{2}\big(|0\rangle + i|1\rangle - i|2\rangle + |3\rangle\big) \\ |b^{(2)}_2\rangle &= \tfrac{1}{2}\big(|0\rangle - i|1\rangle - i|2\rangle - |3\rangle\big) \\ |b^{(2)}_3\rangle &= \tfrac{1}{2}\big(|0\rangle + i|1\rangle + i|2\rangle - |3\rangle\big) \end{aligned}\)

对应的向量形式：

\(\mathcal{B}_2 = \left\{ \frac{1}{2}\begin{pmatrix} 1 \\ -i \\ i \\ 1 \end{pmatrix}, \ \frac{1}{2}\begin{pmatrix} 1 \\ i \\ -i \\ 1 \end{pmatrix}, \ \frac{1}{2}\begin{pmatrix} 1 \\ -i \\ -i \\ -1 \end{pmatrix}, \ \frac{1}{2}\begin{pmatrix} 1 \\ i \\ i \\ -1 \end{pmatrix} \right\}\)

## 第 3 组基（\(\mathcal{B}_3\)）

线性组合表示为：

\(\begin{aligned} |b^{(3)}_0\rangle &= \tfrac{1}{2}\big(|0\rangle - i|1\rangle - |2\rangle - i|3\rangle\big) \\ |b^{(3)}_1\rangle &= \tfrac{1}{2}\big(|0\rangle + i|1\rangle + |2\rangle - i|3\rangle\big) \\ |b^{(3)}_2\rangle &= \tfrac{1}{2}\big(|0\rangle - i|1\rangle + |2\rangle + i|3\rangle\big) \\ |b^{(3)}_3\rangle &= \tfrac{1}{2}\big(|0\rangle + i|1\rangle - |2\rangle + i|3\rangle\big) \end{aligned}\)

对应的向量形式：

\(\mathcal{B}_3 = \left\{ \frac{1}{2}\begin{pmatrix} 1 \\ -i \\ -1 \\ -i \end{pmatrix}, \ \frac{1}{2}\begin{pmatrix} 1 \\ i \\ 1 \\ -i \end{pmatrix}, \ \frac{1}{2}\begin{pmatrix} 1 \\ -i \\ 1 \\ i \end{pmatrix}, \ \frac{1}{2}\begin{pmatrix} 1 \\ i \\ -1 \\ i \end{pmatrix} \right\}\)

## 第 4 组基（\(\mathcal{B}_4\)）

线性组合表示为：

\(\begin{aligned} |b^{(4)}_0\rangle &= \tfrac{1}{2}\big(|0\rangle - |1\rangle - i|2\rangle - i|3\rangle\big) \\ |b^{(4)}_1\rangle &= \tfrac{1}{2}\big(|0\rangle - |1\rangle + i|2\rangle + i|3\rangle\big) \\ |b^{(4)}_2\rangle &= \tfrac{1}{2}\big(|0\rangle + |1\rangle - i|2\rangle + i|3\rangle\big) \\ |b^{(4)}_3\rangle &= \tfrac{1}{2}\big(|0\rangle + |1\rangle + i|2\rangle - i|3\rangle\big) \end{aligned}\)

对应的向量形式：

\(\mathcal{B}_4 = \left\{ \frac{1}{2}\begin{pmatrix} 1 \\ -1 \\ -i \\ -i \end{pmatrix}, \ \frac{1}{2}\begin{pmatrix} 1 \\ -1 \\ i \\ i \end{pmatrix}, \ \frac{1}{2}\begin{pmatrix} 1 \\ 1 \\ -i \\ i \end{pmatrix}, \ \frac{1}{2}\begin{pmatrix} 1 \\ 1 \\ i \\ -i \end{pmatrix} \right\}\)

## 小结 & 与代码的关系

1. 上述 5 组基（\(\mathcal{B}_0,\dots,\mathcal{B}_4\)）共包含 \(5 \times 4 = 20\) 个矢量，构成四维空间中**完备的 MUBs**；
2. 任意不同基组中的两态（即 \(|b^{(a)}_k\rangle\) 和 \(|b^{(b)}_\ell\rangle\)，其中 \(a \neq b\)）满足：\(\big|<b^{(a)}_k | b^{(b)}_\ell>\big|^2 = \frac{1}{4}\)
3. 与 Pauli/stabilizer 构造方法（`_build_bases_pow2_stabilizer`代码）的关系：
   - 两组 MUB 完全等价，差异仅可能体现为：
     - 每个态前的整体相位因子 \(e^{i\phi}\)；
     - 每组基矢内部的排列顺序；
   - 这种差异在物理上不影响 MUB 的核心性质，属于同一 MUB 设计。

若需验证，可将代码中 `dimension=4` 的输出结果按标准计算基 \((|0\rangle,|1\rangle,|2\rangle,|3\rangle)\) 展开，对比后可确认两者一致性（仅相位和排列不同）。
