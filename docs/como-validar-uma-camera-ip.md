# Como validar uma câmera IP antes de instalar

Este guia descreve a sequência de testes de bancada, executada com uma câmera IP simulada em ambiente fechado, sem contato com a rede de produção. O objetivo é detectar defeitos de hardware, firmware e configuração que só aparecem durante operação prolongada, não num primeiro acesso.

O laboratório simula três falhas de comportamento, CAM-07, CAM-13 e CAM-19. Cada uma é acionada por um modo de falha distinto e só se revela no teste correspondente. Nenhuma aparece num log de inicialização ou no menu de configuração: manifestam-se como perda de resposta, sequência de quadros descontínua ou carimbo de data e hora deslocado. Por isso a ordem e o tempo de observação contam mais do que a quantidade de menus abertos.

Os equipamentos necessários são uma estação de trabalho no mesmo segmento de rede da câmera, um navegador ou cliente RTSP e um gravador. Nada de software proprietário é exigido, pois os protocolos testados — descoberta, autenticação, negociação de codec, fluxo de vídeo e carimbo de tempo — são padrões de indústria.

## 1) Descoberta e ping

**O que fazer.** Anote o IP da câmera e pingue-o até obter três respostas. Se ela anunciar serviços por descoberta, registre protocolo e porta.

**O que observar.** Respostas de eco constantes e ausência de perda de pacote. Instabilidade no ping indica interferência de enlace, porta PoE defeituosa ou placa de rede incompatível.

**Falha plantada que esta seção pega.** Nenhuma das três. O modo de falha que causa queda só interrompe o fluxo depois que quadros foram produzidos, e a descoberta ocorre antes da geração de quadros, então o ping passa mesmo na câmera que cai. Ela serve a outro fim: evitar confundir falha de transporte com falha de câmera nos testes seguintes.

## 2) Autenticação e troca de senha padrão

**O que fazer.** Acesse a interface com as credenciais de fábrica, confirme a existência de uma conta administrativa e troque a senha imediatamente, sem reiniciar o equipamento antes de validar a nova credencial.

**O que observar.** Login aceito com as credenciais de fábrica; rejeitado após a troca; sessão mantida com a senha nova. Falha se manifesta como conta bloqueada, loop de redirecionamento ou opção de alteração inacessível.

**Falha plantada que esta seção pega.** Nenhuma das três. As falhas atuam sobre o fluxo de vídeo e o carimbo, não sobre autenticação. Credenciais padrão nunca trocadas são o defeito mais comum em câmeras devolvidas, e este passo é obrigatório mesmo sem acionar CAM-07, CAM-13 ou CAM-19.

## 3) Negociação de codec e resolução

**O que fazer.** Abra o stream pelo método mais leve, geralmente RTSP ou HTTP com H.264, e anote resolução e taxa de quadros. Forçe o codec alternativo, H.265, e confirme a decodificação.

**O que observar.** Codec e resolução aplicados, sem queda do link, sem artefatos visíveis e sem latência anormal ao trocar de codec. Negociação mal resolvida com codec incompatível revela firmware defeituoso.

**Falha plantada que esta seção pega.** Nenhuma das três. A negociação é um pré-requisito; ela não aciona a queda, a perda de quadro ou o relógio errado. Um codec mal configurado, porém, falseia o teste de gravação, por isso precisa ser resolvido antes da etapa quatro.

## 4) Gravação contínua por dez minutos observando perda

**O que fazer.** Grave o fluxo continuamente por dez minutos em disco. Acompanhe contadores de quadro recebido, taxa de quadros e integridade: cada quadro possui um checksum que confere se o dado chegou intacto.

**O que observar.** Continuidade da sequência numérica de quadros, sem lacunas; presença permanente de quadros; e checksums válidos.

**Falhas plantadas que esta seção pega.** Aqui atuam duas falhas. CAM-07 cai depois de um número limitado de quadros e para de responder: a gravação perde fluxo sem aviso e a ausência de heartbeat acusa a falha. CAM-13 perde quadro, pulando um a cada dez e quebrando a sequência; a lacuna nos números revela a perda. Ambas só se revelam com observação continuada.

## 5) Busca por horário com relógio sincronizado via NTP

**O que fazer.** Configure a câmera em um servidor NTP e confirme a alteração de hora, verificando em dois instantes separados. Em seguida, busque eventos por intervalo de horário específico.

**O que observar.** O relógio avançar junto com o NTP e a busca por horário retornar os quadros exatamente no período solicitado.

**Falha plantada que esta seção pega.** CAM-19 com relógio errado. A gravação funciona — quadros chegam e se salvam — mas a câmera carimba cada quadro cinco minutos à frente; a busca por horário só retorna imagens deslocadas. Este é o único teste que detecta CAM-19 e prova que sincronismo de relógio é requisito de usabilidade, não apenas de log.

## Critério de aceite

A câmera só é aprovada para instalação se passar por todas as etapas: ping estável, autenticação com senha trocada, codec e resolução coerentes, dez minutos de gravação sem queda e sem lacunas, e busca por horário assertiva. Se CAM-07, CAM-13 ou CAM-19 aparecerem, a câmera não é condenada por defeito físico: ela sinaliza o modo de falha correspondente, e a resolução envolve troca de unidade ou reprovisionamento antes de voltar a campo.
