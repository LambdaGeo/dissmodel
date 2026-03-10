"""
dissmodel/geo/raster_backend.py
================================
Motor vetorizado de autômatos celulares sobre grades raster (NumPy 2D).

Responsabilidade
----------------
Prover operações espaciais genéricas (shift, dilate, focal_sum, snapshot)
sem qualquer conhecimento de domínio — sem classes de uso do solo, sem CRS,
sem I/O, sem constantes de projeto.

Os modelos de domínio (FloodRasterModel, MangueRasterModel, …) importam
RasterBackend e operam sobre arrays nomeados armazenados em self.arrays.

Exemplo mínimo
--------------
    from dissmodel.geo.raster.backend import RasterBackend, DIRS_MOORE

    b = RasterBackend(shape=(100, 100))
    b.set("estado", np.zeros((100, 100), dtype=np.int8))

    estado = b.get("estado").copy()          # equivale a celula.past[attr]
    vizinhos = b.neighbor_contact(estado == 1)
    for dr, dc in DIRS_MOORE:
        viz = RasterBackend.shift2d(estado, dr, dc)
        ...
    b.arrays["estado"] = estado_novo
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import binary_dilation


# Vizinhança de Moore (8 direções) — constante de framework, não de domínio.
# Os modelos importam daqui; projetos não precisam redefinir.
DIRS_MOORE: list[tuple[int, int]] = [
    (-1, -1), (-1, 0), (-1, 1),
    ( 0, -1),          ( 0, 1),
    ( 1, -1), ( 1, 0), ( 1, 1),
]

# Vizinhança de Von Neumann (4 direções) — disponível para modelos que a usem.
DIRS_VON_NEUMANN: list[tuple[int, int]] = [
    (-1, 0), (0, -1), (0, 1), (1, 0),
]


class RasterBackend:
    """
    Armazenamento e operações vetorizadas para grades raster 2D.

    Substitui forEachCell / forEachNeighbor do TerraME em código NumPy puro.
    O backend é compartilhado entre múltiplos modelos no mesmo Environment —
    cada modelo lê e escreve nos arrays nomeados a cada passo.

    Arrays
    ------
    Armazenados em self.arrays como np.ndarray de shape (rows, cols).
    Nenhum nome é reservado — os modelos de domínio definem os nomes
    ("uso", "alt", "solo", "estado", "temperatura", …).

    Parâmetros
    ----------
    shape : (rows, cols) da grade.
    """

    def __init__(self, shape: tuple[int, int]) -> None:
        self.shape  = shape              # (rows, cols)
        self.arrays: dict[str, np.ndarray] = {}

    # ── leitura / escrita ─────────────────────────────────────────────────────

    def set(self, name: str, array: np.ndarray) -> None:
        """Armazena cópia do array com o nome dado."""
        self.arrays[name] = np.asarray(array).copy()

    def get(self, name: str) -> np.ndarray:
        """Retorna referência direta ao array (use .copy() para .past)."""
        return self.arrays[name]

    def snapshot(self) -> dict[str, np.ndarray]:
        """
        Cópia profunda de todos os arrays — equivale ao mecanismo .past do TerraME.

        Uso típico:
            past = backend.snapshot()
            uso_past = past["uso"]   # estado no início do passo
        """
        return {k: v.copy() for k, v in self.arrays.items()}

    # ── operações espaciais ───────────────────────────────────────────────────

    @staticmethod
    def shift2d(arr: np.ndarray, dr: int, dc: int) -> np.ndarray:
        """
        Desloca o array por (dr, dc) linhas/colunas sem wrap-around.
        Bordas preenchidas com zero.

        Equivale a acessar o vizinho na direção (dr, dc) para cada célula
        simultaneamente — substitui forEachNeighbor com uma operação vetorial.

        Exemplo:
            shift2d(alt, -1, 0)  →  altitude do vizinho ao norte de cada célula
            shift2d(alt,  1, 1)  →  altitude do vizinho ao sudeste
        """
        rows, cols = arr.shape
        out = np.zeros_like(arr)
        rs  = slice(max(0, -dr), min(rows, rows - dr))
        rd  = slice(max(0,  dr), min(rows, rows + dr))
        cs_ = slice(max(0, -dc), min(cols, cols - dc))
        cd  = slice(max(0,  dc), min(cols, cols + dc))
        out[rd, cd] = arr[rs, cs_]
        return out

    @staticmethod
    def neighbor_contact(
        condition: np.ndarray,
        neighborhood: list[tuple[int, int]] | None = None,
    ) -> np.ndarray:
        """
        Retorna máscara booleana onde a célula tem pelo menos um vizinho
        satisfazendo condition.

        neighborhood=None usa DIRS_MOORE (3×3 incluindo a própria célula via
        binary_dilation). Para vizinhança Von Neumann, passe DIRS_VON_NEUMANN
        ou construa uma estrutura personalizada.

        Equivale a forEachNeighbor verificando pertencimento a um conjunto.
        """
        if neighborhood is None:
            return binary_dilation(condition.astype(bool), structure=np.ones((3, 3)))
        # vizinhança customizada via shift manual
        result = np.zeros_like(condition, dtype=bool)
        for dr, dc in neighborhood:
            result |= RasterBackend.shift2d(condition.astype(np.int8), dr, dc) > 0
        return result

    def focal_sum(self, name: str, neighborhood: list[tuple[int, int]] = DIRS_MOORE) -> np.ndarray:
        """
        Soma focal: para cada célula, soma os valores do array nos vizinhos.
        Não inclui a própria célula.

        Útil para contar vizinhos em determinado estado, calcular gradientes, etc.

        Exemplo:
            n_vizinhos_agua = backend.focal_sum_mask("uso", condicao_agua)
        """
        arr    = self.arrays[name]
        result = np.zeros_like(arr, dtype=float)
        for dr, dc in neighborhood:
            result += self.shift2d(arr, dr, dc)
        return result

    def focal_sum_mask(
        self,
        mask: np.ndarray,
        neighborhood: list[tuple[int, int]] = DIRS_MOORE,
    ) -> np.ndarray:
        """
        Conta vizinhos onde mask é True.
        Retorna array int com contagem por célula.
        """
        result = np.zeros(self.shape, dtype=int)
        m = mask.astype(np.int8)
        for dr, dc in neighborhood:
            result += self.shift2d(m, dr, dc)
        return result

    # ── utilitários ───────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        bands = ", ".join(
            f"{k}:{v.dtype}[{v.shape}]" for k, v in self.arrays.items()
        )
        return f"RasterBackend(shape={self.shape}, arrays=[{bands}])"
