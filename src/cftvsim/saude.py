"""Health check de cameras com heartbeat.

Camera health check with heartbeat.

Mede disponibilidade (a camera responde?), perda de quadro por quebra de
sequencia, banda estimada e temperatura, e compara o carimbo dos frames com
o relogio local para acusar camera com relogio adiantado. As falhas
plantadas em `camera.py` (queda, perda de quadro, relogio errado) aparecem
como problemas nomeados no resultado.

Measures availability, frame loss from sequence breaks, estimated
bandwidth and temperature, and flags cameras whose frame timestamps drift
far from the local clock. Planted failures from `camera.py` surface as
named problems in the result.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from .camera import Camera, Frame

# Tolerancia entre o carimbo dos frames e o relogio local, em segundos.
TOLERANCIA_DESLOCAMENTO_S = 120
# Acima disso a temperatura vira problema, em graus Celsius.
LIMITE_TEMPERATURA_C = 70.0
# Payload medio assumido por frame para estimar a banda, em bytes.
TAMANHO_FRAME_BYTES = 12000


@dataclass
class Saude:
    """Resultado do health check de uma camera.

    Health check result for one camera.

    Attributes:
        camera_id: Id da camera avaliada.
        disponivel: Se a camera respondeu (heartbeat presente).
        latencia_ms: Latencia reportada pela camera.
        perda_quadro: Frames perdidos por quebra de sequencia.
        banda_mbps: Banda estimada da janela, em Mbps.
        temperatura_c: Temperatura reportada, em graus Celsius.
        poe_w: Consumo PoE reportado, em watts.
        problemas: Falhas nomeadas detectadas (vazio = saudavel).
    """

    camera_id: str
    disponivel: bool
    latencia_ms: int
    perda_quadro: int
    banda_mbps: float
    temperatura_c: float
    poe_w: float
    problemas: list[str] = field(default_factory=list)


def _banda_mbps(frames: list[Frame]) -> float:
    """Estima a banda da janela: bytes totais divididos pela duracao.

    Estimates window bandwidth: total bytes over the duration.

    Args:
        frames: Frames da janela, em ordem.

    Returns:
        A banda estimada em Mbps, ou 0.0 se nao ha frames.
    """
    if not frames:
        return 0.0
    duracao = frames[-1].carimbo - frames[0].carimbo + 1
    if duracao < 1:
        duracao = 1
    bytes_totais = TAMANHO_FRAME_BYTES * len(frames)
    return (bytes_totais * 8) / (duracao * 1_000_000)


def verificar(
    camera: Camera, frames: list[Frame], base_esperada: int | None = None
) -> Saude:
    """Mede a saude da camera a partir do heartbeat e dos frames.

    Measures camera health from the heartbeat and the frames.

    Args:
        camera: A camera simulada.
        frames: Frames recentes da janela observada, em ordem.
        base_esperada: O tempo de referencia que os carimbos deveriam usar.
            Sem ela, o relogio nao e verificado: comparar carimbo sintetico
            com o relogio de parede acusaria toda camera, porque o laboratorio
            gera frames de uma base arbitraria e nao do "agora".

    Returns:
        O resultado `Saude`; `problemas` lista as falhas nomeadas:
        `camera-indisponivel`, `perda-de-quadro`, `relogio-deslocado` e
        `temperatura-alta`.
    """
    problemas: list[str] = []

    disponivel = camera.viva() and bool(frames)
    if not disponivel:
        problemas.append("camera-indisponivel")

    perda = 0
    for anterior, atual in zip(frames, frames[1:]):
        salto = atual.sequencia - anterior.sequencia
        if salto > 1:
            perda += salto - 1
    if perda > 0:
        problemas.append("perda-de-quadro")

    if frames and base_esperada is not None:
        # carimbo = base + sequencia. O deslocamento e contra a base que o
        # NVR usou para pedir os frames, e nao contra o relogio de parede.
        base_do_frame = frames[0].carimbo - frames[0].sequencia
        if abs(base_do_frame - base_esperada) > TOLERANCIA_DESLOCAMENTO_S:
            problemas.append("relogio-deslocado")

    if camera.temperatura_c > LIMITE_TEMPERATURA_C:
        problemas.append("temperatura-alta")

    return Saude(
        camera_id=camera.id,
        disponivel=disponivel,
        latencia_ms=camera.latencia_ms,
        perda_quadro=perda,
        banda_mbps=_banda_mbps(frames),
        temperatura_c=camera.temperatura_c,
        poe_w=camera.poe_w,
        problemas=problemas,
    )
