#! /usr/bin/env python
# -*- coding: utf-8 -*-


"""Export correspondace table to csv or excel"""


import argparse
import logging
import os
import pandas as pd
import sys

from fonction_publique.matching_grade.grade_matching import (
    correspondance_data_frame_path,
    libelles_emploi_directory,
    )

app_name = os.path.splitext(os.path.basename(__file__))[0]
log = logging.getLogger(app_name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', default = correspondance_data_frame_path,
        help = 'path of the source correspondances file')
    parser.add_argument('-t', '--target',
        default = os.path.join(libelles_emploi_directory, 'correspondances.csv'),
        help = 'path of the conversion result i.e. csv file')
    parser.add_argument('--force', action = 'store_true', default = False, help = "force overwrite ")
    parser.add_argument('--separator', default = ';', choices = [',', ';'], help = 'separator (csv only)')
    parser.add_argument('--decimal', default = '.', choices = [',', '.'], help = 'decimal mark (csv only)')
    parser.add_argument('-v', '--verbose', action = 'store_true', default = False, help = "increase output verbosity")

    args = parser.parse_args()
    logging.basicConfig(level = logging.INFO if args.verbose else logging.WARNING, stream = sys.stdout)

    assert args.separator != args.decimal, "Separator and decimal mark cannot be the same: {}".args.decimal
    log.info('Reading data in {}'.format(args.source))
    correspondances = pd.read_hdf(args.source).rename(columns = dict(libelle = 'libemploi_slugified'))
    correspondance_libemploi_slug_h5 = os.path.join(libelles_emploi_directory, 'correspondance_libemploi_slug.h5')
    correspondance_libemploi_slug = (pd.read_hdf(correspondance_libemploi_slug_h5, 'correspondance_libemploi_slug')
        [['libemploi', 'libemploi_slugified']]
        .drop_duplicates()
        )
    output = correspondances.merge(correspondance_libemploi_slug).head(10)
    log.info('Merging with {} to {}'.format(args.source, args.target))

    assert args.target.endswith('.csv'), "Target file name should end with '.csv'"
    log.info('Start converting to {}'.format(args.source, args.target))

    if os.path.exists(args.target) and not args.force:
        log.warn("{} already exists.\nUse -t option to specify a new file or use the --force option to overwrite existing file".format(args.target))
    else:
        output.to_csv(args.target, sep = args.separator, decimal = args.decimal, index = False)


if __name__ == "__main__":
    sys.exit(main())
