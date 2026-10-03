"""Gravacao e reproducao de janelas de frames.

Recording and playback of frame windows.

Grava uma janela de frames de uma camera simulada, reproduz ela em texto
com um resumo por frame e mede a fracao de sequencias faltando, como um
NVR sintetico faria.

Records a window of frames from a simulated camera, plays it back as text
with a per-frame summary, and measures the fraction of missing sequences,
like a synthetic NVR would.
"""

from __future__ import annotations

from .camera import Camera, Frame


def gravar_janela(camera: Camera, base: int, quantidade: int) -> list[Frame]:
    """Grava ate `quantidade` frames da camera.

    Records up to `quantidade` frames from the camera.

    Args:
        camera: A camera simulada.
        base: Tempo de referencia em segundos (origem dos carimbos).
        quantidade: Quantos frames tentar gravar.

    Returns:
        Os frames gravados, em ordem; a gravacao para cedo se a camera
        cair no meio (heartbeat ausente).
    """
    frames: list[Frame] = []
    for _ in range(quantidade):
        frame = camera.proximo_frame(base)
        if frame is None:
            break
        frames.append(frame)
    return frames


def reproduzir(frames: list[Frame], camera_id: str | None = None) -> str:
    """Reproduz os frames em texto, com um resumo por frame.

    Plays back the frames as text, with one summary line per frame.

    Args:
        frames: Frames a reproduzir, em ordem.
        camera_id: Se informado, confere o checksum de cada frame.

    Returns:
        O texto da reproducao: um cabecalho, uma linha por frame e um
        rodape.
    """
    if not frames:
        return "Gravacao vazia: nenhum frame para reproduzir."
    linhas = [
        f"Reproducao: {len(frames)} frames, "
        f"sequencia {frames[0].sequencia} a {frames[-1].sequencia}."
    ]
    for frame in frames:
        estado = ""
        if camera_id is not None:
            estado = " ok" if frame.confere(camera_id) else " CORROMPIDO"
        linhas.append(f"  seq={frame.sequencia:04d} carimbo={frame.carimbo}{estado}")
    linhas.append("Fim da reproducao.")
    return "\n".join(linhas)


def taxa_de_perda(frames: list[Frame]) -> float:
    """Fracao de sequencias faltando na janela.

    Fraction of missing sequences in the window.

    Args:
        frames: Frames gravados, em ordem.

    Returns:
        De 0.0 (sem perda) a 1.0 (tudo faltando); 0.0 se ha menos de
        dois frames para comparar.
    """
    if len(frames) < 2:
        return 0.0
    total = frames[-1].sequencia - frames[0].sequencia + 1
    faltantes = total - len(frames)
    if faltantes <= 0:
        return 0.0
    return faltantes / total
