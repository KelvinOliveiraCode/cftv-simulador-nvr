"""A linha de comando do cftvsim.

The cftvsim command line.

Um comando: `executar` roda o fluxo completo nas 24 cameras - descoberta,
handshake, gravacao, saude - e escreve o relatorio. O codigo de saida e 1
quando alguma camera tem problema, porque bancada que aprova tudo sem olhar
nao e bancada.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from . import gravacao as modulo_gravacao
from . import nvr as modulo_nvr
from . import rtsp as modulo_rtsp
from . import saude as modulo_saude
from .camera import Camera

SAIDA_OK = 0
SAIDA_PROBLEMA = 1
SAIDA_ERRO = 2

BASE_TEMPO = 1_700_000_000
QUADROS_POR_CAMERA = 60


def _constroi_parser() -> argparse.ArgumentParser:
    """Monta o parser de argumentos.

    Build the argument parser.

    Returns:
        O parser pronto.
    """
    parser = argparse.ArgumentParser(
        prog="cftvsim",
        description=(
            "Bancada de testes de CFTV simulada. / Simulated CFTV test bench."
        ),
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    p_exe = sub.add_parser("executar", help="roda o fluxo completo")
    p_exe.add_argument("topologia", help="o YAML da topologia")
    p_exe.add_argument("--saida", help="grava o relatorio neste arquivo")
    p_exe.add_argument("--quadros", type=int, default=QUADROS_POR_CAMERA)

    return parser


def _carrega_cameras(caminho: str | Path) -> tuple[str, list[Camera]]:
    """Le a topologia do disco.

    Read the topology from disk.

    Args:
        caminho: O YAML.

    Returns:
        O par `(nome_do_nvr, cameras)`.
    """
    documento = yaml.safe_load(Path(caminho).read_text(encoding="utf-8")) or {}
    nvr_nome = str((documento.get("nvr") or {}).get("nome", "NVR"))
    cameras = []
    for item in documento.get("cameras") or []:
        cameras.append(
            Camera(
                id=str(item.get("id", "")),
                ip=str(item.get("ip", "")),
                usuario=str(item.get("usuario", "admin")),
                senha=str(item.get("senha", "FICTICIA")),
                codec=str(item.get("codec", "h264")),
                modo_falha=str(item.get("modo_falha", "ok")),
                latencia_ms=int(item.get("latencia_ms", 12)),
                temperatura_c=float(item.get("temperatura_c", 41.5)),
                poe_w=float(item.get("poe_w", 7.2)),
            )
        )
    return nvr_nome, cameras


def _cmd_executar(args: argparse.Namespace, destino) -> int:
    """Executa `executar`.

    Run `executar`.

    Args:
        args: Os argumentos.
        destino: Onde imprimir.

    Returns:
        O codigo de saida.
    """
    try:
        nvr_nome, cameras = _carrega_cameras(args.topologia)
    except Exception as erro:
        print(f"erro de topologia: {erro}", file=sys.stderr)
        return SAIDA_ERRO

    linhas: list[str] = [
        "# Relatorio de saude do CFTV",
        "",
        "Saida real do comando, copiada sem edicao. Gerado por",
        "`python -m cftvsim executar`; nao editar a mao.",
        "",
        f"NVR: {nvr_nome}   cameras: {len(cameras)}",
        "",
        "## Handshake",
        "",
    ]
    with_problema = 0
    gravacoes = []
    for camera in cameras:
        ok, fases = modulo_rtsp.handshake_completo(camera)
        marca = "ok" if ok else "FALHOU"
        linhas.append(f"- {camera.id} ({camera.ip}): {marca} [{', '.join(fases)}]")
        gravacao = modulo_nvr.gravar(camera, BASE_TEMPO, args.quadros)
        gravacoes.append(gravacao)

    linhas.extend(["", "## Gravacao", ""])
    for gravacao in gravacoes:
        linhas.append(
            f"- {gravacao.camera_id}: {len(gravacao.frames)} frames"
        )

    linhas.extend(["", "## Saude", ""])
    for camera, gravacao in zip(cameras, gravacoes):
        resultado = modulo_saude.verificar(
            camera, gravacao.frames, base_esperada=BASE_TEMPO
        )
        estado = (
            "OK" if resultado.disponivel and not resultado.problemas
            else "COM PROBLEMA"
        )
        if estado != "OK":
            with_problema += 1
        detalhe = (
            ", ".join(resultado.problemas) if resultado.problemas
            else f"latencia {resultado.latencia_ms}ms, perda {resultado.perda_quadro}"
        )
        linhas.append(f"- {camera.id}: {estado} ({detalhe})")

    linhas.extend([
        "",
        f"Resumo: {len(cameras) - with_problema} saudaveis, "
        f"{with_problema} com problema",
    ])
    texto = "\n".join(linhas)
    print(texto, file=destino)

    if args.saida:
        caminho = Path(args.saida)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(texto + "\n", encoding="utf-8", newline="\n")
        print(f"relatorio gravado em {caminho}", file=destino)

    return SAIDA_PROBLEMA if with_problema else SAIDA_OK


def main(argv: list[str] | None = None) -> int:
    """O ponto de entrada.

    The entry point.

    Args:
        argv: Os argumentos, sem `argv[0]`.

    Returns:
        O codigo de saida.
    """
    parser = _constroi_parser()
    args = parser.parse_args(argv)
    if args.comando == "executar":
        return _cmd_executar(args, sys.stdout)
    parser.error(f"comando desconhecido: {args.comando}")
    return SAIDA_ERRO


if __name__ == "__main__":
    main()