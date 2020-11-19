"""
Simulateur du système UDG: thurnabilité
"""
import math
import random
from .base import Strategy, Simulation, Normalien
from dataclasses import dataclass
from typing import Callable
from pprint import pprint
import numpy.random

def fract(x):
    return math.modf(x)[0]


class NeedAThurne(Strategy):
    def play(self, **kwargs):
        al = kwargs.get('al', None)
        if al is None: raise RuntimeError("Invalid simulation system or parameters: no AL found")
        return al if al <= 1 else 1 # Play everything, no choice.

    def __str__(self):
        return '<Stratégie: je veux absolument une thurne>'

class RichPerson(Strategy):
    def play(self, **kwargs):
        al = kwargs.get('al', None)
        if al is None: raise RuntimeError("Invalid simulation system or parameters: no AL found")
        # A rich person will analyse the market before playing.
        # If the AL of the year < 1, they will not play.
        return fract(al) # No matter what, they will always play their fractional part, including if it's zero.

    def __str__(self):
        return '<Stratégie: je peux me loger ailleurs au besoin et garder mon UDG>'


EXP_RANDOM_PARAM = 15 # Entre 10 et 20, selon Milton.
MAX_RANDOMNESS_SIZE = 1 # On ne permet que des ± α où α est dans [0, 9].
RANDOM_THRESHOLD = 0.99 # On ne dépassera pas 99 % de probabilité.

VARIANT_NONUNIFORM = "Variante probabiliste non-uniforme"
VARIANT_RANDOM_CATEGORIES = "Variante à catégories aléatoires"

@dataclass
class UDGConfiguration:
    identifier: str
    function: Callable[[int], int]
    additive_variant: bool = False

class UDG(Simulation):
    strategies = [NeedAThurne, RichPerson] # TODO: the strategy "KnowEverything" should exist, it would perform choice based on the knowledge of all future contexts.
    def __init__(self, config):
        self.al = None
        self.config = config
        self.counter = 0
        self.memory = {} # Book-keep previous UDGs.

    def from_old_system(self, normalien: Normalien) -> Normalien:
        """
        Transforme un normalien donné d'un système archaïque vers
        le système UDG.
        Requiert: al dans metadata.
        """
        if 'al' not in normalien.metadata:
            raise ValueError("Ce normalien n'a pas renseigné son nombre d'AL, impossible de le convertir !")

        assert self.al is not None, "Le système n'a pas d'UDG calculé au préalable, impossible de convertir qui que ce soit."

        self.memory[nouveau.id] = max(0, self.al - normalien.metadata['al']) # Principe de transition d'après Milton.

    def update(self, new_ctx):
        if self.al is not None:
            al_n = self.al
        else:
            al_n = None

        self.al = self.evaluate_al(new_ctx)

        if al_n is not None:
            for id_, U in self.memory.items():
                # FIXME: in the additive variant, we just add some ϵ here, in order to not get out of the system people.
                self.memory[id_] = U*(self.al/al_n) # Actualisation.

    def get_u(self, person):
        return self.memory.get(person.id, self.al)

    def variant(self, play_value):
        if self.config.identifier == VARIANT_NONUNIFORM:
            f = self.config.function
            return min(f(RANDOM_THRESHOLD), f(fract(play_value)) + f(fract(round(numpy.random.exponential(EXP_RANDOM_PARAM), MAX_RANDOMNESS_SIZE)))) # Variante probabiliste non-uniforme.
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
        return {0, fract(balance), int(balance), balance} # Available choices are: 0, {α}, α - {α}, α for α the balance.

    def receive_payment(self, person, amount):
        if person.id not in self.memory:
            self.memory[person.id] = self.al

        cur_balance = self.memory[person.id]
        new_balance = cur_balance - amount if not math.isclose(cur_balance, amount) else 0  # Thanks, IEE754.
        assert new_balance >= 0, "A player cannot play more than its available UDG."
        # Just in case, we allow negative balances in the future.
        self.memory[person.id] = max(0, new_balance)

    def simulate(self, context, people):
        objective = context.nb_thurnes
        self.counter += 1
        chosen = []
        battle = []
        played_nothing = []
        probas = {}

        for person in people:
            played = person.play_strategy(al=self.get_u(person), ctx=context) # UDG amount played.
            assert (played in self.available_playable_choices(person)), f"A player has played a non-accepted amount: {played} (UDG: {self.get_u(person)}), strategy constraint violation"
            probas[person.id] = played
            if played >= 1:
                chosen.append(person)
                self.receive_payment(person, played)
            elif played > 0:
                battle.append((self.variant(played), person))
            else:
                played_nothing.append(person)

        # Catégorie 1: ≥ 1UDG.
        for person in chosen:
            person.thurne = True

        assert len(chosen) <= objective, f"Something went wrong: the set of normaliens who played ≥ 1UDG is larger than the objective, violation of 1UDG = 1 thurne guarantee"

        battle.sort(key=lambda i: i[0], reverse=True) # Sort by decreasing values.
        remaining = min(objective - len(chosen), len(battle))
        # Catégorie 2: 0.01 - 0.99 UDG.
        for _, person in battle[:remaining]:
            played = probas[person.id]
            self.receive_payment(person, played)
            person.thurne = True

        # Catégorie 3: 0UDG.
        if len(chosen) + remaining < objective:
            random.shuffle(played_nothing) # Pure randomness.
            cutoff = objective - (len(chosen) + remaining)
            for person in played_nothing[:cutoff]:
                person.thurne = True


        result = (
                [{'probability': 1, 'person': person, 'thurne': person.thurne, 'cat': 'A'} for person in chosen]
                + [{'probability': probas[person.id], 'person': person, 'thurne': person.thurne, 'cat': 'B'} for _, person in battle]
                + [{'probability': 0, 'person': person, 'thurne': person.thurne, 'cat': 'C'} for person in played_nothing])

        return result # Le résultat.
