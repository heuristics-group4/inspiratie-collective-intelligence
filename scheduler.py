import time
import sys
import os
import random
import fileinput

import general

tickets = general.loadSingleTickets(os.path.abspath("singletickets.txt"))
retourtickets = general.loadRetourTickets(os.path.abspath("retourtickets.txt"))

domain = []
flights = {}

# Store tickets together for each (source city,destination city) pair.
# This allows looking up all tickets a person can take, and implicitely
# gives every ticket a unique index that is used later on.
for ticket in tickets:
    pair = (ticket.sourceCity,ticket.destCity)
    if (pair in flights):
        flights[pair].append(ticket)
    else:
        flights[pair] = [ticket]

# This code determines the maximum ticket index each person may use.
# This is stored in the domain variable which is used by the different
# optimization algorithms.
for p in range(len(general.people)):
    persondata = general.people[p]
    name = persondata[0]
    airfield = persondata[1]
    domain.append((0,len(flights[(airfield,general.destinationCity)])-1))
    domain.append((0,len(flights[(general.destinationCity,airfield)])-1))

def printschedule(sol):
  totalcosttickets = 0
  print '      Name      City Flight Arriv      Flight Depar'
  for d in range(len(sol)/2):
    name=general.people[d][0]
    origin=general.people[d][1]
    outbound=flights[(origin,general.destinationCity)][int(sol[d*2])]
    returnf=flights[(general.destinationCity,origin)][int(sol[d*2+1])]
    ticketcost = outbound.cost + returnf.cost
    retour = 0
    
    for retourticket in retourtickets:
      if outbound.ID == retourticket.flight1 and returnf.ID == retourticket.flight2:
        ticketcost = retourticket.cost
        retour = 1

    totalcosttickets += ticketcost

    if retour == 1:
      print '%10s%10s %6s %5s $%3s %6s %5s %4s' % (name, general.citynames[origin], \
        outbound.ID,general.minutesToFrmTime(outbound.arrivalTime),ticketcost,\
        returnf.ID,general.minutesToFrmTime(returnf.departureTime),'incl')
    else:
      print '%10s%10s %6s %5s $%3s %6s %5s $%3s' % (name, general.citynames[origin], \
        outbound.ID,general.minutesToFrmTime(outbound.arrivalTime),outbound.cost,\
        returnf.ID,general.minutesToFrmTime(returnf.departureTime),returnf.cost)

  print '\nSchedule cost: %s; Ticket costs: $%s' % (retourschedulecost(sol),totalcosttickets)
    
def schedulecost(sol):
    # Calculates a score based on the total time people have to wait
    # on each other on the airport (after they arrived there, but not everyone
    # has), have to wait for their flight (when they're getting back home),
    # and the total cost of the tickets.
    
    totalcosttickets = 0
    latestarrival = 0
    earliestdep = 24*60
    for i in range(len(sol)/2):
        origin = general.people[i][1]
        outbound = flights[(origin,general.destinationCity)][int(sol[i*2])]  # flight used to arrive at LGA
        returnf = flights[(general.destinationCity,origin)][int(sol[i*2+1])]  # flight to get back home
        
        ticketcost = outbound.cost + returnf.cost
        totalcosttickets += ticketcost

        if outbound.arrivalTime > latestarrival:
            latestarrival = outbound.arrivalTime
        if returnf.departureTime < earliestdep:
            earliestdep = returnf.departureTime

    minuteswaited = 0
    for i in range(len(sol)/2):
        origin = general.people[i][1]
        outbound = flights[(origin,general.destinationCity)][int(sol[i*2])]  # flight used to arrive at LGA
        returnf = flights[(general.destinationCity,origin)][int(sol[i*2+1])]  # flight to get back home

        minuteswaited += latestarrival - outbound.arrivalTime
        minuteswaited += returnf.departureTime - earliestdep

    return minuteswaited/2 + totalcosttickets
    
def retourschedulecost(sol):
    # Calculates a score based on the total time people have to wait
    # on each other on the airport (after they arrived there, but not everyone
    # has), have to wait for their flight (when they're getting back home),
    # and the total cost of the tickets.
    
    totalcosttickets = 0
    latestarrival = 0
    earliestdep = 24*60
    for i in range(len(sol)/2):
        origin = general.people[i][1]
        outbound = flights[(origin,general.destinationCity)][int(sol[i*2])]  # flight used to arrive at LGA
        returnf = flights[(general.destinationCity,origin)][int(sol[i*2+1])]  # flight to get back home
        
        ticketcost = outbound.cost + returnf.cost
        
        for retourticket in retourtickets:
          if outbound.ID == retourticket.flight1 and returnf.ID == retourticket.flight2:
            ticketcost = retourticket.cost
        
        totalcosttickets += ticketcost

        if outbound.arrivalTime > latestarrival:
            latestarrival = outbound.arrivalTime
        if returnf.departureTime < earliestdep:
            earliestdep = returnf.departureTime

    minuteswaited = 0
    for i in range(len(sol)/2):
        origin = general.people[i][1]

        outbound = flights[(origin,general.destinationCity)][int(sol[i*2])]  # flight used to arrive at LGA
        returnf = flights[(general.destinationCity,origin)][int(sol[i*2+1])]  # flight to get back home

        minuteswaited += latestarrival - outbound.arrivalTime
        minuteswaited += returnf.departureTime - earliestdep

    return minuteswaited/2 + totalcosttickets

# Use a genetic algorithm to try random solutions and
# evolve the best schedule
def bestschedule():
  bestschedule = general.geneticoptimize(domain,schedulecost)
  printschedule(bestschedule)
  
# same but now using retour
def bestretourschedule():
  bestschedule = general.geneticoptimize(domain,retourschedulecost)
  printschedule(bestschedule)
  
# same but now using different genetic optimizer
def bestretourschedule2():
  bestschedule = general.geneticoptimize2(domain,retourschedulecost)
  printschedule(bestschedule)

# same but now using different genetic optimizer
def bruteforce():
  bestschedule = general.bruteforce(retourschedulecost)
  printschedule(bestschedule)


#used for testing
#scores = []
#for i in range(100):
#  scores.append(retourschedulecost(general.geneticoptimize2(domain,retourschedulecost)))
#print '      n:   min:   max:    avg:'
#print '%7s%7s%7s%9s' % (len(scores),min(scores),max(scores),float(sum(scores))/len(scores))

