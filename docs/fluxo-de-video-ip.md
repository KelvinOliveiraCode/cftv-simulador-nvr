# Fluxo de vídeo IP

Um quadro sai da câmera e chega na tela passando por seis etapas, e cada uma
pode ser o lugar onde a imagem morre. Este documento é o mapa dessas etapas,
na ordem em que o pacote as atravessa.

## 1. Captura

O sensor expõe e o codificador comprime. Aqui nasce tudo que o resto do fluxo
vai carregar: resolução, taxa de quadros e o codec. Erro aqui é permanente —
nenhuma etapa seguinte recupera detalhe que não foi capturado.

## 2. Empacotamento RTSP

O quadro vira pacotes RTP sob sessão RTSP. O handshake tem quatro fases
(descoberta, autenticação, codec, gravação) e para na primeira que falhar.
Credencial errada não é "imagem ruim": é sessão que nem abre.

## 3. Transporte

Os pacotes atravessam a rede. Perda aqui é buraco na sequência: o quadro 10
some e o 11 chega. O NVR não adivinha o que faltou — registra a falta. É por
isso que taxa de perda é métrica de rede, não de câmera.

## 4. Gravação

O NVR escreve com carimbo de chegada. Se o relógio da câmera está adiantado,
o carimbo mente: a gravação funciona, mas a busca por horário procura no
lugar errado. Relógio é infraestrutura, não detalhe.

## 5. Indexação

Cada quadro entra no índice por câmera e por horário. Sem índice, buscar é
varrer tudo; com índice errado, buscar é não achar. A CAM-19 deste
laboratório prova: os quadros existem, o índice diz que estão 5 minutos no
futuro, e quem busca no horário certo não acha nada.

## 6. Reprodução e busca

Ler do índice, montar a sequência, entregar. É aqui que perda vira travada
visível e relógio errado vira "não há gravação nesse horário".

## Onde este laboratório simplifica

Os "quadros" são contadores com checksum, não imagem. Isso basta para perda,
duplicata e dessincronia — que são os três defeitos que importam para
validação — e evita gastar um byte com vídeo de verdade. O que não é
simulado: latência real, jitter, nem comportamento de switch sob carga.
