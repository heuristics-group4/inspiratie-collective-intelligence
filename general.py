import time
import urllib2
import xml.dom.minidom
import sys
import os
import random
import fileinput
import math

people = [('Seymour','BOS'),
          ('Franny','DAL'),
          ('Zooey','CAK'),
          ('Walt','MIA'),
          ('Buddy','ORD'),
          ('Les','OMA')]

citynames = {'BOS':'Boston',
             'DAL':'Dallas',
             'CAK':'Akron',
             'MIA':'Miami',
             'ORD':'Chicago',
             'OMA':'Omaha'}

destinationCity='LGA'	# Laguardia

def minutesToFrmTime(minutes):
    return time.strftime("%H:%M",time.strptime(str(minutes/60)+" "+str(minutes%60),"%H %M"))

class SingleTicket:
    def __init__(self, ID, sourceCity, destCity, departureTime, arrivalTime, cost):
        self.ID = ID
        self.sourceCity = sourceCity
        self.destCity = destCity
        self.departureTime = departureTime
        self.arrivalTime = arrivalTime
        self.cost = cost
    def toString(self):
        return "(ID "+self.ID+",From "+self.sourceCity+",To "+self.destCity+",Dep "+minutesToFrmTime(self.departureTime)+\
                ",Arr "+minutesToFrmTime(self.arrivalTime)+",Cost "+str(self.cost)+")"

class RetourTicket:
    def __init__(self, flight1, flight2, cost):
        self.flight1 = flight1
        self.flight2 = flight2
        self.cost = cost
    def toString(self):
        return "(Flight1 "+self.flight1+",Flight2 "+self.flight2+",Cost "+str(self.cost)+")"

def loadSingleTickets(filename):
    def timeToMinutes(formattedTime):
        s = formattedTime.split(":")
        return int(s[0])*60+int(s[1])
    tickets = []
    for line in fileinput.input(filename):
        spline = line.strip().split()
        if len(spline):
            ID,sourceCity,destCity,departureTime,arrivalTime,cost = spline
            ticket = SingleTicket(ID,sourceCity,destCity,\
                                  timeToMinutes(departureTime),timeToMinutes(arrivalTime),int(cost[1:]))
            tickets.append(ticket)
    return tickets
    
def loadRetourTickets(filename):
    def timeToMinutes(formattedTime):
        s = formattedTime.split(":")
        return int(s[0])*60+int(s[1])
    retours = []
    for line in fileinput.input(filename):
        spline = line.strip().split()
        if len(spline):
            flight1,flight2,cost = spline
            
            retour = RetourTicket(flight1,flight2,int(cost[1:]))
            retours.append(retour)
    return retours    

def randomoptimize(domain,costf):
  best=999999999
  bestr=None
  for i in range(0,1000):
    # Create a random solution
    r=[float(random.randint(domain[i][0],domain[i][1])) 
       for i in range(len(domain))]
    
    # Get the cost
    cost=costf(r)
    
    # Compare it to the best one so far
    if cost<best:
      best=cost
      bestr=r 
  return bestr #changed from 'return r'

def hillclimb(domain,costf):
  # Create a random solution
  sol=[random.randint(domain[i][0],domain[i][1])
      for i in range(len(domain))]
  # Main loop
  while 1:
    # Create list of neighboring solutions
    neighbors=[]
    
    for j in range(len(domain)):
      # One away in each direction
      if sol[j]>domain[j][0]:
        neighbors.append(sol[0:j]+[sol[j]-1]+sol[j+1:]) #swapped this and
      if sol[j]<domain[j][1]:
        neighbors.append(sol[0:j]+[sol[j]+1]+sol[j+1:]) # this line

    print sol

    # See what the best solution amongst the neighbors is
    current=costf(sol)
    best=current
    for j in range(len(neighbors)):
      cost=costf(neighbors[j])
      if cost<best:
        best=cost
        sol=neighbors[j]

    # If there's no improvement, then we've reached the top
    if best==current:
      break
  return sol

def annealingoptimize(domain,costf,T=10000.0,cool=0.95,step=1):
  # Initialize the values randomly
  vec=[float(random.randint(domain[i][0],domain[i][1])) 
       for i in range(len(domain))]
  
  while T>0.1:
    # Choose one of the indices
    i=random.randint(0,len(domain)-1)

    # Choose a direction to change it
    dir=random.randint(-step,step)

    # Create a new list with one of the values changed
    vecb=vec[:]
    vecb[i]+=dir
    if vecb[i]<domain[i][0]: vecb[i]=domain[i][0]
    elif vecb[i]>domain[i][1]: vecb[i]=domain[i][1]

    # Calculate the current cost and the new cost
    ea=costf(vec)
    eb=costf(vecb)
    p=pow(math.e,(-eb-ea)/T)

    # Is it better, or does it make the probability
    # cutoff?
    if (eb<ea or random.random()<p):
      vec=vecb      

    # Decrease the temperature
    T=T*cool
  return vec

