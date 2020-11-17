"""
Simulateur du système UDG: thurnabilité
"""
import math
from random import random
from base import Strategy, Simulation
from decorators import dataclass
from typing import Callable

def fract(x):
    return math.modf(x)[0]


class NeedAThurne(Strategy):
    def play(self, **kwargs):
        al = kwargs.get('al', None)
        if al is None: raise RuntimeError("Invalid simulation system or parameters: no AL found")
        return al # Play everything, no choice.

    def __str__(self):
        return '<Stratégie: je veux absolument une thurne>'

class RichPerson(Strategy):
    def play(self, **kwargs):
        al = kwargs.get('al', None)
        if al is None: raise RuntimeError("Invalid simulation system or parameters: no AL found")
        # A rich person will analyse the market before playing.
        # If the AL of the year < 1, they will not play.
        if al < 1:
            return 0
        else:
            # In that case, they can play only the fractional part.
            return fract(al) # They keep, thus, 1 AL a priori.

    def __str__(self):
        return '<Stratégie: je peux me loger ailleurs au besoin et garder mon UDG>'


MAX_RANDOMNESS_SIZE = 1 # On ne permet que des ± α où α est dans [0, 9].
RANDOM_THRESHOLD = 0.99 # On ne dépassera pas 99 % de probabilité.

VARIANT_NONUNIFORM = "Variante probabiliste non-uniforme"
VARIANT_RANDOM_CATEGORIES = "Variante à catégories aléatoires"

@dataclass
class UDGConfiguration:
    identifier: str
    function: Callable[[int], int]

class UDG(Simulation):
    strategies = [NeedAThurne, RichPerson] # TODO: the strategy "KnowEverything" should exist, it would perform choice based on the knowledge of all future contexts.
    def __init__(self, config):
        self.al = None
        self.config = config
        self.counter = 0
        self.memory = {} # Book-keep previous UDGs.

    def update(self, new_ctx):
        if self.al is not None:
            al_n = self.al
        else:
            al_n = None

        self.al = self.evaluate_al(new_ctx)

        if al_n is not None:
            for id_, U in self.memory:
                self.memory[id_] = U*(self.al/al_n) # Actualisation.

    def get_u(self, person):
        return self.memory.get(person.id, self.al)

    def variant(self, play_value):
        if self.config.identifier == VARIANT_NONUNIFORM:
            f = self.config.function
            return min(f(RANDOM_THRESHOLD), f(fract(play_value)) + f(fract(round(random(), MAX_RANDOMNESS_SIZE)))) # Variante probabiliste non-uniforme.
        elif self.config.identifier == VARIANT_RANDOM_CATEGORIES:
            raise NotImplementedError # TODO
        else:
            raise ValueError("No such variant for play value adjustment")

    def __str__(self):
        return f'<Système UDG {self.al}, tour numéro {self.counter}, {self.config.identifier}, {len(self.memory)} normaliens dans le système>'

    @staticmethod
    def evaluate_al(context):
        return context.nb_thurnes / context.promo_size # Évaluation proposé par Milton.

    def available_playable_choices(self, person):
        balance = self.get_u(person)
        return {0, fract(balance), balance} # Available choices are: 0, {α}, α for α the balance.

    def receive_payment(self, person, amount):
        if person.id not in self.memory:
            self.memory[person.id] = self.al

        new_balance = self.memory[person.id] - amount
        assert new_balance >= 0, "A player cannot play more than its available UDG."
        # Just in case, we allow negative balances in the future.
        self.memory[person.id] = max(0, new_balance)

    def simulate(self, context, people):
        objective = context.nb_thurnes
        self.counter += 1
        chosen = []
        battle = []
        probas = {}

        for person in people:
            played = person.play_strategy(al=self.get_u(person)) # UDG amount played.
            assert (played in self.available_playable_choices(person)), f"A player has played a non-accepted amount: {played} (UDG: {self.get_u(person)}), strategy constraint violation"
            probas[person.id] = played
            if played >= 1:
                chosen.append(person)
                self.receive_payment(person, played)
            elif played > 0:
                battle.append((self.variant(played), person))

        for person in chosen:
            person.thurne = True

        assert len(chosen) <= objective, f"Something went wrong: the set of normaliens who played ≥ 1UDG is larger than the objective, violation of 1UDG = 1 thurne guarantee"

        battle.sort(key=lambda i: i[0], reverse=True) # Sort by decreasing values.
        remaining = objective - len(chosen)
        for _, person in battle[:remaining]:
            self.receive_payment(person, played)
            person.thurne = True

        result = [{'probability': 1, 'person': person, 'thurne': person.thurne} for person in chosen] + [
                {'probability': probas[person.id], 'person': person, 'thurne': person.thurne} for _, person in battle]
        return result # Le résultat.
