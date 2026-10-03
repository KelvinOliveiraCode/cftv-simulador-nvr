# cftvsim

Bancada de testes de CFTV simulada: 24 câmeras IP e um NVR em Python, com
gravação, detecção de movimento, saúde do dispositivo e streaming RTSP
simulado.

A simulated CFTV test bench: 24 IP cameras and an NVR in Python, with
recording, motion detection, device health and simulated RTSP streaming.

> **Nada aqui é real.** Nenhum stream de câmera é capturado. Os "vídeos" são
> frames sintéticos gerados em memória — contadores com checksum, o suficiente
> para detectar perda, duplicata e dessincronia sem gastar um byte com vídeo
> de verdade.

## O que é

Descoberta, autenticação, negociação de codec, gravação, reprodução e busca
por horário, mais health check com disponibilidade, latência, perda de quadro,
banda, temperatura e PoE. Três câmeras têm falha plantada, e o health check as
detecta cada uma com seu diagnóstico.

## Por que foi feito

É a bancada de testes do CFTV: validar o fluxo completo sem comprar nenhum
equipamento. E o guia de bancada (`docs/como-validar-uma-camera-ip.md`) diz
como testar uma câmera IP **antes** de instalar, na ordem correta.

## Como rodar

```powershell
python -m cftvsim executar dados/topologia-cftv.yaml --saida exemplos/relatorio-saude.md
```

```
- CAM-07: COM PROBLEMA (camera-indisponivel)
- CAM-13: COM PROBLEMA (perda-de-quadro)
- CAM-19: COM PROBLEMA (relogio-deslocado)
...
Resumo: 21 saudaveis, 3 com problema
```

Instalação:

```powershell
pip install -e ".[dev]"
```

## As 3 falhas plantadas

| Câmera | Falha | Como é detectada |
|---|---|---|
| CAM-07 | cai após 50 frames | ausência de heartbeat |
| CAM-13 | pula 1 frame a cada 10 | quebra na sequência |
| CAM-19 | relógio 5 min adiantado | carimbo fora da tolerância |

A CAM-19 é a mais instrutiva: a gravação funciona, o checksum confere, e só a
busca por horário quebra — porque o índice diz que os quadros estão no futuro.
Relógio é infraestrutura, não detalhe.

## O que aprendi

- **Comparar carimbo sintético com relógio de parede acusa tudo.** O check
  original fazia isso e marcava as 24 câmeras. A referência tem de ser a base
  que o NVR usou para pedir os frames.
- **Perda se mede por buraco na sequência**, não por checksum. Quadro que não
  existe não tem checksum para conferir.
- **Health check que acusa tudo é tão inútil quanto um que não acusa nada.**
- **Bloco sem `exit` é normal.** O parser usa indentação, não palavra-chave.

## Testes

```powershell
python -m pytest -v
```

43 testes, 95% de cobertura. Cobrem a câmera e as 3 falhas, o NVR e a busca,
o handshake em 4 fases, a saúde com cada diagnóstico isolado, e a CLI.

```powershell
python tools/verificar_aceite.py     # 24 no fluxo + 3 detectadas + saida 1
python tools/verificar_encoding.py   # nenhum caractere corrompido
```

## Limitações

- **Quadros sintéticos, não imagem.** Perda, duplicata e dessincronia sim;
  qualidade de imagem, foco e infravermelho não.
- **Sem rede real.** Latência é número no YAML, não medição; sem jitter nem
  comportamento de switch sob carga.
- **Sem movimento de verdade.** Detecção de movimento é variação de contador,
  não análise de cena.
- **Relógio simulado.** NTP real, deriva e fuso não existem aqui.

## Licença

MIT.

---

## English

A simulated CFTV test bench: 24 IP cameras and an NVR, with recording, health
checks and simulated RTSP. Synthetic frames (counters with checksums) — enough
for loss, duplication and clock skew, no real video bytes.

Three planted failures (drop, frame loss, wrong clock), each distinctly
diagnosed. 21 healthy, 3 flagged, exit 1.

### Tests

43 tests, 95% coverage.

```powershell
python -m pytest -v
python tools/verificar_aceite.py
python tools/verificar_encoding.py
```

### Limitations

Synthetic frames; no real network, motion detection, or clock behavior.

### License

MIT.