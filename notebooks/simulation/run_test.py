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

simulator.run()
