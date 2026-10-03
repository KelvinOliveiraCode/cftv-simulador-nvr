"""Testes da CLI.

CLI tests.

A CLI roda o fluxo nas 24 cameras e devolve 1 quando ha problema. O teste que
importa e o de saida: bancada que aprova tudo sem olhar nao e bancada, e o
codigo de saida e o que um job automatizado leria.
"""

from __future__ import annotations

import contextlib
import io
from pathlib import Path

import pytest

from cftvsim.cli import main as cli_main

RAIZ = Path(__file__).resolve().parent.parent
TOPOLOGIA = RAIZ / "dados" / "topologia-cftv.yaml"


def _roda(argv):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        codigo = cli_main(argv)
    return codigo, buffer.getvalue()


class TestExecutar:
    """O fluxo completo."""

    def test_detecta_as_tres_falhas(self) -> None:
        codigo, saida = _roda(["executar", str(TOPOLOGIA)])
        assert codigo == 1
        assert "CAM-07" in saida and "CAM-13" in saida and "CAM-19" in saida

    def test_resumo_21_a_3(self) -> None:
        _, saida = _roda(["executar", str(TOPOLOGIA)])
        assert "21 saudaveis, 3 com problema" in saida

    def test_grava_relatorio(self, tmp_path: Path) -> None:
        destino = tmp_path / "rel.md"
        codigo, _ = _roda(["executar", str(TOPOLOGIA), "--saida", str(destino)])
        assert codigo == 1
        assert "CAM-07" in destino.read_text(encoding="utf-8")

    def test_topologia_inexistente(self, tmp_path: Path) -> None:
        codigo = cli_main(["executar", str(tmp_path / "nao-existe.yaml")])
        assert codigo == 2

    def test_help_sai_com_zero(self) -> None:
        with pytest.raises(SystemExit) as erro:
            cli_main(["--help"])
        assert erro.value.code == 0

    def test_sem_comando_falha(self) -> None:
        with pytest.raises(SystemExit):
            cli_main([])