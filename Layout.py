from gurobipy import *

#SETS
# I         Set of temporary facility (TF) locations
# J         Set of permanent facility (PF) locations
# K         Set of service coverage windows
# T         Set of PF sizes
# S         Set of scenarios
# L         Set of items
# J[i][k]       Set of PFs that can service TF i within SCW k  ( Jik⊆ Jik', for k<k' )
# M[s]	    Set of demand points under disaster scenario s
# I[m] in I	Set of TFs that are close enough to serve demand point m


#PARAMETERS
# d[m][l][s]	Demand of point m in Ms for item l in L under scenario s in S 
# r[k][l]	    Proportion of demand for item l to be satisfied within service coverage window k in K
# K[t][p]	    Capacity of a PF of size t in T
# K[i][T]	    Capacity of the TF (size T) at location i in I(m) 
# u[l]	    Capacity consumption of item l
# h[l]	    Acquisition, expected inventory holding and wastage costs cost of item l 
# c[j][t]	    Fixed cost of PF at location j of size t
# delta[i][m]	Distance between TF i in I and demand point m in M(s)


m = Model("Attempt1")


#VARIABLES
# 1, if demand point m in assigned to TF i for scenario s
X = {(i,m,s): m.addVar(vtype=GRB.BINARY) for s in S for i in I for m in M[s]}

# 1, if TF i is opened under scenario s
Y = {(i,s): m.addVar(vtype=GRB.BINARY) for s in S for i in I}

# amount of item l transported from PJ j to TF i under scenario s
F = {(j,i,l,s): m.addVar() for s in S for j in J for i in I for l in L}

# 1, if PF j of size t is opened
Z = {(j,t): m.addVar(vtype=GRB.BINARY) for j in J for t in T}

# prepositioned invenctory amount of item l at PF j
I = {(j,l): m.addVar() for j in J for l in L}


#OBJECTIVE
m.setObjective(
    quicksum(c[j][t]*Z[j,t] for j in J for t in T) + \
    quicksum(h[l]*I[j,l] for j in J for l in L),
    GRB.MINIMIZE)

# CONSTRAINTS
### NAME = m.addConstr()
### NAME = {s:
#        m.addConstr()
#        for s in S}

# 2
TWO = {(s,m):
       m.addConstr(quicksum(X[s,i,m] for i in I[m]) == 1)
           for s in S for m in M[s]}

# 3
THREE = {(i,m,s):
       m.addConstr(X[i,m,s] <= Y[i,s])
       for i in I for m in M[s] for s in S}

# 4
FOUR = {(i,s):
       m.addConstr(quicksum(u[l]*quicksum(d[m][l][s]*X[i,m,s] for m in M[s]) for l in L) <= K[i][T]*Y[i,s])
           i in I for s in S}

# 5 
FIVE = 

# 6
SIX = 

# 7
SEVEN = 

# 8
EIGHT = 

# 9
NINE = 

# 10
TEN = 

# 11
ELEVEN = 

# 12
TWELVE = 

# 13
THIRTEEN = 

# 14
FOURTEEN = 

