<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/tests-43%20passing-brightgreen?style=flat-square" alt="Tests">
  <img src="https://img.shields.io/badge/coverage-94.88%25-green?style=flat-square" alt="Coverage">
  <img src="https://img.shields.io/badge/deps-PyYAML%20only-blue?style=flat-square" alt="Dependencies">
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="License">
</p>

# cftv-simulador-nvr

CFTV test bench in Python — 24 simulated IP cameras, an NVR that discovers, authenticates, negotiates codec, records, and searches by time, with a health check that detects 3 planted failures, each with its own diagnosis.

## Problem / Why it exists

Validate the full flow of a CFTV system — discovery, authentication, codec negotiation, recording, time search — without buying equipment and without touching a customer's camera. The bench closes the loop with 3 planted failures in the simulated cameras and proves whether the NVR detects them, each with a named diagnosis, before any field installation.

## What it does

- Loads the topology from `dados/topologia-cftv.yaml`: NVR-LAB-01 with 32 channels, 8 TB of disk, and 24 fictitious IP cameras (192.168.30.11 to 192.168.30.34).
- Runs a simulated 4-phase RTSP handshake per camera: discovery, authentication, codec, recording. The first failing phase ends the negotiation; there is no retry.
- Up to 60 frames per camera are recorded in memory, with a timestamp and a SHA-256 checksum truncated to 16 hexadecimal characters.
- Runs the health check of each camera: availability (heartbeat), frame loss from sequence break, estimated bandwidth, temperature, and clock drift.
- Generates a Markdown report with handshake, recording, and health of each camera, plus the summary.
- Exits with code 0 when all cameras are healthy, code 1 when at least one has a problem, and code 2 on topology error.

The topology plants 3 failures

| Camera | Failure | How it is detected |
| --- | --- | --- |
| CAM-07 | drops after 50 frames | absence of heartbeat |
| CAM-13 | skips 1 frame every 10 | gap in sequence |
| CAM-19 | clock 5 minutes ahead | timestamp outside the 120s tolerance against the NVR base |

In the CAM-19 case, recording works, the checksum matches, and only the time search breaks, because the index says the frames are 5 minutes in the future.

## Stack

- Python 3.10+
- Single runtime dependency: PyYAML >= 6.0 (YAML reading)
- Development: pytest >= 7.4, pytest-cov >= 4.1
- Packaging: setuptools, packages in `src/`

## How it works

The command `python -m cftvsim executar <topology>` runs these steps in order.

1. Reads the YAML topology and instantiates the 24 cameras with IP, user, fictitious password, codec (h264 or h265), failure mode, latency, temperature, and PoE consumption.
2. For each camera, runs the 4-phase RTSP handshake with the camera's own credentials.
3. Recording: requests up to 60 frames per camera. The downed camera (CAM-07) stops responding mid-way and the recording stays short (49 frames).
4. Health: checks heartbeat, counts loss from sequence jumps, estimates bandwidth (12,000 bytes per frame), checks temperature above 70 degrees Celsius, and checks clock offset against the time base the NVR used to request the frames — never against the wall clock, which would accuse all 24 cameras.
5. Prints the report and, if `--saida` is given, writes the file in Markdown.

Real output of the run (exit code 1 because there are cameras with problems).

```
- CAM-07: PROBLEM (camera-unavailable)
- CAM-13: PROBLEM (frame-loss)
- CAM-19: PROBLEM (clock-offset)
...
Summary: 21 healthy, 3 with problems
report written to exemplos\relatorio-saude.md
```

## How to run

Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

Validation

```powershell
python -m pytest tests/ -v
```

Execution

```powershell
python -m cftvsim executar dados/topologia-cftv.yaml --saida exemplos/relatorio-saude.md
```

Without installing anything, from the repository root

```powershell
$env:PYTHONPATH="$PWD\src"; python -m cftvsim executar dados/topologia-cftv.yaml --saida exemplos/relatorio-saude.md
```

## Project structure

```
cftv-simulador-nvr/
├── dados/
│   └── topologia-cftv.yaml   # fictitious topology: 24 cameras + NVR-LAB-01
├── docs/
│   ├── como-validar-uma-camera-ip.md
│   └── fluxo-de-video-ip.md
├── exemplos/
│   └── relatorio-saude.md    # real output of the command, do not edit by hand
├── src/
│   └── cftvsim/
│       ├── __init__.py       # package version
│       ├── __main__.py       # enables `python -m cftvsim`
│       ├── camera.py         # simulated IP camera: frame, checksum, 3 failure modes
│       ├── cli.py            # `executar` command and exit codes 0, 1, 2
│       ├── gravacao.py       # frame window, text playback, loss rate
│       ├── nvr.py            # recording, time search, per-camera index
│       ├── rtsp.py           # 4-phase handshake
│       └── saude.py          # health check: heartbeat, loss, bandwidth, clock, temperature
├── tests/
│   ├── test_camera.py
│   ├── test_cli.py
│   └── test_nvr.py
├── tools/
│   ├── gerar_topologia.py
│   ├── verificar_aceite.py
│   └── verificar_encoding.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

Tests give 43 passing and 94.88% coverage (the project requires 70%).

## Trade-offs and decisions

- Synthetic frames (counter with checksum) instead of real video: enough to simulate loss, duplicate, and clock desynchrony; does not simulate image quality, focus, or infrared.
- No real network: latency and loss are numbers declared in the YAML, not measured; there is no jitter nor switch behavior under load.
- Simulated clock with arbitrary base: the health check reference is the base the NVR used to request the frames, never the machine's wall clock.
- First handshake failure ends the negotiation without retry: in a real network, a camera that lied in one phase cannot be trusted in the next.
- Exit code 1 when there is a problem: a bench that approves everything without looking is not a bench.
- No closing keyword in blocks: the parser uses indentation.

## Known limitations

- Synthetic frames, not image: loss, duplicate, and desynchrony are simulated; image quality, focus, and infrared are not.
- No real network: latency and loss are declared in the YAML; no jitter, no link measurement, no switch under load.
- No real movement: motion detection is counter variation, not scene analysis.
- Simulated clock: real NTP, clock drift, and time zone do not exist here.

## License

MIT. See [LICENSE](LICENSE).

## Author

Kelvin Oliveira - https://github.com/KelvinOliveiraCode
