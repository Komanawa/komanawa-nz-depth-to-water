# Introduction

This project provides a comprehensive suite of Python scripts designed for cleaning and processing groundwater
data from various regions across New Zealand. It supports data from Auckland, Bay of Plenty, Canterbury,
Gisborne, Hawke's Bay, Horizons, Marlborough, Northland, Otago, Southland, Taranaki, Tasman, Waikato,
Wellington, and West Coast. The project aims to standardize the groundwater data, making it more
accessible and usable for analysis.

# Prerequisites

Before you begin, ensure you have met the following requirements:
conda create -c conda-forge --name futcoast python numpy pandas pytables openpyxl
matplotlib scipy netcdf4 psutil geopandas flopy pysheds scikit-learn py7zr pyemu
conda activate futcoast
komanawa-kslcore.git
komanawa-modeltools.git
komanawa-ksl-tools.git

# Usage

The main functionality of this project is encapsulated in various modules, each responsible for
processing data from a specific region. To use these modules, you can import the necessary functions in
your Python scripts or use them interactively in a Python environment.

# Example script usage:

python
Copy code
from project_module import get_auk_data

Call the function to process Auckland groundwater data
auk_data = get_auk_data(recalc=True)

# Main function - build_final_database.py

## Overview
This Python script is designed to consolidate processed groundwater data from various individual databases into a
single, unified database for both data and metadata. It automates the integration of data from different regions,
handling metadata and elevation details, and ensuring consistency across the combined dataset.

## Functions Overview
build_final_meta_data(recalc=False): Generates a consolidated metadata database from multiple sources. Set recalc to
True to force a recalculation of the metadata.

build_final_water_data(recalc=False, recalc_sub=False, redownload=False): Aggregates water data from various sources
into a single database. The recalc parameter controls the recalculation of the final water data, recalc_sub controls the
recalculation of individual water data sources, and redownload controls whether to redownload the source data.

Notes
The script uses the HDF5 format for efficient storage and access to large datasets.
Elevation data is sampled from LiDAR DEMs where available, providing accurate ground elevation information to complement
the water data.
Error handling and data validation are integral parts of the script, ensuring the integrity of the combined datasets.