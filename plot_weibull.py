#!/usr/bin/env python3

from __future__ import division

import argparse
import collections
import glob
import shelve
import os.path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, ScalarFormatter, AutoLocator

names = ['FIFO', 'PS', 'SRPT', 'FSP', 'LAS', 'SRPTE', 'SRPTE+PS', 'SRPTE+LAS',
         'FSPE', 'FSPE+PS', 'FSPE+LAS']
axes = 'shape sigma load timeshape njobs est_factor'.split()

plotted = 'FIFO PS LAS SRPTE FSPE FSPE+PS'.split()

styles = {'FIFO': 'k-+', 'PS': 'k--+', 'LAS': 'k-.+',
          'SRPTE': 'r-x', 'FSPE': 'r--x', 'FSPE+PS': 'r-.x'}

parser = argparse.ArgumentParser(description="plot of mean sojourn time")
parser.add_argument('dirname', help="directory in which results are stored")
parser.add_argument('--xaxis', default='shape', choices=axes,
                    help='what to put in the x-axis; default: shape')
parser.add_argument('--linx', default=False, action='store_true',
                    help='linear (instead of logarithmic) x axis')
parser.add_argument('--liny', default=False, action='store_true',
                    help='linear (instead of logarithmic) y axis')
parser.add_argument('--normalize', choices=names,
                    help="normalize against another scheduler")
parser.add_argument('--shape', type=float, default=0.5,
                    help="shape for job size distribution "
                    "(if not on one of the axes); default: 0.5")
parser.add_argument('--sigma', type=float, default=0.5,
                    help="sigma for size estimation error log-normal "
                    "distribution (if not on one of the axes); default: 0.5")
parser.add_argument('--load', type=float, default=0.9,
                    help="load for the generated workload; default: 0.99")
parser.add_argument('--timeshape', type=float, default=1,
                    help="shape for the Weibull distribution of job "
                    "inter-arrival times; default: 1 (i.e. exponential)")
parser.add_argument('--njobs', type=int, default=10000,
                    help="number of jobs in the workload; default: 10000")
parser.add_argument('--est_factor', type=float,
                    help="multiply estimated size by this value")
parser.add_argument('--nolatex', default=False, action='store_true',
                    help="disable LaTeX rendering")
args = parser.parse_args()

if not args.est_factor and 'est_factor' != args.xaxis:
    axes.pop()

xaxis_idx = axes.index(args.xaxis)

fname_regex = [str(getattr(args, ax)) for ax in axes]
fname_regex[xaxis_idx] = '[0-9.]*'
glob_str = os.path.join(args.dirname,
                        'res_{}_[0-9.]*.s'.format('_'.join(fname_regex)))
fnames = glob.glob(glob_str)

cache = shelve.open(os.path.join(args.dirname, 'cache.s'))
def getmean(fname, scheduler):
    key = '{}_mean_{}'.format(os.path.split(fname)[1], scheduler)
    try:
        return cache[key]
    except KeyError:
        shelve_ = shelve.open(fname, 'r')
        mean = np.array(shelve_[scheduler]).mean()
        shelve_.close()
        cache[key] = mean
        return mean

results = collections.defaultdict(lambda: collections.defaultdict(list))
for fname in fnames:
    print('.', end='', flush=True)
    split = os.path.splitext(os.path.split(fname)[1])[0].split('_')[1:-1]
    xval = float(split[xaxis_idx])
    if args.xaxis == 'load':
        xval = 1 - xval
    for scheduler in plotted:
        try:
            mst = getmean(fname, scheduler)
            if args.normalize:
                mst = mst / getmean(fname, args.normalize)
        except:
            # the file is being written now
            continue
        results[scheduler][xval].append(mst)
cache.close()

print()

def load_linformat(x, pos):
    return str(1 - x)
load_linformatter = FuncFormatter(load_linformat)

fig = plt.figure(figsize=(8, 4.5))
ax = fig.add_subplot(111)
ax.set_xlabel(args.xaxis)
if args.normalize:
    ylabel = "MST / MST({})".format(args.normalize)
else:
    ylabel = "Mean sojourn time"
ax.set_ylabel(ylabel)
for scheduler in plotted:
    sched_results = sorted(results[scheduler].items())
    xs, ys = zip(*[(x, sum(ys) / len(ys)) for x, ys in sched_results])
    style = styles[scheduler]
    if args.linx:
        if args.liny:
            plotfun = ax.plot
        else:
            plotfun = ax.semilogy
    else:
        if args.liny:
            plotfun = ax.semilogx
        else:
            plotfun = ax.loglog
    plotfun(xs, ys, style, label=scheduler, linewidth=2, markersize=10)

ax.legend(loc=0, ncol=2)
ax.tick_params(axis='x', pad=7)

if args.xaxis == 'load':
    ax.xaxis.set_major_formatter(load_linformatter)
    ax.xaxis.set_ticks([0.5, 0.1, 0.01, 0.001])

if args.xaxis in ['shape', 'sigma', 'timeshape']:
    ax.xaxis.set_ticks([0.125, 0.25, 0.5, 1, 2, 4])
    ax.xaxis.set_ticklabels('0.125 0.25 0.5 1 2 4'.split())
    
ax.yaxis.set_major_formatter(ScalarFormatter())

minvs = min(min(vs) for vs in results.values())
maxvs = max(max(vs) for vs in results.values())

if args.xaxis == 'load':
    ax.set_xlim(maxvs, 0.00098)
else:
    ax.set_xlim(minvs, maxvs)

if not args.nolatex:
    import plot_helpers
    plot_helpers.config_paper(15)

plt.tight_layout(1)
    
plt.show()