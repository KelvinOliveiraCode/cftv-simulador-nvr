"""Prova de aceite do cftvsim.

cftvsim acceptance proof.

O criterio de aceite tem tres partes:

1. **As 24 cameras passam pelo fluxo completo** - descoberta, handshake,
   gravacao, saude - sem excecao.
2. **As 3 com falha plantada sao detectadas**, cada uma com seu diagnostico:
   CAM-07 indisponivel, CAM-13 com perda, CAM-19 com relogio deslocado.
3. **O relatorio sai correto**: 21 saudaveis, 3 com problema, e o codigo de
   saida e 1 porque ha problema.
"""

from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from cftvsim.cli import main as cli_main  # noqa: E402

TOPOLOGIA = RAIZ / "dados" / "topologia-cftv.yaml"

ESPERADAS = {
    "CAM-07": "camera-indisponivel",
    "CAM-13": "perda-de-quadro",
    "CAM-19": "relogio-deslocado",
}


class Falha(Exception):
    """Uma condicao de aceite nao foi satisfeita."""


def checar(condicao: bool, mensagem: str) -> None:
    """Falha se a condicao e falsa.

    Args:
        condicao: A condicao.
        mensagem: O que deu errado.

    Raises:
        Falha: Se a condicao for falsa.
    """
    if not condicao:
        raise Falha(mensagem)


def principal() -> int:
    """Roda a prova de aceite.

    Returns:
        0 se tudo passar, 1 se alguma condicao falhar.
    """
    try:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            codigo = cli_main(["executar", str(TOPOLOGIA)])
        saida = buffer.getvalue()

        for cid in [f"CAM-{i:02d}" for i in range(1, 25)]:
            checar(cid in saida, f"{cid} nao passou pelo fluxo")
        print("1) as 24 cameras passaram pelo fluxo completo")

        for cid, diagnostico in sorted(ESPERADAS.items()):
            checar(cid in saida, f"{cid} nao aparece no relatorio")
            checar(
                diagnostico in saida,
                f"{cid} sem o diagnostico {diagnostico}",
            )
        print("2) as 3 falhas plantadas detectadas com diagnostico certo")

        checar("21 saudaveis, 3 com problema" in saida, "resumo incorreto")
        checar(codigo == 1, f"codigo de saida {codigo}, esperado 1")
        print("3) relatorio correto e saida 1 havendo problema")
    except Falha as erro:
        print("\nACEITE FALHOU:")
        print(f"  - {erro}")
        return 1

    print("\nok: 24 no fluxo, 3 detectadas, relatorio correto")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())