from __future__ import division

import random

from heapq import heapify, heappop, heappush

import schedulers

ARRIVAL, COMPLETE, INTERNAL = 0, 1, 2
eps = 0.001
rand = random.Random()


def identity(x):
    return x


def lognorm_error(sigma, factor=1):
    def err_func(x):
        return factor * x * rand.lognormvariate(0, sigma)
    return err_func


def normal_error(sigma, factor=1):
    def err_func(x):
        while True:
            res = factor * x * rand.gauss(1, sigma)
            if res >= 0:
                return res
    return err_func


def fixed_estimations(estimations):
    estimations_i = iter(estimations)

    def err_func(x):
        return next(estimations_i)
    return err_func


def simulator(jobs, scheduler_factory=schedulers.PS,
              size_estimation=identity, priorities=None):

    events = [(t, ARRIVAL, (jobid, size)) for jobid, t, size in jobs]
    heapify(events)  # not needed if jobs are sorted by arrival time
    remaining = {}   # mapping jobid to remaining size
    schedule = {}    # mapping from jobid to resource ratio -- values
                     # should add up to <= 1
    scheduler = scheduler_factory()

    last_t = 0
    print "events:"
    print events

    if priorities is not None:
        def enqueue(t, jobid, size):
            scheduler.enqueue(t, jobid, size, priorities[jobid])
    else:
        def enqueue(t, jobid, size):
            scheduler.enqueue(t, jobid, size)
        

    while events:  # main loop

        t, event_type, event_data = heappop(events)
	print "current event : event arrival time + event type + data"
	print str(t) + ",  " +str(event_type) + ",  " + str(event_data)
	print 

        delta = t - last_t
	
	print "event delta and last_t"
	print str(delta)+",  "+str(last_t)
	print
        
# update remaining sizes

        for jobid, resources in schedule.items():
            remaining[jobid] -= delta * resources
            #assert remaining[jobid] > -eps
	print "schedule.items at "+str(t)
	print (schedule.items())
	print 
        
	print "remaining times "
	print (remaining)
	print
        
# process event (and call the scheduler)

        if event_type == ARRIVAL:
	    print "arrival " + str(jobid)
            jobid, size = event_data
            remaining[jobid] = size
            enqueue(t, jobid, size_estimation(size))
        elif event_type == COMPLETE:
	    print "complete " + str(jobid) +" at " + str(t)
            jobid = event_data
            #assert -eps <= remaining[jobid] <= eps
            yield t, jobid # t 
            del remaining[jobid]
            scheduler.dequeue(t, jobid)
        schedule = scheduler.schedule(t) 
	print "schedule "+str(schedule) +"  at "+str(t)
 
        #assert sum(schedule.values()) < 1 + eps
        #assert not remaining or sum(schedule.values()) > 1 - eps
        #if (scheduler_factory.__name__ == 'PS'):
        #    assert set(schedule) == set(remaining)

        # if a job would terminate before next event, insert the
        # COMPLETE event

        candidate_event = False
        next_int = scheduler.next_internal_event()
        if next_int is not None:
            next_time = t + next_int
            if (not events) or next_time < events[0][0]:
                candidate_event = next_time, INTERNAL, None

        if remaining:
            completions = ((remaining[jobid] / resources, jobid)
                           for jobid, resources in schedule.items())
	    print "all completions " + str(completions)
            try:
                next_delta, jobid = min(completions)
		print "next delta and job id "+ str((next_delta, jobid))
            except ValueError:  # no scheduled items
		print "no element for min next delta"
                pass
            else:
                #if (scheduler_factory.__name__ == 'FSP'
                #    and size_estimation is identity):
                #    assert schedule == {jobid: 1}
                next_complete = t + next_delta
		print "in else "+ str((next_complete, t, next_delta))

                if not events or events[0][0] > next_complete:
                    if not candidate_event or next_time > next_complete:
			
                        candidate_event = next_complete, COMPLETE, jobid

        if candidate_event:
	    print "pushing new candidate event "+ str(candidate_event)
            heappush(events, candidate_event)

        last_t = t

    assert not remaining
