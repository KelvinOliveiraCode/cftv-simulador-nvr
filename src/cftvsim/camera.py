"""Camera IP simulada.

Simulated IP camera.

Uma camera tem identidade, estado e um modo de falha opcional. Nada aqui toca
rede: o "stream" e uma sequencia de frames sinteticos gerados em memoria, e
cada frame e um contador com checksum - o suficiente para detectar perda,
duplicata e dessincronia de relogio sem gastar um byte com video de verdade.

## As 3 falhas plantadas

Elas estao documentadas aqui e nao escondidas, porque o criterio de aceite e
que o health check as detecte. Falha que ninguem sabe onde esta nao e
criterio, e loteria.

1. **CAM-07 cai**: apos N frames, para de responder. O health acusa por
   ausencia de heartbeat.
2. **CAM-13 perde quadro**: pula 1 frame a cada 10. O health acusa pela
   sequencia quebrada.
3. **CAM-19 com relogio errado**: carimba 5 minutos adiantado. A gravacao
   funciona, mas a busca por horario nao acha - e e isso que o teste prova.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

# Modos de falha conhecidos. Qualquer outro valor e erro de topologia, nao
# comportamento novo: falha silenciosa aqui viraria camera "saudavel" que nao
# e, e e exatamente o que o health check existe para pegar.
OK = "ok"
CAI = "cai"
PERDE_QUADRO = "perde-quadro"
RELOGIO_ERRADO = "relogio-errado"
MODOS_FALHA = (OK, CAI, PERDE_QUADRO, RELOGIO_ERRADO)

# Apos quantos frames a camera que cai para de responder.
LIMITE_QUEDA = 50
# A cada quantos frames a camera com perda pula um.
INTERVALO_PERDA = 10
# O adianto do relogio errado, em segundos.
ADIANTAMENTO = 300


class ErroDeCamera(Exception):
    """A camera nao pode ser criada ou operada.

    The camera cannot be created or operated.
    """


@dataclass
class Frame:
    """Um quadro sintetico.

    A synthetic frame.

    Attributes:
        sequencia: Numero sequencial a partir de 1.
        carimbo: O timestamp em segundos desde a epoca.
        soma: Checksum do conteudo, para detectar corrupcao.
    """

    sequencia: int
    carimbo: int
    soma: str

    def confere(self, camera_id: str) -> bool:
        """Se o checksum bate com o esperado.

        Whether the checksum matches the expected value.

        Args:
            camera_id: O id da camera que gerou o frame.

        Returns:
            Verdadeiro se o conteudo esta integro.
        """
        esperado = hashlib.sha256(
            f"{camera_id}:{self.sequencia}:{self.carimbo}".encode("ascii")
        ).hexdigest()[:16]
        return self.soma == esperado


@dataclass
class Camera:
    """Uma camera IP simulada.

    A simulated IP camera.

    Attributes:
        id: Identificador unico, como `CAM-01`.
        ip: Endereco ficticio.
        usuario: Usuario de acesso.
        senha: Senha ficticia (nunca real).
        codec: `h264` ou `h265`.
        modo_falha: Um de `MODOS_FALHA`.
        latencia_ms: Latencia simulada de resposta.
        temperatura_c: Temperatura simulada.
        poe_w: Consumo PoE simulado em watts.
    """

    id: str
    ip: str
    usuario: str = "admin"
    senha: str = "FICTICIA"
    codec: str = "h264"
    modo_falha: str = OK
    latencia_ms: int = 12
    temperatura_c: float = 41.5
    poe_w: float = 7.2
    _gerados: int = field(default=0, repr=False)

    def __post_init__(self) -> None:
        if self.modo_falha not in MODOS_FALHA:
            raise ErroDeCamera(
                f"camera {self.id}: modo de falha {self.modo_falha!r} desconhecido"
            )
        if self.codec not in ("h264", "h265"):
            raise ErroDeCamera(f"camera {self.id}: codec {self.codec!r} desconhecido")

    def viva(self) -> bool:
        """Se a camera responde agora.

        Whether the camera responds now.
        """
        if self.modo_falha == CAI:
            return self._gerados < LIMITE_QUEDA
        return True

    def proximo_frame(self, base_tempo: int) -> Frame | None:
        """Gera o proximo frame, ou nada se a camera caiu.

        Generate the next frame, or nothing if the camera dropped.

        Args:
            base_tempo: O tempo de referencia em segundos.

        Returns:
            O frame, ou `None` se a camera nao responde mais.
        """
        if not self.viva():
            return None
        self._gerados += 1
        sequencia = self._gerados
        if self.modo_falha == PERDE_QUADRO and sequencia % INTERVALO_PERDA == 0:
            self._gerados += 1
            sequencia = self._gerados
        carimbo = base_tempo + sequencia
        if self.modo_falha == RELOGIO_ERRADO:
            carimbo += ADIANTAMENTO
        soma = hashlib.sha256(
            f"{self.id}:{sequencia}:{carimbo}".encode("ascii")
        ).hexdigest()[:16]
        return Frame(sequencia=sequencia, carimbo=carimbo, soma=soma)

    def reiniciar_contador(self) -> None:
        """Zera o contador de frames gerados.

        Reset the generated frame counter.
        """
        self._gerados = 0