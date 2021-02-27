from udg import UDG, UDGConfiguration, VARIANT_NONUNIFORM, VARIANT_RANDOM_CATEGORIES
from sampler import Simulator, ScenarioEvent, Scenario

# Scénario de grosse décroissance avant recroissance plus tard.
scenario = Scenario([
        ScenarioEvent.INCREASING,  # TG21.
        ScenarioEvent.SUPER_DECREASING, # TG22
        ScenarioEvent.STABLE, # TG23
        ScenarioEvent.INCREASING, # TG24
        ScenarioEvent.INCREASING, # TG25
        ScenarioEvent.STABLE # TG26
        ])
# Tel que décrit par Milton.
simulator = Simulator(
        UDG(UDGConfiguration(identifier=VARIANT_RANDOM_CATEGORIES, function=lambda x: 100*x)),
        scenario)

def extract_kpi(raw_simulation_result):
    cats = ["A", "B", "C"]
    kpis = {}
    for c in cats:
        individuals = [i for i in raw_simulation_result if i['cat'] == c]
        c_loge = sum(1 for individual in individuals if individual['thurne'])
        kpis[f"{c}_total"] = len(individuals)
        kpis[f"{c}_logé"] = c_loge

    return kpis

raw_results = simulator.run()

kpis = []
for rr in raw_results:
    kpis.append(extract_kpi(rr["result"]))
