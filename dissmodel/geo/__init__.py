# dissmodel/geo/__init__.py

# vector substrate
from .vector.neighborhood       import attach_neighbors
from .vector.regular_grid       import regular_grid, parse_idx
from .vector.fill               import fill, FillStrategy
from .vector.cellular_automaton import CellularAutomaton   
from .vector.model              import SpatialModel

# raster substrate
from .raster.backend            import RasterBackend, DIRS_MOORE, DIRS_VON_NEUMANN
from .raster.model              import RasterModel
from .raster.cellular_automaton import RasterCellularAutomaton
from .raster.regular_grid       import make_raster_grid
from .raster.band_spec          import BandSpec   # se tiver classe exportável

# raster io — opcional, não importa por padrão (requer rasterio)
# from .raster.io import load_geotiff, save_geotiff