def geneticoptimize(domain,costf,popsize=100,step=1,
                    mutprob=0.2,elite=0.25,maxiter=100):
  # Mutation Operation
  def mutate(vec):
    i=random.randint(0,len(domain)-1)
    decrease_valid = vec[i] - step >= domain[i][0]
    increase_valid = vec[i] + step <= domain[i][1]
    decrease = vec[0:i]+[vec[i]-step]+vec[i+1:]
    increase = vec[0:i]+[vec[i]+step]+vec[i+1:]
    if random.random()<0.5:
      if increase_valid: return increase
      elif decrease_valid: return decrease
      else: return vec
    else:
      if decrease_valid: return decrease
      elif increase_valid: return increase
      else: return vec
  
  # Crossover Operation
  def crossover(r1,r2):
    i=random.randint(1,len(domain)-1) #was )-2)
    return r1[0:i]+r2[i:]

  # Build the initial population
  pop=[]
  for i in range(popsize):
    vec=[random.randint(domain[i][0],domain[i][1]) 
         for i in range(len(domain))]
    pop.append(vec)
  
  # How many winners from each generation?
  topelite=int(elite*popsize)
  
  # Main loop 
  for i in range(maxiter):
    scores=[(costf(v),v) for v in pop]
    scores.sort()
    ranked=[v for (s,v) in scores]
    
    # Start with the pure winners
    pop=ranked[0:topelite]
    
    # Add mutated and bred forms of the winners
    while len(pop)<popsize:
      if random.random()<mutprob:

        # Mutation
        c=random.randint(0,topelite)
        pop.append(mutate(ranked[c]))
      else:
      
        # Crossover
        c1=random.randint(0,topelite)
        c2=random.randint(0,topelite)
        pop.append(crossover(ranked[c1],ranked[c2]))
    
    # Print current best score
    #print scores[0][0]
    
  return scores[0][1]
  
def geneticoptimize2(domain,costf,popsize=100,step=1,

                    mutprob=0.2,elite=0.25,maxiter=100):
  # Mutation Operation
  def mutate(vec):
    i=random.randint(0,len(domain)-1)
    decrease_valid = vec[i] - step >= domain[i][0]
    increase_valid = vec[i] + step <= domain[i][1]
    decrease = vec[0:i]+[vec[i]-step]+vec[i+1:]
    increase = vec[0:i]+[vec[i]+step]+vec[i+1:]
    if random.random()<0.5:
      if increase_valid: return increase
      elif decrease_valid: return decrease
      else: return vec
    else:
      if decrease_valid: return decrease
      elif increase_valid: return increase
      else: return vec
  
  # Crossover Operation
  def crossover(r1,r2):
    i=random.randint(1,len(domain)-1) #was )-2)
    return r1[0:i]+r2[i:]

  # Build the initial population
  pop=[]
  for i in range(popsize):
    vec=[random.randint(domain[i][0],domain[i][1]) 
         for i in range(len(domain))]
    pop.append(vec)
  
  # How many winners from each generation?
  topelite=int(elite*popsize)
  
  # Main loop 
  for i in range(maxiter):
    scores=[(costf(v),v) for v in pop]
    scores.sort()
    ranked=[v for (s,v) in scores]
    
    # Start with the pure winners
    pop=ranked[0:topelite]
    
    # Add mutated and bred forms of the winners
    while len(pop)<popsize:
      if random.random()<(mutprob*2/((i+maxiter/5)/(maxiter/5))):

        # Mutation
        c=random.randint(0,topelite)
        pop.append(mutate(ranked[c]))
      else:
      
        # Crossover
        c1=random.randint(0,topelite)
        c2=random.randint(0,topelite)
        pop.append(crossover(ranked[c1],ranked[c2]))
    
    # Print current best score
    #print scores[0][0]
    
  return scores[0][1]

def bruteforce(costf):
  #I hardcoded the range used in each step instead of using domain, because it just might save a few minutes in total.
  best=999999999
  bestresult=None
  for i in range(7):
    for j in range(7):
      for k in range(9):
        for l in range(9):
          for m in range(14):
            for n in range(14):
              for o in range(10):
                for p in range(10):
                  print i,j,k,l,m,n,o,p #to have an idea how long this will take
                  for q in range(16):
                    for r in range(16):
                      for s in range(14):
                        for t in range(14):
                          result = [i,j,k,l,m,n,o,p,q,r,s,t]
                      
                          # Get the cost
                          cost=costf(result)
    
                          # Compare it to the best one so far
                          if cost<best:
                            best=cost
                            bestresult=result 
  return bestresult


