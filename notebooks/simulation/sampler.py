class Simulator:
    def __init__(self, simulation):
        self.s = simulation

    def generate_contexts(self):
        pass

    def generate_normaliens(self):
        # Par promo, il y a 200 normaliens élèves, 132 normaliens étudiants (parfois un peu moins) et 20 élèves SI.
        # Donc, on simule la sortie d'une promo de normaliens.
        # L'entrée d'une promo de normaliens.
        self.s.strategies

    def evaluate_result(self, result, context, people):
        # On dispose de la probabilité de thurnabilité des gens.
        esperance = sum(issue['probability'] for issue in result) # E(X) = sum E(X_i) = sum P(X_i) pour X_i de Bernouilli
        obtenu = sum(issue['thurne'] for issue in result)

        print(f'\tEspérance: {esperance}\n\tPersonnes thurnés: {obtenu}')


    def run(self, contexts=None, peoples=None):
        if contexts is None:
            contexts = self.generate_contexts() # Sample contexts.
        if peoples is None:
            peoples = [None] * len(contexts)

        for people, context in zip(contexts, peoples):
            people = people or self.generate_normaliens(context)
            self.s.update(context)
            result = self.s.simulate(context, people)
            self.evaluate_result(result, context, people)

        # Évaluation rétro-spective sur les N années.
        # On regarde maintenant la variable A_id qui donne le nombre d'années logés à l'ENS.
        # Sur un échantillon représentatif, est ce que 1/N (sum_i A_i) ~ E(A) ~ objectif.
        # objectif \in {1.5, 2, 3}.
