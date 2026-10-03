"""Gera a topologia com 24 cameras de forma deterministica.

Generate the 24-camera topology deterministically.

Vinte e uma cameras saudaveis e tres com falha plantada, documentadas no
modulo `camera.py` e aqui: CAM-07 cai, CAM-13 perde quadro, CAM-19 tem o
relogio adiantado. A posicao delas na lista e fixa para que o relatorio de
saude seja comparavel entre execucoes.
"""

from __future__ import annotations

import random
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "dados" / "topologia-cftv.yaml"

SEMENTE = 20261003

# As 3 falhas plantadas: (id, modo). Documentadas em camera.py.
FALHAS = {
    "CAM-07": "cai",
    "CAM-13": "perde-quadro",
    "CAM-19": "relogio-errado",
}

LOCAIS = [
    "entrada-principal", "estacionamento", "recepcao", "corredor-norte",
    "corredor-sul", "deposito", "doca", "perimetro-leste",
]


def principal() -> int:
    """Gera a topologia.

    Generate the topology.

    Returns:
        Sempre 0.
    """
    rng = random.Random(SEMENTE)
    linhas = [
        "# Topologia CFTV ficticia: 24 cameras IP e um NVR.",
        "#",
        "# CONTEUDO FICTICIO. Enderecos, usuarios e senhas sao inventados.",
        "# As 3 falhas plantadas: CAM-07 cai, CAM-13 perde quadro,",
        "# CAM-19 tem o relogio adiantado em 5 minutos.",
        "",
        "nvr:",
        "  nome: NVR-LAB-01",
        "  canais: 32",
        "  disco_tb: 8",
        "",
        "cameras:",
    ]
    for indice in range(1, 25):
        cid = f"CAM-{indice:02d}"
        modo = FALHAS.get(cid, "ok")
        linhas.extend([
            f"  - id: {cid}",
            f"    ip: 192.168.30.{10 + indice}",
            "    usuario: admin",
            "    senha: FICTICIA",
            f"    codec: {'h265' if indice % 3 == 0 else 'h264'}",
            f"    modo_falha: {modo}",
            f"    local: {LOCAIS[(indice - 1) % len(LOCAIS)]}",
            f"    latencia_ms: {8 + rng.randrange(10)}",
            f"    temperatura_c: {38.0 + rng.random() * 8:.1f}",
            f"    poe_w: {6.0 + rng.random() * 3:.1f}",
        ])
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text("\n".join(linhas) + "\n", encoding="utf-8", newline="\n")
    print(f"topologia gravada em {DESTINO.relative_to(RAIZ)}: 24 cameras")
    print("falhas plantadas: CAM-07 cai, CAM-13 perde quadro, CAM-19 relogio errado")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())