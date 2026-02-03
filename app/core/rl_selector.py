import numpy as np

class RLActionSelector:
    def __init__(self):
        # Simulated historical success rates
        self.success_rates = {
            'respond': 0.8,
            'summarize': 0.7,
            'intent': 0.6,
            'default': 0.5
        }

    def select_action(self, state, actions):
        scores = []
        for action in actions:
            score = 0.0

            # Heuristic 1: Action type - 'respond' gets higher score if state contains keywords
            if action == 'respond' and any(kw in str(state).lower() for kw in ['question', 'urgent']):
                score += 2.0

            # Heuristic 2: Action length - shorter actions preferred
            score -= len(str(action)) * 0.1

            # Heuristic 3: Simulated historical success rates
            score += self.success_rates.get(action, 0.5)

            scores.append(score)

        # Apply softmax to convert scores to probabilities
        scores = np.array(scores)
        exp_scores = np.exp(scores)
        probabilities = exp_scores / np.sum(exp_scores)

        # Selected action: highest probability
        selected_idx = np.argmax(probabilities)
        selected_action = actions[selected_idx]

        # Full probability distribution
        prob_dist = {action: float(prob) for action, prob in zip(actions, probabilities)}

        # Ranked actions list: sorted by probability descending
        ranked = sorted(zip(actions, probabilities), key=lambda x: x[1], reverse=True)
        ranked_actions = [action for action, _ in ranked]

        return selected_action, prob_dist, ranked_actions