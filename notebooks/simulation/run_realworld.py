import pandas as pd
from itertools import chain
from collections import defaultdict
from udg import UDG, UDGConfiguration, VARIANT_NONUNIFORM, VARIANT_RANDOM_CATEGORIES
from base import Normalien, Context, Strategy
from sampler import ScenarioEvent, Scenario, DEFAULT_PROMO_SIZE
from realworld import RealWorldSimulator
from typing import List
import matplotlib.pyplot as plt

class TransitionStrategy(Strategy):
    def __init__(self, jokers: int, strict: bool = True):
        self.strict = strict
        self.jokers = jokers
    def play(self, **kwargs):
        al = kwargs.get('al', None)
        if self.jokers >= 2:
            will = 1
        elif self.jokers == 1:
            will = 1
        elif self.jokers == 1:
            will = al/2
        elif self.jokers == 0:
           will = al/3

        if self.strict:
            return will
        else:
            return al if will >= al else will

    def __str__(self):
        return '<Stratégie: je joue {} jokers mais en UDG (strict: {})>'.format(self.jokers, self.strict)

def normaliens_from_export(df) -> List[List[Normalien]]:
    normaliens_per_year = defaultdict(list)

    for row in df.itertuples(index=False):
        year, login, _, ranking, jokers, _, scol, al = row
        n = Normalien(id_=login, strategy=TransitionStrategy(jokers, strict=False), statut="égalité pour tous, ok?", metadata={'al': al, 'ranking': ranking, 'jokers': jokers})
        if scol == "CST":
            print(f"Avertissement: {login} est en CST, cela n'est pas géré")
        elif int(scol) >= 2:
            n.year = int(scol) - 1
            normaliens_per_year[year].append(n)

    for _, normaliens in sorted(normaliens_per_year.items(), key=lambda kv: kv[0]):
        yield normaliens

def contexts_from_export(df, perfect_information: bool = False) -> List[Context]:
    per_year = df.groupby('année')
    contexts = [None] * len(per_year)

    nb_thurnes = per_year.thurne.count()

    for i, nb_thurnes in zip(range(len(contexts)), nb_thurnes):
        contexts[i] = Context(
                nb_thurnes=nb_thurnes,
                promo_size=DEFAULT_PROMO_SIZE
        )

    for i in range(1, len(contexts) - 1):
        contexts[i - 1].future = contexts[i]
        contexts[i + 1].past = contexts[i]
        if perfect_information:
            pass # contexts[i].promo_size = # the true amount of conscrits in TG.

    return contexts

export_df = pd.read_csv("./export.csv")
# Lire le passé, c'est comprendre le futur.
past_peoples = list(normaliens_from_export(export_df))
past_contexts = contexts_from_export(export_df)

# Backtesting de scénario + prédiction.
# scenario = scenario_from_past(past) + [ScenarioEvent.INCREASING] # Prédiction sur le TG21.


def extract_kpi(raw_simulation_result):
    cats = ["A", "B", "C"]
    kpis = {}
    for c in cats:
        individuals = [i for i in raw_simulation_result if i['cat'] == c]
        c_loge = sum(1 for individual in individuals if individual['thurne'])
        kpis[f"{c}_total"] = len(individuals)
        kpis[f"{c}_logé"] = c_loge

    return kpis

def evaluate_repartition():
    raw_results = run_simulation()
    kpis = []

    for rr in raw_results:
        kpis.append(extract_kpi(rr["result"]))

    pd.DataFrame(kpis, index=range(5)).plot(kind='bar', figsize=(10, 10))
    plt.show()

def volatility_for_a_person(personal_results):
    avg_p = sum(result['probability'] for result in personal_results) / len(personal_results)
    empirical_p = sum(1 for result in personal_results if result['thurne'])/len(personal_results)

    # deviation de la probabilité empirique avec la probabilité moyenne.
    return avg_p, empirical_p

def evaluate_volatility(runs: int = 5_000):
    results_per_id_and_year = defaultdict(list)
    year = 0
    for i in range(runs):
        rr = run_simulation(past_contexts.copy(), past_peoples.copy(), print_evaluation=False)
        for year, yr in enumerate(rr):
            for result in yr['result']:
                results_per_id_and_year[(result['person'].id, year)].append(result)
        print(f'{i + 1}/{runs}')

    devs = defaultdict(list)
    for (_, year), rr in results_per_id_and_year.items():
        avg_p, emp_p = volatility_for_a_person(rr)
        devs[year].append(abs(avg_p - emp_p))

    return pd.concat({2016 + k: pd.Series(v) for k, v in devs.items()})


def run_simulation(ctxs, peoples, print_evaluation = True):
    # Tel que décrit par Milton.
    simulator = RealWorldSimulator(
            UDG(UDGConfiguration(identifier=VARIANT_RANDOM_CATEGORIES, function=None)))

    simulator.prepare(ctxs[0], peoples[0])
    return simulator.run(
            contexts=ctxs,
            peoples=peoples,
            print_evaluation=print_evaluation)
