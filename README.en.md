# cftv-simulador-nvr

**English** · [Português (Brasil)](README.md)

[![Python 3](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](#) [![PyYAML](https://img.shields.io/badge/PyYAML-only%20dep-3776AB?style=flat-square)](#) [![pytest](https://img.shields.io/badge/pytest-43%20tests-0A9EDC?style=flat-square&logo=pytest)](#) [![MIT License](https://img.shields.io/badge/License-MIT-f4c430?style=flat-square)](LICENSE)

## What it is

**A CCTV NVR simulator**: simulated IP cameras, RTSP negotiation (handshake + authentication), frame recording and playback with a loss rate, health checks (bandwidth) and an NVR index with time-range search. It is an educational surveillance-systems lab.

## Status

An educational lab, working and tested (43 tests).

## Features

- **Camera** (`camera.py`): `Camera`, `Frame` — model with id.
- **RTSP** (`rtsp.py`): `negociar` (full handshake), `Sessao`, `handshake_completo`. Simulated authentication (`_autenticacao`).
- **NVR** (`nvr.py`): `gravar`, `buscar_por_horario`, `indice_por_camera`.
- **Recording** (`gravacao.py`): `gravar_janela`, `reproduzir`, `taxa_de_perda`.
- **Health** (`saude.py`): `verificar(Saude)` — mbps bandwidth.
- **CLI** (`cftvsim`): `executar`.

## Architecture

A `cftvsim` package with separate modules per function (camera, RTSP, NVR, recording, health). CLI in `cli.py`.

## Stack

- Python ≥ 3.10, PyYAML ≥ 6.0
- pytest (dev)

## Repository layout

```
cftv-simulador-nvr/
├── src/cftvsim/     # camera · rtsp · nvr · gravacao · saude · cli
├── dados/
├── tests/           # 43 tests
└── LICENSE          # MIT
```

## Prerequisites and installation

```bash
pip install -e .
```

## How to run

```bash
cftvsim executar dados/
```

## Tests and quality

```bash
PYTHONPATH=src python -m pytest tests/   # 43 passed
```

## Technical decisions

- Simulated RTSP (no sockets): testable without a real camera.
- Frame-loss rate calculated directly (simple and didactic).

## Known limitations

- Simulation — it does not replace a real NVR or physical cameras.

## Development process

An individual project by Kelvin Oliveira, built with orchestrated AI agents and reviewed by the author.

## License and author

MIT — Copyright (c) 2026 Kelvin Rebelo de Oliveira. Author: [Kelvin Oliveira](https://github.com/KelvinOliveiraCode) · [Portfolio](https://kelvinoliveiracode.github.io/portfolio/)
