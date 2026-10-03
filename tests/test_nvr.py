"""Testes do NVR, RTSP, saude e gravacao.

NVR, RTSP, health and recording tests.

O criterio de aceite passa por aqui: 24 cameras no fluxo, 3 falhas plantadas
detectadas cada uma com seu diagnostico, e nenhuma camera saudavel acusada.
Um health check que acusa tudo e tao inutil quanto um que nao acusa nada - e
foi exatamente o que aconteceu antes da correcao do relogio, que estes testes
travam.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from cftvsim import gravacao as modulo_gravacao
from cftvsim import nvr as modulo_nvr
from cftvsim import rtsp as modulo_rtsp
from cftvsim import saude as modulo_saude
from cftvsim.camera import Camera

RAIZ = Path(__file__).resolve().parent.parent
TOPOLOGIA = RAIZ / "dados" / "topologia-cftv.yaml"
BASE = 1_700_000_000


def _camera(cid: str, modo: str = "ok") -> Camera:
    return Camera(id=cid, ip="192.168.30.99", modo_falha=modo)


class TestNvr:
    """Gravacao e busca."""

    def test_grava_60(self) -> None:
        assert len(modulo_nvr.gravar(_camera("C"), BASE, 60).frames) == 60

    def test_grava_quem_caiu(self) -> None:
        assert len(modulo_nvr.gravar(_camera("C", "cai"), BASE, 60).frames) == 50

    def test_busca_por_horario(self) -> None:
        gravacao = modulo_nvr.gravar(_camera("C"), BASE, 60)
        achados = modulo_nvr.buscar_por_horario([gravacao], BASE + 10, BASE + 20)
        assert len(achados) == 11

    def test_busca_invertida_devolve_vazio(self) -> None:
        gravacao = modulo_nvr.gravar(_camera("C"), BASE, 60)
        assert modulo_nvr.buscar_por_horario([gravacao], BASE + 20, BASE + 10) == []

    def test_gravar_quantidade_negativa(self) -> None:
        with pytest.raises(ValueError):
            modulo_nvr.gravar(_camera("C"), BASE, -1)

    def test_relogio_errado_desloca_a_busca(self) -> None:
        # A CAM-19 grava com carimbo adiantado: buscar no horario "certo"
        # nao acha, e e isso que o teste prova. Gravacao que funciona e
        # busca que nao acha e o sintoma exato do relogio errado.
        gravacao = modulo_nvr.gravar(_camera("C", "relogio-errado"), BASE, 10)
        assert modulo_nvr.buscar_por_horario([gravacao], BASE + 1, BASE + 10) == []
        assert len(modulo_nvr.buscar_por_horario([gravacao], BASE + 301, BASE + 310)) == 10

    def test_indice_agrupa(self) -> None:
        gravacoes = [
            modulo_nvr.gravar(_camera("A"), BASE, 5),
            modulo_nvr.gravar(_camera("B"), BASE, 5),
        ]
        indice = modulo_nvr.indice_por_camera(gravacoes)
        assert set(indice) == {"A", "B"}


class TestRtsp:
    """O handshake em 4 fases."""

    def test_fluxo_completo(self) -> None:
        ok, fases = modulo_rtsp.handshake_completo(_camera("C"))
        assert ok is True
        assert fases == ["descoberta", "autenticacao", "codec", "gravacao"]

    def test_senha_errada_para_na_autenticacao(self) -> None:
        sessao = modulo_rtsp.negociar(_camera("C"), "admin", "errada")
        assert sessao.ok is False
        assert sessao.fase == "autenticacao"

    def test_camera_caida_para_na_descoberta(self) -> None:
        camera = _camera("C", "cai")
        for _ in range(60):
            camera.proximo_frame(BASE)
        sessao = modulo_rtsp.negociar(camera, "admin", "FICTICIA")
        assert sessao.ok is False
        assert sessao.fase == "descoberta"

    def test_codec_acordado(self) -> None:
        sessao = modulo_rtsp.negociar(_camera("C"), "admin", "FICTICIA")
        assert sessao.codec_acordado == "h264"


class TestSaude:
    """Cada falha com seu diagnostico, e so o seu."""

    def _verifica(self, cid: str, modo: str):
        camera = _camera(cid, modo)
        gravacao = modulo_nvr.gravar(camera, BASE, 60)
        return modulo_saude.verificar(camera, gravacao.frames, base_esperada=BASE)

    def test_queda(self) -> None:
        resultado = self._verifica("CAM-07", "cai")
        assert resultado.disponivel is False
        assert resultado.problemas == ["camera-indisponivel"]

    def test_perda(self) -> None:
        resultado = self._verifica("CAM-13", "perde-quadro")
        assert resultado.problemas == ["perda-de-quadro"]
        assert resultado.perda_quadro == 6

    def test_relogio(self) -> None:
        resultado = self._verifica("CAM-19", "relogio-errado")
        assert resultado.problemas == ["relogio-deslocado"]

    def test_saudavel_limpa(self) -> None:
        resultado = self._verifica("CAM-01", "ok")
        assert resultado.disponivel is True
        assert resultado.problemas == []

    def test_sem_base_nao_acusa_relogio(self) -> None:
        # Sem referencia, o relogio nao e verificado. Verificar contra o
        # relogio de parede acusaria toda camera, porque os carimbos sao
        # sinteticos - e foi exatamente o bug que esta assinatura corrige.
        camera = _camera("CAM-01", "ok")
        gravacao = modulo_nvr.gravar(camera, BASE, 5)
        assert modulo_saude.verificar(camera, gravacao.frames).problemas == []


class TestGravacao:
    """Janela, reproducao e taxa."""

    def test_janela(self) -> None:
        assert len(modulo_gravacao.gravar_janela(_camera("C"), BASE, 10)) == 10

    def test_janela_para_quando_cai(self) -> None:
        frames = modulo_gravacao.gravar_janela(_camera("C", "cai"), BASE, 100)
        assert len(frames) == 50

    def test_taxa_zero_quando_integra(self) -> None:
        frames = modulo_gravacao.gravar_janela(_camera("C"), BASE, 10)
        assert modulo_gravacao.taxa_de_perda(frames) == 0.0

    def test_taxa_com_perda(self) -> None:
        frames = modulo_gravacao.gravar_janela(_camera("C", "perde-quadro"), BASE, 20)
        assert modulo_gravacao.taxa_de_perda(frames) > 0.0

    def test_taxa_vazia(self) -> None:
        assert modulo_gravacao.taxa_de_perda([]) == 0.0

    def test_reproduzir_vazia(self) -> None:
        assert "vazia" in modulo_gravacao.reproduzir([])

    def test_reproduzir_com_camera_id(self) -> None:
        frames = modulo_gravacao.gravar_janela(_camera("C"), BASE, 3)
        texto = modulo_gravacao.reproduzir(frames, "C")
        assert texto.count(" ok") == 3
        assert "CORROMPIDO" not in texto

    def test_reproduzir_acusa_corrompido(self) -> None:
        frames = modulo_gravacao.gravar_janela(_camera("C"), BASE, 2)
        frames[0].soma = "0" * 16
        assert "CORROMPIDO" in modulo_gravacao.reproduzir(frames, "C")


class TestTopologia:
    """O arquivo real tem 24 cameras e as 3 falhas."""

    def test_vinte_e_quatro(self) -> None:
        documento = yaml.safe_load(TOPOLOGIA.read_text(encoding="utf-8"))
        assert len(documento["cameras"]) == 24

    def test_falhas_plantadas(self) -> None:
        documento = yaml.safe_load(TOPOLOGIA.read_text(encoding="utf-8"))
        falhas = {
            c["id"]: c["modo_falha"]
            for c in documento["cameras"]
            if c["modo_falha"] != "ok"
        }
        assert falhas == {
            "CAM-07": "cai",
            "CAM-13": "perde-quadro",
            "CAM-19": "relogio-errado",
        }