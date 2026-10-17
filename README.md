<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/testes-43%20passing-brightgreen?style=flat-square" alt="Testes">
  <img src="https://img.shields.io/badge/cobertura-94.88%25-green?style=flat-square" alt="Cobertura">
  <img src="https://img.shields.io/badge/deps-PyYAML%20apenas-blue?style=flat-square" alt="Dependencias">
  <img src="https://img.shields.io/badge/licenca-MIT-yellow?style=flat-square" alt="Licenca">
</p>

# cftv-simulador-nvr

Bancada de testes de CFTV em Python — 24 cameras IP simuladas, um NVR que descobre, autentica, negocia codec, grava e busca por horario, com health check que detecta 3 falhas plantadas, cada uma com seu proprio diagnostico.

## Problema / Por que existe

Validar o fluxo completo de um sistema de CFTV - descoberta, autenticacao, negociacao de codec, gravacao, busca por horario - sem comprar equipamento e sem mexer em camera de cliente. A bancada fecha o circuito com 3 falhas plantadas nas cameras simuladas e prova se o NVR as detecta, cada uma com diagnostico nomeado, antes de qualquer instalacao em campo.

## O que faz

- Carrega a topologia de `dados/topologia-cftv.yaml`: NVR-LAB-01 com 32 canais, 8 TB de disco e 24 cameras IP ficticias (192.168.30.11 a 192.168.30.34).
- Executa um handshake RTSP simulado em 4 fases por camera: descoberta, autenticacao, codec e gravacao. A primeira fase que falha encerra a negociacao; nao ha retentativa.
- Ate 60 frames por camera sao gravados em memoria, com carimbo e checksum sha256 truncado a 16 caracteres hexadecimais.
- Roda o health check de cada camera: disponibilidade (heartbeat), perda de quadro por quebra de sequencia, banda estimada, temperatura e relogio deslocado.
- Gera um relatorio Markdown com handshake, gravacao e saude de cada camera, mais o resumo.
- Sai com codigo 0 quando todas as cameras estao saudaveis, codigo 1 quando pelo menos uma tem problema e codigo 2 em erro de topologia.

A topologia planta 3 falhas

| Camera | Falha | Como e detectada |
| --- | --- | --- |
| CAM-07 | cai apos 50 frames | ausencia de heartbeat |
| CAM-13 | pula 1 frame a cada 10 | buraco na sequencia |
| CAM-19 | relogio 5 minutos adiantado | carimbo fora da tolerancia de 120s contra a base do NVR |

No caso CAM-19, a gravacao funciona, o checksum confere, e so a busca por horario quebra, porque o indice diz que os quadros estao 5 minutos no futuro.

## Stack

- Python 3.10+
- Unica dependencia de execucao: PyYAML >= 6.0 (leitura do YAML)
- Desenvolvimento: pytest >= 7.4, pytest-cov >= 4.1
- Empacotamento: setuptools, pacotes em `src/`

## Como funciona

O comando `python -m cftvsim executar <topologia>` executa estas etapas em ordem.

1. Le o YAML da topologia e instancia as 24 cameras com IP, usuario, senha ficticia, codec (h264 ou h265), modo de falha, latencia, temperatura e consumo PoE.
2. Para cada camera, roda o handshake RTSP em 4 fases com as credenciais proprias da camera.
3. Gravacao: pede ate 60 frames por camera. A camera que caiu (CAM-07) para de responder no meio e a gravacao fica curta (49 frames).
4. Saude: verifica heartbeat, conta perda por salto de sequencia, estima banda (12.000 bytes por frame), verifica temperatura acima de 70 graus Celsius e checa deslocamento de relogio contra a base de tempo que o NVR usou para pedir os frames - nunca contra o relogio de parede, que acusaria todas as 24 cameras.
5. Imprime o relatorio e, se `--saida` for informado, grava o arquivo em Markdown.

Saida real da execucao (codigo de saida 1 porque ha cameras com problema).

```
- CAM-07: COM PROBLEMA (camera-indisponivel)
- CAM-13: COM PROBLEMA (perda-de-quadro)
- CAM-19: COM PROBLEMA (relogio-deslocado)
...
Resumo: 21 saudaveis, 3 com problema
relatorio gravado em exemplos\relatorio-saude.md
```

## Como rodar

Instalacao

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

Validacao

```powershell
python -m pytest tests/ -v
```

Execucao

```powershell
python -m cftvsim executar dados/topologia-cftv.yaml --saida exemplos/relatorio-saude.md
```

Sem instalar nada, da raiz do repositorio

```powershell
$env:PYTHONPATH="$PWD\src"; python -m cftvsim executar dados/topologia-cftv.yaml --saida exemplos/relatorio-saude.md
```

## Estrutura do projeto

```
cftv-simulador-nvr/
├── dados/
│   └── topologia-cftv.yaml   # topologia ficticia: 24 cameras + NVR-LAB-01
├── docs/
│   ├── como-validar-uma-camera-ip.md
│   └── fluxo-de-video-ip.md
├── exemplos/
│   └── relatorio-saude.md    # saida real do comando, nao editar a mao
├── src/
│   └── cftvsim/
│       ├── __init__.py       # versao do pacote
│       ├── __main__.py       # permite `python -m cftvsim`
│       ├── camera.py         # camera IP simulada: frame, checksum, 3 modos de falha
│       ├── cli.py            # comando `executar` e codigos de saida 0, 1, 2
│       ├── gravacao.py       # janela de frames, reproducao em texto, taxa de perda
│       ├── nvr.py            # gravacao, busca por horario, indice por camera
│       ├── rtsp.py           # handshake em 4 fases
│       └── saude.py          # health check: heartbeat, perda, banda, relogio, temperatura
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

Os testes dao 43 passando e a cobertura e de 94.88% (o projeto exige 70%).

## Trade-offs e decisoes

- Quadros sinteticos (contador com checksum) em vez de video real: basta para simular perda, duplicata e dessincronia de relogio; nao simula qualidade de imagem, foco nem infravermelho.
- Sem rede real: latencia e perda sao numeros declarados no YAML, nao medida; nao ha jitter nem comportamento de switch sob carga.
- Relogio simulado com base arbitraria: a referencia do health check e a base que o NVR usou para pedir os frames, nunca o relogio de parede da maquina.
- Primeira falha do handshake para a negociacao sem retentativa: em rede real, camera que mentiu numa fase nao pode ser confiada na proxima.
- Codigo de saida 1 quando ha problema: bancada que aprova tudo sem olhar nao e bancada.
- Nao ha palavra-chave de encerramento nos blocos: o parser usa indentacao.

## Limitações conhecidas

- Quadros sinteticos, nao imagem: perda, duplicata e dessincronia simulam; qualidade de imagem, foco e infravermelho nao.
- Sem rede real: latencia e perda sao declaradas no YAML; sem jitter, sem medida de enlace, sem switch sob carga.
- Sem movimento de verdade: deteccao de movimento e variacao de contador, nao analise de cena.
- Relogio simulado: NTP real, deriva de relogio e fuso horario nao existem aqui.

## Licenca

MIT. Ver [LICENSE](LICENSE).

## Autor

Kelvin Oliveira - https://github.com/KelvinOliveiraCode
