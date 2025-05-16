

from dissmodel.core import Model

import matplotlib.pyplot as plt
import streamlit as st
import inspect


def track_plot(label, color, plot_type="line"):
    def decorator(cls):
        if not hasattr(cls, "_plot_info"):
            cls._plot_info = {}
        cls._plot_info[label.lower()] = {
            "plot_type": plot_type,
            "label": label,
            "color": color,
            "data": [],
        }
        return cls
    return decorator




class Chart(Model):
    def setup(self, select= None, pause=True):
        import matplotlib.pyplot as plt
        self.select = select
        self.interval = 1
        self.time_points = []
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel("Tempo")
        self.ax.set_title("Histórico das Variáveis")
        self.pause = pause

    def execute(self):
        import matplotlib.pyplot as plt
        plt.sca(self.ax)
        self.time_points.append(self.env.now())

        # Garante que _plot_metadata exista
        plot_metadata = getattr(self.env, "_plot_metadata", {})
        
        for label, info in plot_metadata.items():   
            if self.select == None or label in self.select:
                self.ax.plot(info["data"], label=label, color=info["color"])

        if self.env.now() == 0:
            plt.legend()

        self.ax.relim()
        self.ax.autoscale_view()
        plt.draw()


        if self.pause:
            plt.pause(0.1)
            if self.env.now() == self.env.end_time:
                plt.show()
