"""Handshake RTSP simulado em 4 fases.

Simulated RTSP handshake in 4 phases.

O NVR "negocia" uma sessao com a camera em quatro fases, na ordem:
descoberta, autenticacao, codec e gravacao. A primeira fase que falha encerra
a negociacao; nao ha retentativa, porque em rede real a camera que mentiu numa
fase nao pode ser confiada na proxima. Regras de comportamento (credencial
errada falha na autenticacao, camera que caiu falha na descoberta, codec
acordado e o da camera) estao no contrato da tarefa, nao duplicadas aqui.
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass

from cftvsim.camera import Camera

# Fases do handshake, em ordem. A tupla serve de rota da negociacao e de
# referencia para reportar quais fases foram percorridas ate onde parou.
FASE_DESCOBERTA = "descoberta"
FASE_AUTENTICACAO = "autenticacao"
FASE_CODEC = "codec"
FASE_GRAVACAO = "gravacao"
FASES = (FASE_DESCOBERTA, FASE_AUTENTICACAO, FASE_CODEC, FASE_GRAVACAO)


@dataclass
class Sessao:
    """Estado de uma negociacao RTSP.

    State of one RTSP negotiation.

    Attributes:
        camera_id: Id da camera alvo.
        codec_acordado: Codec aceito; vazio ate a fase de codec passar.
        fase: Ultima fase executada: a que parou a negociacao ou a final.
        ok: Verdadeiro apenas se as quatro fases passaram.
    """

    camera_id: str
    codec_acordado: str = ""
    fase: str = ""
    ok: bool = False


def fases_percorridas(sessao: Sessao) -> list[str]:
    """Fases visitadas em ordem, ate a fase atual (inclusive).

    Phases visited in order, up to the current one (inclusive).

    Args:
        sessao: Sessao em qualquer estado.

    Returns:
        Lista de nomes de fase; vazia se nenhuma fase foi executada.
    """
    if sessao.fase not in FASES:
        return []
    return list(FASES[: FASES.index(sessao.fase) + 1])


def _autenticacao(camera: Camera, usuario: str, senha: str) -> bool:
    """Confere as credenciais apresentadas contra as da camera.

    Checks the presented credentials against the camera's.
    """
    return (
        secrets.compare_digest(usuario, camera.usuario)
        and secrets.compare_digest(senha, camera.senha)
    )


def _gravacao(camera: Camera, base_tempo: int) -> bool:
    """Pede um frame de gravacao e confere o checksum.

    Requests a recording frame and verifies its checksum.
    """
    frame = camera.proximo_frame(base_tempo)
    return frame is not None and frame.confere(camera.id)


def negociar(camera: Camera, usuario: str, senha: str) -> Sessao:
    """Executa o handshake RTSP em 4 fases, parando na primeira falha.

    Runs the RTSP handshake in 4 phases, stopping at the first failure.

    Ordem fixa: descoberta, autenticacao, codec, gravacao. Credencial errada
    falha na autenticacao; camera que caiu falha na descoberta; codec
    acordado e o que a camera oferece.

    Args:
        camera: Camera simulada.
        usuario: Usuario apresentado.
        senha: Senha apresentada.

    Returns:
        Sessao com a fase onde parou, o codec acordado (se chegou la) e
        `ok=True` apenas se as quatro fases passaram.
    """
    sessao = Sessao(camera_id=camera.id)

    # Fase 1 - descoberta: a camera tem que responder agora. Quem caiu nao
    # responde, e e exatamente isso que a fase existe para detectar.
    sessao.fase = FASE_DESCOBERTA
    if not camera.viva():
        return sessao

    # Fase 2 - autenticacao: credencial errada falha aqui, nunca antes.
    sessao.fase = FASE_AUTENTICACAO
    if not _autenticacao(camera, usuario, senha):
        return sessao

    # Fase 3 - codec: em simulacao a camera sempre oferece o codec dela,
    # entao o acordado e o proprio codec da camera.
    sessao.fase = FASE_CODEC
    sessao.codec_acordado = camera.codec

    # Fase 4 - gravacao: pede um frame e confere o checksum para fechar.
    sessao.fase = FASE_GRAVACAO
    if not _gravacao(camera, int(time.time())):
        return sessao

    sessao.ok = True
    return sessao


def handshake_completo(camera: Camera) -> tuple[bool, list[str]]:
    """Handshake completo com as credenciais da propria camera.

    Full handshake using the camera's own credentials.

    Args:
        camera: Camera simulada.

    Returns:
        Tupla (ok, fases): sucesso e a lista de fases percorridas em ordem,
        parando na primeira que falhar.
    """
    sessao = negociar(camera, camera.usuario, camera.senha)
    return sessao.ok, fases_percorridas(sessao)
