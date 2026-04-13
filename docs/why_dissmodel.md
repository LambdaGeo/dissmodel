# Why DisSModel?

## Pythonic Modeling
Before DisSModel, many spatial modeling tools required learning domain-specific languages (DSL) or older stacks. We believe **Spatial Modeling is Data Science**. By building on Python, we offer:

- **Full Stack Integration**: Use Scikit-Learn or PyTorch inside your model rules.
- **Active Community**: Leverage the best geospatial libraries (GeoPandas, libpysal) directly.
- **Academic Rigor**: Designed at [UFMA](https://www.ufma.br/) to support high-level research in coastal dynamics and LUCC.

---

## Key Advantages

### 1. Reproducibility First
Unlike many modeling tools where results are "volatile", DisSModel treats every run as an **Experiment**. With built-in SHA256 hashing and TOML snapshots, you can reproduce a simulation exactly as it was run years ago.

### 2. The Dual-Substrate Hybrid
You don't have to choose between GIS precision and speed. Use **Vector** for administrative boundaries and **Raster** for physical processes (like floods or fires) within the same environment.

### 3. Decoupled Architecture
Your scientific code (the `Model`) doesn't need to know if the data is on your SSD or in a MinIO bucket in the cloud. The `io` and `executor` modules handle the plumbing, so you can focus on the equations.

---

## From Research to Production
DisSModel started as a thesis project and evolved into a production-ready framework. It is currently being used to model mangrove succession and coastal flooding, proving its capability in real-world, high-impact scenarios.