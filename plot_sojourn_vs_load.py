#!/usr/bin/env python3

import shelve
import sys

from glob import glob

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

import plot_helpers

dataset, sigma, d_over_n = sys.argv[1:4]
sigma = float(sigma)
d_over_n = float(d_over_n)

for_paper = len(sys.argv) >= 5 and sys.argv[4] == 'paper'

if for_paper:
    plot_helpers.config_paper()

glob_str = 'results_{}_{}_{}_[0-9.]*.s'.format(dataset, sigma, d_over_n)
shelve_files = sorted((float(fname.split('_')[4][:-2]), fname)
                      for fname in glob(glob_str))
loads = [load for load, _ in shelve_files]

no_error = ['FIFO', 'PS', 'FSP (no error)', 'SRPT (no error)']
with_error = ['FIFO', 'PS', 'FSP + FIFO', 'FSP + PS', 'SRPT']

no_error_data = [[] for _ in no_error]
with_error_data = [[] for _ in with_error]

for load, fname in shelve_files:
    res = shelve.open(fname, 'r')
    for i, scheduler in enumerate(no_error):
        no_error_data[i].append(np.array(res[scheduler]).mean())
    for i, scheduler in enumerate(with_error):
        with_error_data[i].append(np.array(res[scheduler]).mean())

figures = [("No error", float(0), no_error, no_error_data),
           (r"$\sigma={}$".format(sigma), sigma, with_error, with_error_data)]

for title, sigma_, schedulers, data in figures:
    plt.figure(title)
    plt.xlabel("load")
    plt.ylabel("mean sojourn time (s)")
    for scheduler, mst, style in zip(schedulers, data,
                                     plot_helpers.cycle_styles('x')):
        plt.semilogy(loads, mst, style, label=scheduler)
    plt.grid()
    plt.legend(loc=2)

    if for_paper:
        fmt = 'sojourn-vs-load_{}_{}_{}.pdf'
        fname = fmt.format(dataset, sigma_, d_over_n)
        plt.savefig(fname)

if not for_paper:
    plt.show()