import time as T

class ExecutionEvaluator:
    timers = []
    @staticmethod
    def timer(name):
        for timer in ExecutionEvaluator.timers:
            if timer.name == name:
                return timer
        return ExecutionEvaluator(name)

    def __init__(self, name):
        self.name = name
        self.time = 0
        self.cnt = 0
        self.st, self.ft = 0, 0
        ExecutionEvaluator.timers.append(self)

    def report(self):
        return f'(name={self.name}, number of exec={self.cnt}, mean of exec={0 if self.cnt==0 else self.time/self.cnt})'

    def start(self):
        self.st = T.time()

    def finish(self):
        self.ft = T.time()
        self.cnt += 1
        self.time += self.ft - self.st


    @staticmethod
    def report_all():
        return '\n'.join([timer.report() for timer in ExecutionEvaluator.timers])