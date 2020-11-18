import bisect
import random
from base import Normalien, Context, Simulation
from typing import List, Optional, NewType
from collections import defaultdict
from enum import IntEnum
from pprint import pprint

def mex(A): # Must be sorted to be efficient: O(mex(A)), i.e. worst case, linear.
    c = 0
    for x in A:
        if c != x:
            return c
        c += 1

    return c + 1

DEFAULT_NB_THURNES = 320
DEFAULT_PROMO_SIZE = 200
POPULATION_SIZE_BY_STATUT = {
    "eleve": 200,
    "etudiant": 132,
    "etudiant-si": 20
}

LAST_YEAR = {
    "eleve": 4,
    "etudiant": 3,
    "etudiant-si": 3,
    "masterien": 2
}

class ScenarioEvent(IntEnum):
    STABLE = 0 # Variation de 1% à 5%
    INCREASING = 1 # Augmentation de 10-20 % du nombre de thurnes
    DECREASING = 2 # Diminution de 10-20 % du nombre de thurnes
    SUPER_INCREASING = 3 # Super augmentation de 40-70 % du nombre de thurnes
    SUPER_DECREASING = 4 # Super diminution de 40-70 % du nombre de thurnes

Scenario = NewType("Scenario", List[ScenarioEvent])

def imagine_context(prev_ctx: Context, event: ScenarioEvent) -> Context:
    if event == ScenarioEvent.STABLE:
        V = 1 + random.randint(10, 50) / 1000
    elif event == ScenarioEvent.INCREASING:
        V = 1 + random.randint(10, 20) / 100
    elif event == ScenarioEvent.DECREASING:
        V = 1 - random.randint(10, 20) / 100
    elif event == ScenarioEvent.SUPER_INCREASING:
        V = 1 + random.randint(40, 70) / 100
    elif event == ScenarioEvent.SUPER_DECREASING:
        V = 1 - random.randint(40, 70) / 100
    else:
        raise ValueError(f"Context cannot be imagined with an unknown event: {ScenarioEvent(event)}")

    return Context(
            nb_thurnes=int(V*prev_ctx.nb_thurnes), # Multiplicatif, est ce un problème ? FIXME: peut-on faire les choses un peu mieux concernant ça? sampler une vraie distribution?
            promo_size=prev_ctx.promo_size, # Cela ne change pas vraiment, sauf modification dans les décrets ou comportements collectifs.
            future=None,
            past=prev_ctx)

