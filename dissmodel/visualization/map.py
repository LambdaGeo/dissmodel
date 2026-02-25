import matplotlib.pyplot as plt
from dissmodel.core import Model
from dissmodel.visualization._utils import is_interactive_backend

# Função auxiliar para detectar se está rodando em notebook
def is_notebook():
    try:
        from IPython import get_ipython
        shell = get_ipython().__class__.__name__
        return shell == "ZMQInteractiveShell"
    except Exception:
        return False


class Map(Model):
    def setup(self, gdf, plot_params, pause=True, plot_area=None):
        
        if not is_notebook():
            self.fig, self.ax = plt.subplots(1, 1, figsize=(10, 6))

        self.plot_params = plot_params
        self.pause = pause
        self.gdf = gdf
        self.plot_area = plot_area

    def update(self, year, gdf):

        

        if is_notebook():        
            from IPython.display import clear_output
            clear_output(wait=True)  # Limpa a saída do notebook para exibir apenas o gráfico atualizado
            self.fig, self.ax = plt.subplots(1, 1, figsize=(10, 6))

        

        # evitar de ficar duplicando legenda
        self.fig.clf()
        self.ax = self.fig.add_subplot(1, 1, 1)
        
        self.gdf.plot(ax=self.ax, **self.plot_params)
        self.ax.set_title(f'Mapa - Ano {year}')
        plt.tight_layout()
        plt.draw()

        if self.plot_area:
            # Modo Streamlit
            self.plot_area.pyplot(self.fig)
        elif is_notebook():
            # Modo Jupyter Notebook
            from IPython.display import display
            display(self.fig)    
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


    def execute(self):
        year = self.env.now()
        self.update(year, self.gdf)
