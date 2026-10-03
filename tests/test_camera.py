"""Testes da camera.

Camera tests.

A camera e o contrato: NVR, RTSP, saude e gravacao consomem o que ela produz.
Tres comportamentos precisam estar travados porque o resto do projeto depende
deles sem verificar de novo: cair apos 50, pular 1 a cada 10, e carimbar 300s
adiantado.
"""

from __future__ import annotations

import pytest

from cftvsim.camera import (
    ADIANTAMENTO,
    CAI,
    INTERVALO_PERDA,
    LIMITE_QUEDA,
    OK,
    PERDE_QUADRO,
    RELOGIO_ERRADO,
    Camera,
    ErroDeCamera,
)


class TestCriacao:
    """O construtor recusa o que nao conhece."""

    def test_modo_invalido(self) -> None:
        with pytest.raises(ErroDeCamera):
            Camera(id="X", ip="y", modo_falha="explode")

    def test_codec_invalido(self) -> None:
        with pytest.raises(ErroDeCamera):
            Camera(id="X", ip="y", codec="mpeg1")


class TestSaudavel:
    """Camera sem falha gera sequencia perfeita."""

    def test_60_frames_sem_falha(self) -> None:
        camera = Camera(id="CAM-01", ip="x")
        frames = [camera.proximo_frame(1000) for _ in range(60)]
        assert all(f is not None for f in frames)
        assert [f.sequencia for f in frames] == list(range(1, 61))

    def test_checksum_confere(self) -> None:
        camera = Camera(id="CAM-01", ip="x")
        frame = camera.proximo_frame(1000)
        assert frame.confere("CAM-01") is True
        assert frame.confere("OUTRA") is False


class TestQueda:
    """CAM-07: 50 frames e silencio."""

    def test_para_aos_50(self) -> None:
        camera = Camera(id="CAM-07", ip="x", modo_falha=CAI)
        frames = [camera.proximo_frame(1000) for _ in range(60)]
        assert sum(1 for f in frames if f is not None) == LIMITE_QUEDA
        assert frames[-1] is None

    def test_viva_antes_e_morta_depois(self) -> None:
        camera = Camera(id="CAM-07", ip="x", modo_falha=CAI)
        assert camera.viva() is True
        for _ in range(LIMITE_QUEDA):
            camera.proximo_frame(1000)
        assert camera.viva() is False


class TestPerda:
    """CAM-13: 1 a cada 10 some."""

    def test_sequencia_tem_buraco(self) -> None:
        camera = Camera(id="CAM-13", ip="x", modo_falha=PERDE_QUADRO)
        sequencias = [
            f.sequencia for _ in range(30)
            if (f := camera.proximo_frame(1000)) is not None
        ]
        assert 10 not in sequencias
        assert 11 in sequencias

    def test_intervalo_documentado(self) -> None:
        assert INTERVALO_PERDA == 10


class TestRelogio:
    """CAM-19: 5 minutos adiantado."""

    def test_adiantamento(self) -> None:
        camera = Camera(id="CAM-19", ip="x", modo_falha=RELOGIO_ERRADO)
        frame = camera.proximo_frame(1000)
        assert frame.carimbo - (1000 + frame.sequencia) == ADIANTAMENTO
        assert ADIANTAMENTO == 300

    def test_checksum_continua_valido(self) -> None:
        # O relogio errado nao corrompe: o checksum usa o proprio carimbo.
        # E por isso que a gravacao funciona e so a busca quebra.
        camera = Camera(id="CAM-19", ip="x", modo_falha=RELOGIO_ERRADO)
        assert camera.proximo_frame(1000).confere("CAM-19") is True


class TestReinicio:
    """O contador zera sob pedido."""

    def test_reiniciar(self) -> None:
        camera = Camera(id="CAM-07", ip="x", modo_falha=CAI)
        for _ in range(LIMITE_QUEDA):
            camera.proximo_frame(1000)
        assert camera.viva() is False
        camera.reiniciar_contador()
        assert camera.viva() is True