class Simulator:
    def __init__(self,
            simulation: Simulation,
            scenario: Scenario,
            initial_context: Optional[Context] = None):
        self.s = simulation
        self.scenario = scenario
        self.initial_ctx = initial_context or Context(
                nb_thurnes=DEFAULT_NB_THURNES,
                promo_size=DEFAULT_PROMO_SIZE,
                future=None,
                past=None)

    def generate_contexts(self, n: int = 5) -> List[Context]:
        # Il faut sampler un ensemble de N contextes.
        # Notamment pour backfiller les contextes futurs et passés.
        contexts = [self.initial_ctx] * n

        for i in range(1, n):
            # Comment prévoir des évolutions?
            # Il faut des scénarios.
            # Un scénario est la donnée d'une liste d'évenements:
            # stable, stable, croissance, décroissance, etc.
            # Ils peuvent encoder une forme de brutalité.
            event = self.scenario[i - 1]

            contexts[i] = imagine_context(contexts[i - 1], event)
            contexts[i - 1].future = contexts[i]

        return contexts

    def random_variation_on_outgoing(self):
        """
        Retourne un Δ < 0 pour faire varier les normaliens sortants.
        Interprétation: CST, rallonge d'études, etc.
        """
        return 0 # No lo sé yet how to handle it.

    def generate_normaliens(self, context: Context, previous_generation: Optional[List[Normalien]] = None) -> List[Normalien]:
        # Donc, on simule la sortie d'une promo de normaliens.
        # L'entrée d'une promo de normaliens.

        # Deux comportements principaux.
        # (a) Faire une CST, être un normalien une année de plus.
        # (b) Ne pas s'inscrire au thurnage général car on a une autre solution: turnage partiel ou externe.
        # Il faut donc contrôler le nombre de CST au cours d'une année.
        # Il faut donc contrôler le nombre de non-inscriptions au thurnage général:
        #  - Soit en se basant sur une métrique de température du thurnage général: pas assez de thurnes => même pas besoin de s'inscrire, etc.
        #  - Soit ???
        # FIXME: choisir des stratégies basé sur le statut du normalien, modéliser la précarité des étudiants/SI (non salariés) et la pseudo-aisance des élèves (salariés).

        # 1. Générer la nouvelle promotion de 2A: 100% des 1A.
        nv_promo = []
        ids = sorted([p.id for p in previous_generation]) if previous_generation else []

        for statut, size in POPULATION_SIZE_BY_STATUT.items():
            for _ in range(size//2): # FIXME: Bouh, c'est moche, que faire?
                new_id = mex(ids) # linear.
                n = Normalien(new_id,
                        random.choice(self.s.strategies)(),
                        statut=statut)
                n.year += 1 # 2A.
                nv_promo.append(n)
                bisect.insort(ids, new_id) # sorted append: linear.

        # 2. Sampler les sortants de 3A et 4A selon les statuts.
        people_by_statut = defaultdict(list)
        for p in (previous_generation or []):
            if p.statut is not None:
                people_by_statut[p.statut].append(p)

        last_year_by_statut = defaultdict(list)
        for statut in POPULATION_SIZE_BY_STATUT.keys():
            ly = LAST_YEAR[statut]
            for p in people_by_statut[statut]:
                # Est ce que ce normalien était en dernière année, vis à vis de son statut?
                if p.year == ly:
                    last_year_by_statut[statut].append(p)

        normaliens = set(previous_generation or [])
        for statut, size in POPULATION_SIZE_BY_STATUT.items():
            # Y'a-t-il assez de normaliens à sortir?
            if len(last_year_by_statut[statut]) > 0: # FIXME: Bouch, c'est moche aussi, que faire?
                outgoing = size//2 + self.random_variation_on_outgoing() # Population d'entrée ± variation aléatoire, paramétrable.
                # Merci, pour l'aventure. Au revoir.
                byebye_people = set(random.sample(last_year_by_statut[statut], outgoing))
                normaliens -= byebye_people
                # On ne met pas à jour people_by_statut et last_year_by_statut.
                # C'est une perte de temps.

        # 3. On met à jour l'année de chaque normalien retenu.
        for n in normaliens:
            n.year += 1
            # TODO: veut-on autoriser le changement de stratégie?

        # 4. À ce stade, normaliens constitue un ensemble de normaliens inscrits au thurnage général.
        return list(normaliens | set(nv_promo))

    def evaluate_result(self, result, context, people):
        # On dispose de la probabilité de thurnabilité des gens.
        esperance = sum(issue['probability'] for issue in result) # E(X) = sum E(X_i) = sum P(X_i) pour X_i de Bernouilli
        obtenu = sum(issue['thurne'] for issue in result)

        print(f'\t\tTotal normaliens: {len(people)}\n\t\tTotal thurnes: {context.nb_thurnes}\n\t\tEspérance: {round(esperance, 2)}\n\t\tPersonnes thurnés: {obtenu}')


    def run(self, contexts=None, peoples=None):
        if contexts is None:
            contexts = self.generate_contexts() # Sample contexts.
        if peoples is None:
            peoples = [None] * len(contexts)

        for index, context in enumerate(contexts):
            if index > 0:
                # ensure organic generation.
                previous_gen = peoples[index - 1]
                p = peoples[index] or self.generate_normaliens(context, previous_gen)
            else:
                p = peoples[0] or self.generate_normaliens(context, peoples[0])

            peoples[index] = p

        for index, (p, context) in enumerate(zip(peoples, contexts)):
            self.s.update(context)
            result = self.s.simulate(context, p)
            thurne = [r for r in result if r['thurne']]
            print(f'\n\tAnnée {index + 1}')
            assert len(thurne) <= context.nb_thurnes, f"Violation de la loi de la conservation de thurnes, plus de thurnes attribué ({len(thurne)}) que physiquement disponible ({context.nb_thurnes})!"
            self.evaluate_result(result, context, p)
            # Réinitialisation de la thurnabilité.
            for q in p:
                q.thurne = False

        # Évaluation rétro-spective sur les N années.
        # On regarde maintenant la variable A_id qui donne le nombre d'années logés à l'ENS.
        # Sur un échantillon représentatif, est ce que 1/N (sum_i A_i) ~ E(A) ~ objectif.
        # objectif \in {1.5, 2, 3}.
