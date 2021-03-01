from sampler import Simulator, Context, Normalien
from typing import List, Optional, Tuple

def partition_conscrits(normaliens: List[Normalien]) -> Tuple[List[Normalien], List[Normalien]]:
    conscrits, vieux = [], []

    for n in normaliens:
        if n.year == 1:
            conscrits.append(n)
        else:
            vieux.append(n)

    return conscrits, vieux

class RealWorldSimulator(Simulator):
    def compare_classements(self, people) -> List[Normalien]:
        pass

    def prepare(self, initial_context, initial_people) -> List[Normalien]:
        # Utilise le système de transition.
        # Partitionnons initial_people en conscrits (1A) et vieux (≥2A).
        conscrits, vieux = partition_conscrits(initial_people)
        # 1. On calcule l'UDG pour les conscrits.
        # On connaît la taille de la promo et le nombre de thurnes.
        self.s.al = None # On s'assure qu'on démarre à zéro.
        self.s.update(initial_context) # On évalue l'UDG.
        # 2. Transforme les 2A, 3A, 4A selon le système de transition.
        ns = conscrits + list(map(self.s.from_old_system, vieux))

        return ns
