"""Barramento de eventos em memória.

No diagrama de microsserviços esse papel é do message broker (RabbitMQ/Kafka). No monólito modular os eventos
são entregues na hora, dentro do mesmo processo. Para separar um módulo em microsserviço, basta trocar esta
classe por uma que publique no broker; os módulos continuam iguais.
"""
from collections import defaultdict


class BarramentoEventos:
    def __init__(self):
        self.assinantes = defaultdict(list)

    def assinar(self, tipo_evento, tratador):
        self.assinantes[tipo_evento].append(tratador)

    def publicar(self, evento):
        for tratador in self.assinantes[type(evento)]:
            tratador(evento)
