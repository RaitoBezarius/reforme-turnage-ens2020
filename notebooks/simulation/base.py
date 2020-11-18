from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Context:
    nb_thurnes: int
    promo_size: int
    future: Optional['Context'] = None
    past: Optional['Context'] = None

class Normalien:
    def __init__(self, id_, strategy, statut=None, metadata=None):
        self.id = id_
        self.strategy = strategy
        self.thurne = False
        self.year = 1 # conscrit.
        self.statut = statut
        self.metadata = metadata or {}

    def play_strategy(self, **kwargs):
        return self.strategy.play(**kwargs)

    def __str__(self):
        return f'<Normalien numéro {self.id}, {self.year}A, utilisant {self.strategy}, thurné: {self.thurne}, statut: {self.statut}, metadata: {self.metadata}>'

    def __repr__(self):
        return str(self)


class Strategy:
    def play(self, **kwargs):
        raise NotImplementedError

    def __str__(self):
        return '<Stratégie abstraite>'

    def __repr__(self):
        return str(self)

class Simulation:
    strategies: List[Strategy] = []
    def update(self, new_ctx: Context):
        raise NotImplementedError

    def __str__(self):
        return '<Système de thurnage abstrait>'

    def simulate(self, context: Context, people: List[Normalien]):
        raise NotImplementedError
