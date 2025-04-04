"""
created matt_dumont 
on: 6/1/24
"""
from pathlib import Path
import datetime
import matplotlib.pyplot as plt
from build_dataset.update_technial_note.data_stats import get_data_stats, write_rst_table_with_tabulate, \
    get_running_totals
from build_dataset.update_technial_note.statistical_measures_of_dwt_data import hist_sd, exceedance_prob, \
    density_calc_sites, plot_density, npoints_in_dist_calc_sites, plot_points_in_dist

docs_build_dir = Path(__file__).parents[2].joinpath('docs_build')
assert docs_build_dir.exists(), f'{docs_build_dir} does not exist. should not get here'


def update_tech_note(wl_data, metadata, base_outdir=docs_build_dir, figs_only=False):
    """
    Update the technical note with the latest data statistics
    :param wl_data:
    :param metadata:
    :param base_outdir:
    :return:
    """
    base_outdir.mkdir(exist_ok=True)
    base_outdir.joinpath('tables').mkdir(exist_ok=True)
    base_outdir.joinpath('_static').mkdir(exist_ok=True)
    with open(base_outdir.joinpath('last_updated.rst'), 'w') as f:
        f.write(f':Data Last updated: {datetime.date.today().isoformat()}')
    if not figs_only:
        print('updating tables')
        # depth to water statistics
        hist_sd(outdir=base_outdir, wd=wl_data, md=metadata)
        exceedance_prob(outdir=base_outdir, wd=wl_data, md=metadata)

        # summary data
        overview_table, by_source_table = get_data_stats(wl_data, metadata)
        for k in overview_table.index:
            if pd.api.types.is_integer(overview_table.loc[k]):
                overview_table.loc[k] = f'{overview_table.loc[k]:,d}'
            elif pd.api.types.is_float(overview_table.loc[k]):
                overview_table.loc[k] = f'{overview_table.loc[k]:,.2f}'

        write_rst_table_with_tabulate(overview_table, base_outdir.joinpath('tables/full_dataset_summary.rst'),
                                      'Overview of the dataset')
        write_rst_table_with_tabulate(by_source_table, base_outdir.joinpath('tables/by_source_summary.rst'),
                                      'Data summary by source')
    print('creating running totals')
    running_totals = get_running_totals(wl_data)
    for nm, fig in running_totals.items():
        fig.savefig(base_outdir.joinpath('_static', f'{nm}.png'))
        plt.close(fig)
    print('saved running totals, now creating density and points in dist')

    if not figs_only:
        density_calc_sites(metadata)
        npoints_in_dist_calc_sites(metadata)

    plot_density()

    print('saved density, now creating points in dist')
    plot_points_in_dist()
    print('saved points in dist')


if __name__ == '__main__':
    import pandas as pd
    from komanawa.nz_depth_to_water.get_data import get_nz_depth_to_water

    water_level_data, metadata = get_nz_depth_to_water()
    print('update tech note')
    update_tech_note(water_level_data, metadata, figs_only=True)

    pass
