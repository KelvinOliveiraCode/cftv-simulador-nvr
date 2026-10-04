<div align="center">

<p>
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/tests-43%20passing-brightgreen?style=flat-square" alt="Tests">
  <img src="https://img.shields.io/badge/coverage-95%25-green-brightgreen?style=flat-square" alt="Coverage">
  <img src="https://img.shields.io/badge/deps-PyYAML%20only-blue?style=flat-square" alt="Deps">
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/platform-Windows-blue?style=flat-square" alt="Windows">
</p>

# cftv-simulador-nvr

**Bancada de CFTV simulada: 24 cameras IP, um NVR em Python e 3 falhas plantadas com diagnostico proprio.**

</div>

---

## PT-BR

### O que e

Bancada de testes de CFTV em Python: 24 cameras IP simuladas e um NVR que
descobre, autentica, negocia codec, grava, reproduce e busca por horario, com
health check de disponibilidade, latencia, perda de quadro, banda, temperatura
e PoE. Tres cameras tem falha plantada e o health check detecta cada uma com o
seu diagnostico.

### Por que foi feito

E a bancada de testes do CFTV: validar o fluxo completo sem comprar nenhum
equipamento e sem tocar em camera de cliente. E o guia de bancada
(`docs/como-validar-uma-camera-ip.md`) diz como testar uma camera IP **antes**
de instalar, na ordem correta.

### Como rodar

```powershell
# 1. Instalar
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .

# 2. Validar
python -m pytest tests/ -v

# 3. Executar
python -m cftvsim executar dados/topologia-cftv.yaml --saida exemplos/relatorio-saude.md
```

Saida real (o comando termina com codigo 1 porque ha cameras com problema):

```
- CAM-07: COM PROBLEMA (camera-indisponivel)
- CAM-13: COM PROBLEMA (perda-de-quadro)
- CAM-19: COM PROBLEMA (relogio-deslocado)
...
Resumo: 21 saudaveis, 3 com problema
relatorio gravado em exemplos\relatorio-saude.md
```

Sem instalar nada, da raiz do repositorio:

```powershell
$env:PYTHONPATH="$PWD\src"; python -m cftvsim executar dados/topologia-cftv.yaml --saida exemplos/relatorio-saude.md
```

### As 3 falhas plantadas

| Camera | Falha | Como e detectada |
|---|---|---|
| CAM-07 | cai apos 50 frames | ausencia de heartbeat |
| CAM-13 | pula 1 frame a cada 10 | quebra na sequencia |
| CAM-19 | relogio 5 min adiantado | carimbo fora da tolerancia |

A CAM-19 e a mais instrutiva: a gravacao funciona, o checksum confere, e so a
busca por horario quebra, porque o indice diz que os quadros estao no futuro.
Relogio e infraestrutura, nao detalhe.

### O que aprendi

- **Comparar carimbo sintetico com relogio de parede acusa tudo.** O check
  original fazia isso e marcava as 24 cameras. A referencia tem de ser a base
  que o NVR usou para pedir os frames.
- **Perda se mede por buraco na sequencia**, e nao por checksum. Quadro que nao
  existe nao tem checksum para conferir.
- **Health check que acusa tudo e tao inutil quanto um que nao acusa nada.**
- **Bloco sem `exit` e normal.** O parser usa indentacao, nao palavra-chave.

### Limitacoes

- **Quadros sinteticos, nao imagem.** Perda, duplicata e dessincronia sim;
  qualidade de imagem, foco e infravermelho nao.
- **Sem rede real.** Latencia e numero no YAML, nao medicao: sem jitter e sem
  comportamento de switch sob carga.
- **Sem movimento de verdade.** Deteccao de movimento e variacao de contador,
  nao analise de cena.
- **Relogio simulado.** NTP real, deriva e fuso nao existem aqui.

### Licenca

MIT. Ver [LICENSE](LICENSE).

---

## EN

### What it is

A CFTV test bench in Python: 24 simulated IP cameras and an NVR that discovers,
authenticates, negotiates the codec, records, plays back and searches by time,
with health checks for availability, latency, frame loss, bandwidth, temperature
and PoE. Three cameras carry a planted failure and the health check gives each
one its own diagnosis.

### Why it was built

It is the CFTV test bench: validating the full flow without buying equipment and
without touching a customer camera. The bench guide
(`docs/como-validar-uma-camera-ip.md`) also explains how to test an IP camera
**before** installing it, in the right order.

### How to run

```powershell
# 1. Install
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .

# 2. Validate
python -m pytest tests/ -v

# 3. Run
python -m cftvsim executar dados/topologia-cftv.yaml --saida exemplos/relatorio-saude.md
```

Real output (the command exits with code 1 because some cameras have problems):

```
- CAM-07: COM PROBLEMA (camera-indisponivel)
- CAM-13: COM PROBLEMA (perda-de-quadro)
- CAM-19: COM PROBLEMA (relogio-deslocado)
...
Resumo: 21 saudaveis, 3 com problema
relatorio gravado em exemplos\relatorio-saude.md
```

Without installing anything, from the repository root:

```powershell
$env:PYTHONPATH="$PWD\src"; python -m cftvsim executar dados/topologia-cftv.yaml --saida exemplos/relatorio-saude.md
```

### The 3 planted failures

| Camera | Failure | How it is detected |
|---|---|---|
| CAM-07 | drops after 50 frames | missing heartbeat |
| CAM-13 | skips 1 frame every 10 | break in the sequence |
| CAM-19 | clock 5 min ahead | timestamp outside tolerance |

CAM-19 is the most instructive one: recording works, the checksum matches, and
only the time search breaks, because the index says the frames are in the
future. A clock is infrastructure, not a detail.

### What I learned

- **Comparing a synthetic timestamp against the wall clock flags everything.**
  The original check did that and marked all 24 cameras. The reference has to
  be the base the NVR used to request the frames.
- **Loss is measured by the hole in the sequence**, not by the checksum. A frame
  that does not exist has no checksum to verify.
- **A health check that flags everything is as useless as one that flags
  nothing.**
- **A block without `exit` is normal.** The parser uses indentation, not a
  keyword.

### Limitations

- **Synthetic frames, not images.** Loss, duplication and desync are simulated;
  image quality, focus and infrared are not.
- **No real network.** Latency is a number in the YAML, not a measurement: no
  jitter, no switch behaviour under load.
- **No real motion.** Motion detection is a counter variation, not scene
  analysis.
- **Simulated clock.** Real NTP, drift and time zone do not exist here.

### License

MIT. See [LICENSE](LICENSE).

---

<div align="center">
  <sub>Por <a href="https://github.com/KelvinOliveiraCode">Kelvin Oliveira</a> &middot;
  <a href="https://kelvinoliveiracode.github.io/portfolio/">portfolio</a></sub>
</div>
