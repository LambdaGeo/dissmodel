from dissmodel.core import Model
import matplotlib.pyplot as plt
import inspect
import streamlit as st
from IPython.display import display, Image
import io

from dissmodel.visualization._utils import is_interactive_backend

# Função auxiliar para detectar se está rodando em notebook
def is_notebook():
    try:
        from IPython import get_ipython
        shell = get_ipython().__class__.__name__
        return shell == "ZMQInteractiveShell"
    except Exception:
        return False

# Decorador para registrar variáveis a serem plotadas
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
    def setup(
        self,
        select=None,
        pause=True,
        plot_area=None,
        show_legend=True,       
        show_grid=False,        
        title="Histórico das Variáveis"  # Permite customizar o título
    ):
        self.select = select
        self.interval = 1
        self.time_points = []
        self.pause = pause
        self.plot_area = plot_area
        self.show_legend = show_legend
        self.show_grid = show_grid
        self.title = title

        if not is_notebook():
            self.fig, self.ax = plt.subplots()
            self.ax.set_xlabel("Tempo")
            self.ax.set_title(self.title)

    def execute(self):
        if is_notebook():
            from IPython.display import clear_output
            clear_output(wait=True)
            self.fig, self.ax = plt.subplots()
            self.ax.set_xlabel("Tempo")
            self.ax.set_title(self.title)

        plt.sca(self.ax)
        self.time_points.append(self.env.now())

        plot_metadata = getattr(self.env, "_plot_metadata", {})

        self.ax.clear()
        self.ax.set_xlabel("Tempo")
        self.ax.set_title(self.title)

        for label, info in plot_metadata.items():
            if self.select is None or label in self.select:
                self.ax.plot(info["data"], label=label, color=info["color"])

        # Mostrar grade se habilitado
        if self.show_grid:
            self.ax.grid(True)

        # Mostrar legenda se habilitado
        if self.show_legend:
            self.ax.legend()

        self.ax.relim()
        self.ax.autoscale_view()
        plt.tight_layout()
        plt.draw()

        if self.plot_area:
            # Modo Streamlit
            self.plot_area.pyplot(self.fig)
        elif is_notebook():
            buf = io.BytesIO()
            self.fig.savefig(buf, format='png')
            buf.seek(0)
            display(Image(data=buf.read()))
            plt.close(self.fig)
        elif self.pause:
            if is_interactive_backend():
                plt.pause(0.1)
                if self.env.now() == self.env.end_time:
                    plt.show()
            else:
                raise RuntimeError(
                    "No interactive matplotlib backend detected. "
                    "Add this to the top of your script:\n\n"
                    "    import matplotlib\n"
                    "    matplotlib.use('TkAgg')  # or 'Qt5Agg'\n"
                )
