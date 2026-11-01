# cftv-simulador-nvr

[English](README.en.md) · **Português (Brasil)**

[![Python 3](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](#) [![PyYAML](https://img.shields.io/badge/PyYAML-%C3%BAnica%20dep-3776AB?style=flat-square)](#) [![pytest](https://img.shields.io/badge/pytest-43%20testes-0A9EDC?style=flat-square&logo=pytest)](#) [![MIT License](https://img.shields.io/badge/License-MIT-f4c430?style=flat-square)](LICENSE)

## O que é

**Simulador de NVR para CFTV**: câmeras IP simuladas, negociação RTSP (handshake + autenticação), gravação e reprodução de frames com taxa de perda, verificação de saúde (banda) e índice NVR com busca por horário. É um laboratório educacional de sistemas de vigilância.

## Status

Laboratório educacional funcional e testado (43 testes).

## Funcionalidades

- **Câmera** (`camera.py`): `Camera`, `Frame` — modelo com id.
- **RTSP** (`rtsp.py`): `negociar` (handshake completo), `Sessao`, `handshake_completo`. Simula autenticação (`_autenticacao`).
- **NVR** (`nvr.py`): `gravar`, `buscar_por_horario`, `indice_por_camera`.
- **Gravação** (`gravacao.py`): `gravar_janela`, `reproduzir`, `taxa_de_perda`.
- **Saúde** (`saude.py`): `verificar(Saude)` — banda mbps.
- **CLI** (`cftvsim`): `executar`.

## Arquitetura

Pacote `cftvsim` com módulos separados por função (câmera, RTSP, NVR, gravação, saúde). CLI em `cli.py`.

## Stack

- Python ≥ 3.10, PyYAML ≥ 6.0
- pytest (dev)

## Estrutura do repositório

```
cftv-simulador-nvr/
├── src/cftvsim/     # camera · rtsp · nvr · gravacao · saude · cli
├── dados/
├── tests/           # 43 testes
└── LICENSE          # MIT
```

## Pré-requisitos e instalação

```bash
pip install -e .
```

## Como executar

```bash
cftvsim executar dados/
```

## Testes e qualidade

```bash
PYTHONPATH=src python -m pytest tests/   # 43 passed
```

## Decisões técnicas

- RTSP simulado (sem socket): testável sem câmera real.
- Perda de frames calculada diretamente (simples e didática).

## Limitações

- Simulação — não substitui NVR real nem câmeras físicas.

## Processo de desenvolvimento

Projeto individual de Kelvin Oliveira, construído com agentes de IA orquestrados e revisado pelo autor.

## Licença e autor

MIT — Copyright (c) 2026 Kelvin Rebelo de Oliveira. Autor: [Kelvin Oliveira](https://github.com/KelvinOliveiraCode) · [Portfólio](https://kelvinoliveiracode.github.io/portfolio/)
