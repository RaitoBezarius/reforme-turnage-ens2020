from udg import UDG, UDGConfiguration, VARIANT_NONUNIFORM
from sampler import Simulator, ScenarioEvent, Scenario

# Scénario de grosse décroissance avant recroissance plus tard.
scenario = Scenario([
        ScenarioEvent.SUPER_DECREASING,  # TG21.
        ScenarioEvent.STABLE, # TG22
        ScenarioEvent.INCREASING, # TG23
        ScenarioEvent.INCREASING, # TG24
        ScenarioEvent.STABLE, # TG25
        ScenarioEvent.STABLE # TG26
        ])
# Tel que décrit par Milton.
simulator = Simulator(
        UDG(UDGConfiguration(identifier=VARIANT_NONUNIFORM, function=lambda x: 100*x)),
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
