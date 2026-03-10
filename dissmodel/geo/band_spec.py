from dataclasses import dataclass


@dataclass
class BandSpec:
    """
    Specification of a raster band in a GeoTIFF.

    Attributes
    ----------
    name : str
        Name used inside RasterBackend (e.g. 'uso', 'alt', 'soil').
    dtype : str
        NumPy dtype used to store the band.
    nodata : float | int
        Value representing missing data.
    """

    name: str
    dtype: str
    nodata: float | int