class Trace:
    def __init__(self):
        self.steps = []

    def log(self, step: str, **data):
        self.steps.append({
            "step": step,
            **data
        })

    def export(self):
        return {
            "steps": self.steps
        }
