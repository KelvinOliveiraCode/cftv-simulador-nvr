"""Gravador NVR simulado: grava, indexa por camera e busca por horario.

Simulated NVR recorder: records, indexes by camera, searches by time.

Nada toca disco: a gravacao e uma lista de frames em memoria, com inicio e
fim extraidos dos carimbos. A busca por horario devolve frames de todas as
cameras dentro do intervalo - e e exatamente la que a CAM-19, com relogio
adiantado, aparece deslocada: os carimbos dela nao caem na janela esperada.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

try:
    from .camera import CAI, RELOGIO_ERRADO, Camera, Frame
except ImportError:
    # Executado como script solto, sem o pacote no caminho.
    from camera import CAI, RELOGIO_ERRADO, Camera, Frame  # type: ignore


@dataclass
class Gravacao:
    """Uma sessao de gravacao de uma camera.

    One recording session of a single camera.

    Attributes:
        camera_id: O id da camera gravada.
        frames: Os frames coletados, em ordem de chegada.
        inicio: Carimbo do primeiro frame (ou a base, se nao gravou nada).
        fim: Carimbo do ultimo frame (ou a base, se nao gravou nada).
    """

    camera_id: str
    frames: list[Frame] = field(default_factory=list)
    inicio: int = 0
    fim: int = 0


def gravar(camera: Camera, base_tempo: int, quantidade: int) -> Gravacao:
    """Tenta gravar `quantidade` frames, ignorando os que nao chegam.

    Try to record `quantidade` frames, dropping the ones that never arrive.

    Camera que cai (CAM-07) para de responder no meio: os frames ausentes
    simplesmente nao entram na lista, e a gravacao fica curta.

    Args:
        camera: A camera a gravar.
        base_tempo: O tempo de referencia, em segundos.
        quantidade: Quantos frames tentar coletar.

    Returns:
        A Gravacao resultante; `frames` pode ter menos que `quantidade`.
    """
    if quantidade < 0:
        raise ValueError(f"quantidade invalida: {quantidade}")
    frames: list[Frame] = []
    for _ in range(quantidade):
        frame = camera.proximo_frame(base_tempo)
        if frame is not None:
            frames.append(frame)
    inicio = frames[0].carimbo if frames else base_tempo
    fim = frames[-1].carimbo if frames else base_tempo
    return Gravacao(camera_id=camera.id, frames=frames, inicio=inicio, fim=fim)


def buscar_por_horario(
    gravacoes: Iterable[Gravacao], inicio: int, fim: int
) -> list[Frame]:
    """Devolve frames com carimbo dentro de [inicio, fim].

    Return frames whose timestamp falls inside [inicio, fim].

    Varre todas as gravacoes, une os resultados e ordena por carimbo.
    Se `fim` < `inicio` o intervalo e vazio e a resposta e lista vazia.
    Camera com relogio errado (CAM-19) so aparece se a janela cobrir os
    carimbos deslocados dela.

    Args:
        gravacoes: As gravacoes a consultar.
        inicio: Limite inferior do intervalo, inclusivo.
        fim: Limite superior do intervalo, inclusivo.

    Returns:
        Os frames encontrados, ordenados por carimbo (e sequencia).
    """
    if fim < inicio:
        return []
    achados: list[Frame] = []
    for gravacao in gravacoes:
        for frame in gravacao.frames:
            if inicio <= frame.carimbo <= fim:
                achados.append(frame)
    achados.sort(key=lambda f: (f.carimbo, f.sequencia))
    return achados


def indice_por_camera(
    gravacoes: Iterable[Gravacao],
) -> dict[str, list[Gravacao]]:
    """Agrupamento de gravacoes por camera.

    Group recordings by camera.

    Args:
        gravacoes: As gravacoes a indexar.

    Returns:
        Dicionario camera_id -> lista de gravacoes, preservando a ordem em
        que cada camera apareceu na entrada.
    """
    indice: dict[str, list[Gravacao]] = {}
    for gravacao in gravacoes:
        indice.setdefault(gravacao.camera_id, []).append(gravacao)
    return indice


def _gate_final() -> None:  # pragma: no cover - demonstracao manual
    """Gravacao real de 3 cameras; imprime as contagens.

    Real three-camera recording; prints the counts.
    """
    base = 1_750_000_000
    cameras = [
        Camera(id="CAM-01", ip="10.0.0.11"),
        Camera(id="CAM-07", ip="10.0.0.17", modo_falha=CAI),
        Camera(id="CAM-19", ip="10.0.0.39", modo_falha=RELOGIO_ERRADO),
    ]
    gravacoes = [gravar(c, base, 60) for c in cameras]
    print("contagem por camera:")
    for gravacao in gravacoes:
        print(
            f"  {gravacao.camera_id}: {len(gravacao.frames)} frames "
            f"(inicio={gravacao.inicio} fim={gravacao.fim})"
        )
    print("indice por camera:")
    for camera_id, lista in indice_por_camera(gravacoes).items():
        total = sum(len(g.frames) for g in lista)
        print(f"  {camera_id}: {len(lista)} gravacao(oes), {total} frames")
    janela_inicio, janela_fim = base + 1, base + 60
    print(f"busca por horario na janela [{janela_inicio}, {janela_fim}]:")
    for gravacao in gravacoes:
        achados = buscar_por_horario([gravacao], janela_inicio, janela_fim)
        print(f"  {gravacao.camera_id}: {len(achados)} frames")
    vazio = buscar_por_horario(gravacoes, 0, 0)
    print(f"busca em intervalo vazio: {len(vazio)} frames")


if __name__ == "__main__":
    _gate_final()
