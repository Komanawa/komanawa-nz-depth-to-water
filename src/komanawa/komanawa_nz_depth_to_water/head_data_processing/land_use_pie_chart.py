"""
created Evelyn_Charlesworth 
on: 26/05/2023
"""
"""This Python script creates pie chart for land use in the Ashley area based on the NIWA land use layer"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from project_base import gis_data

def get_and_plot_1km_land_use_data():
    """
    This function reads in the land use data and plots a pie chart of the land use within 1km of the coast
    :return:
    """

    # dictionary to store the land types
    land_types = {'DAIRY': 0, 'DEER': 0, 'PAST_OTH_A': 0, 'LC_EXOTIC': 0, 'LC_NATIVE': 0, 'LC_SCRUB': 0,
                  'LC_URBAN': 0, 'OTHER': 0, 'TUSS_DAIRY': 0, 'POTATOES': 0, 'PAST_UNGR': 0, 'MAIZE': 0,
                  'ONIONS': 0, 'KIWIFRUIT': 0, 'APPLES': 0, 'GRAPES': 0, 'HILL': 0, 'HIGH': 0, 'INTENSIV': 0,
                  'LC_WATER': 0}

    # reading in the data
    data_path = gis_data.joinpath('land_use_~1km_coast.csv')
    one_km_land_use_data = pd.read_csv(data_path)

    # accumulate percentages for each land type
    for index, row in one_km_land_use_data.iterrows():
        for land_type in land_types.keys():
            land_types[land_type] += row[land_type]

    # calculate the total area
    total_area = sum(land_types.values())

    # calculate the total percentage for each land type
    land_type_percentages = {land_type: (percentage / total_area) * 100 for land_type, percentage in land_types.items()}

    # filter out land types with zero for plotting
    plotting_land_type_percentages = {land_type: percentage for land_type, percentage in land_type_percentages.items()
                                      if percentage > 0}

    # plotting the pie chart
    # percentage threshold for labelling
    plt.figure(figsize=(8, 8))
    labels = plotting_land_type_percentages.keys()
    sizes = plotting_land_type_percentages.values()
    colours = ['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f', '#e5c494', '#b3b3b3', '#1f78b4',
               '#33a02c',
               '#fb9a99', '#fdbf6f', '#cab2d6', '#6a3d9a', '#ffff99', '#b15928', '#a8ddb5', '#d9d9d9', '#969696',
               '#525252']

    threshold = 2.0
    patches, texts, autotexts = plt.pie(sizes, colors=colours, startangle=90,
                                        autopct=lambda pct: f"{pct:.1f}%" if pct >= threshold else '')
    # this ensures that the pie is circular
    plt.axis('equal')
    plt.legend(patches, labels, loc='best')
    plt.title('Land use % within ~1km of the coast (Ashley Area)')
    plt.savefig(gis_data.joinpath('land_use_~1km_coast.png'))

    return land_type_percentages


def get_and_plot_3km_land_use_data():
    """
    This function reads in the land use data and plots a pie chart of the land use within 3km of the coast
    :return:
    """

    # dictionary to store the land types
    land_types = {'DAIRY': 0, 'DEER': 0, 'PAST_OTH_A': 0, 'LC_EXOTIC': 0, 'LC_NATIVE': 0, 'LC_SCRUB': 0,
                  'LC_URBAN': 0, 'OTHER': 0, 'TUSS_DAIRY': 0, 'POTATOES': 0, 'PAST_UNGR': 0, 'MAIZE': 0,
                  'ONIONS': 0, 'KIWIFRUIT': 0, 'APPLES': 0, 'GRAPES': 0, 'HILL': 0, 'HIGH': 0, 'INTENSIV': 0,
                  'LC_WATER': 0}

    # reading in the data
    data_path = gis_data.joinpath('land_use_~3km_coast.csv')
    one_km_land_use_data = pd.read_csv(data_path)

    # accumulate percentages for each land type
    for index, row in one_km_land_use_data.iterrows():
        for land_type in land_types.keys():
            land_types[land_type] += row[land_type]

    # calculate the total area
    total_area = sum(land_types.values())

    # calculate the total percentage for each land type
    land_type_percentages = {land_type: (percentage / total_area) * 100 for land_type, percentage in land_types.items()}

    # filter out land types with zero for plotting
    plotting_land_type_percentages = {land_type: percentage for land_type, percentage in land_type_percentages.items()
                                      if percentage > 0}

    # plotting the pie chart
    # percentage threshold for labelling
    plt.figure(figsize=(8, 8))
    labels = plotting_land_type_percentages.keys()
    sizes = plotting_land_type_percentages.values()
    colours = ['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f', '#e5c494', '#b3b3b3', '#1f78b4',
               '#33a02c',
               '#fb9a99', '#fdbf6f', '#cab2d6', '#6a3d9a', '#ffff99', '#b15928', '#a8ddb5', '#d9d9d9', '#969696',
               '#525252']

    threshold = 2.0
    patches, texts, autotexts = plt.pie(sizes, colors=colours, startangle=90,
                                        autopct=lambda pct: f"{pct:.1f}%" if pct >= threshold else '')
    # this ensures that the pie is circular
    plt.axis('equal')
    plt.legend(patches, labels, loc='best')
    plt.title('Land use % within ~3km of the coast (Ashley Area)')
    plt.savefig(gis_data.joinpath('land_use_~3km_coast.png'))

    return land_type_percentages


def get_and_plot_5km_land_use():
    """
    This function reads in the land use data and plots a pie chart of the land use within 5km of the coast
    :return:
    """

    # dictionary to store the land types
    land_types = {'DAIRY': 0, 'DEER': 0, 'PAST_OTH_A': 0, 'LC_EXOTIC': 0, 'LC_NATIVE': 0, 'LC_SCRUB': 0,
                  'LC_URBAN': 0, 'OTHER': 0, 'TUSS_DAIRY': 0, 'POTATOES': 0, 'PAST_UNGR': 0, 'MAIZE': 0,
                  'ONIONS': 0, 'KIWIFRUIT': 0, 'APPLES': 0, 'GRAPES': 0, 'HILL': 0, 'HIGH': 0, 'INTENSIV': 0,
                  'LC_WATER': 0}

    # reading in the data
    data_path = gis_data.joinpath('land_use_~5km_coast.csv')
    one_km_land_use_data = pd.read_csv(data_path)

    # accumulate percentages for each land type
    for index, row in one_km_land_use_data.iterrows():
        for land_type in land_types.keys():
            land_types[land_type] += row[land_type]

    # calculate the total area
    total_area = sum(land_types.values())

    # calculate the total percentage for each land type
    land_type_percentages = {land_type: (percentage / total_area) * 100 for land_type, percentage in land_types.items()}

    # filter out land types with zero for plotting
    plotting_land_type_percentages = {land_type: percentage for land_type, percentage in land_type_percentages.items()
                                      if percentage > 0}

    # plotting the pie chart
    # percentage threshold for labelling
    plt.figure(figsize=(8, 8))
    labels = plotting_land_type_percentages.keys()
    sizes = plotting_land_type_percentages.values()
    colours = ['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f', '#e5c494', '#b3b3b3', '#1f78b4',
               '#33a02c',
               '#fb9a99', '#fdbf6f', '#cab2d6', '#6a3d9a', '#ffff99', '#b15928', '#a8ddb5', '#d9d9d9', '#969696',
               '#525252']

    threshold = 2.0
    patches, texts, autotexts = plt.pie(sizes, colors=colours, startangle=90,
                                        autopct=lambda pct: f"{pct:.1f}%" if pct >= threshold else '')
    # this ensures that the pie is circular
    plt.axis('equal')
    plt.legend(patches, labels, loc='best')
    plt.title('Land use % within ~5km of the coast (Ashley Area)')
    plt.savefig(gis_data.joinpath('land_use_~5km_coast.png'))

    return land_type_percentages

def get_and_plot_10km_land_use():
    """
    This function reads in the land use data and plots a pie chart of the land use within 10km of the coast
    :return:
    """

    # dictionary to store the land types
    land_types = {'DAIRY': 0, 'DEER': 0, 'PAST_OTH_A': 0, 'LC_EXOTIC': 0, 'LC_NATIVE': 0, 'LC_SCRUB': 0,
                  'LC_URBAN': 0, 'OTHER': 0, 'TUSS_DAIRY': 0, 'POTATOES': 0, 'PAST_UNGR': 0, 'MAIZE': 0,
                  'ONIONS': 0, 'KIWIFRUIT': 0, 'APPLES': 0, 'GRAPES': 0, 'HILL': 0, 'HIGH': 0, 'INTENSIV': 0,
                  'LC_WATER': 0}

    # reading in the data
    data_path = gis_data.joinpath('land_use_~10km_coast.csv')
    one_km_land_use_data = pd.read_csv(data_path)

    # accumulate percentages for each land type
    for index, row in one_km_land_use_data.iterrows():
        for land_type in land_types.keys():
            land_types[land_type] += row[land_type]

    # calculate the total area
    total_area = sum(land_types.values())

    # calculate the total percentage for each land type
    land_type_percentages = {land_type: (percentage / total_area) * 100 for land_type, percentage in land_types.items()}

    # filter out land types with zero for plotting
    plotting_land_type_percentages = {land_type: percentage for land_type, percentage in land_type_percentages.items()
                                      if percentage > 0}

    # plotting the pie chart
    # percentage threshold for labelling
    plt.figure(figsize=(8, 8))
    labels = plotting_land_type_percentages.keys()
    sizes = plotting_land_type_percentages.values()
    colours = ['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f', '#e5c494', '#b3b3b3', '#1f78b4',
               '#33a02c',
               '#fb9a99', '#fdbf6f', '#cab2d6', '#6a3d9a', '#ffff99', '#b15928', '#a8ddb5', '#d9d9d9', '#969696',
               '#525252']

    threshold = 2.0
    patches, texts, autotexts = plt.pie(sizes, colors=colours, startangle=90,
                                        autopct=lambda pct: f"{pct:.1f}%" if pct >= threshold else '')
    # this ensures that the pie is circular
    plt.axis('equal')
    plt.legend(patches, labels, loc='best')
    plt.title('Land use % within ~10km of the coast (Ashley Area)')
    plt.savefig(gis_data.joinpath('land_use_~10km_coast.png'))

    return land_type_percentages

if __name__ == '__main__':
    a = get_and_plot_1km_land_use_data()
    b = get_and_plot_3km_land_use_data()
    c = get_and_plot_5km_land_use()
    d = get_and_plot_10km_land_use()
    pass