# dissmodel/geo/__init__.py

# vector substrate
from .vector.neighborhood       import attach_neighbors
from .vector.vector_grid       import vector_grid, parse_idx
from .vector.fill               import fill, FillStrategy
from .vector.cellular_automaton import CellularAutomaton   
from .vector.spatial_model              import SpatialModel

# raster substrate
from .raster.backend            import RasterBackend, DIRS_MOORE, DIRS_VON_NEUMANN
from .raster.raster_model              import RasterModel
from .raster.cellular_automaton import RasterCellularAutomaton
from .raster.raster_grid       import raster_grid
from .raster.band_spec          import BandSpec   # se tiver classe exportável

# raster io — opcional, não importa por padrão (requer rasterio)
# from .raster.io import load_geotiff, save_geotiff