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
        help = 'path of the conversion result i.e. csv or xls file')
    parser.add_argument('--format', default = 'csv', choices = ['csv', 'xls'], help = 'target file format')
    parser.add_argument('--separator', default = ';', choices = [',', ';'], help = 'separator (csv only)')
    parser.add_argument('--decimal', default = '.', choices = [',', '.'], help = 'decimal mark (csv only)')
    parser.add_argument('-v', '--verbose', action = 'store_true', default = False, help = "increase output verbosity")

    args = parser.parse_args()
    logging.basicConfig(level = logging.INFO if args.verbose else logging.WARNING, stream = sys.stdout)

    assert args.separator != args.decimal, "Separator and decimal mark cannot be the same: {}".args.decimal
    df = pd.read_hdf(correspondance_data_frame_path)
    if args.format == 'csv':
        assert args.target.endswith('.csv'), "Target file name should end with '.csv'"
    else:
        assert args.target.endswith('.xls'), "Target file name should end with '.xls'"

    log.info('Start converting data in {} to {}'.format(args.source, args.target))

    if args.format == 'csv':
        df.to_csv(args.target, sep = args.separator)
    else:
        df.to_excel(args.target)


if __name__ == "__main__":
    sys.exit(main())
