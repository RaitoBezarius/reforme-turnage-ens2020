from decorators import dataclass
from typing import List

@dataclass
class Context:
    nb_thurnes: int
    promo_size: int

class Normalien:
    def __init__(self, id_, strategy):
        self.id = id_
        self.strategy = strategy
        self.thurne = False

    def play_strategy(self, **kwargs):
        return self.strategy(**kwargs)

    def __str__(self):
        return f'<Normalien numéro {self.id}, utilisant {self.strategy}, thurné: {self.thurne}>'


class Strategy:
    def play(self, **kwargs):
        raise NotImplementedError

    def __str__(self):
        return '<Stratégie abstraite>'

class Simulation:
    def update(self, new_ctx: Context):
        raise NotImplementedError

    def __str__(self):
        return '<Système de thurnage abstrait>'

    def simulate(self, context: Context, people: List[Normalien]):
        raise NotImplementedError
