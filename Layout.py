from gurobipy import *

#SETS
# TF         Set of temporary facility (TF) locations
# PF         Set of permanent facility (PF) locations
# K         Set of service coverage windows
# T         Set of PF sizes
# S         Set of scenarios
# L         Set of items
# PF[i][k]       Set of PFs that can service TF i within SCW k  ( PFik⊆ PFik', for k<k' )
# M[s]	    Set of demand points under disaster scenario s
# TF[m] in TF Set of TFs that are close enough to serve demand point m


#PARAMETERS
# d[m][l][s]	Demand of point m in Ms for item l in L under scenario s in S 
# r[k][l]	    Proportion of demand for item l to be satisfied within service coverage window k in K
# K[t][p]	    Capacity of a PF of size t in T
# K[i][T]	    Capacity of the TF (size T) at location i in TF(m) 
# u[l]	    Capacity consumption of item l
# h[l]	    Acquisition, expected inventory holding and wastage costs cost of item l 
# c[j][t]	    Fixed cost of PF at location j of size t
# delta[i][m]	Distance between TF i in TF and demand point m in M(s)


m = Model("Attempt1")


#VARIABLES
# 1, if demand point m in assigned to TF i for scenario s
X = {(i,m,s): m.addVar(vtype=GRB.BINARY) for s in S for i in TF for m in M[s]}

# 1, if TF i is opened under scenario s
Y = {(i,s): m.addVar(vtype=GRB.BINARY) for s in S for i in TF}

# amount of item l transported from PJ j to TF i under scenario s
F = {(j,i,l,s): m.addVar() for s in S for j in PF for i in TF for l in L}

# 1, if PF j of size t is opened
Z = {(j,t): m.addVar(vtype=GRB.BINARY) for j in PF for t in T}

# prepositioned invenctory amount of item l at PF j
I = {(j,l): m.addVar() for j in PF for l in L}


#OBJECTIVE
m.setObjective(
    quicksum(c[j][t]*Z[j,t] for j in PF for t in T) + \
    quicksum(h[l]*I[j,l] for j in PF for l in L),
    GRB.MINIMIZE)

# CONSTRAINTS


# Each demand point assigned to one TF
TWO = {(s,m):
       m.addConstr(quicksum(X[s,i,m] for i in TF[m]) == 1)
           for s in S for m in M[s]}

# Demand points only assigned to TFs that are open
THREE = {(i,m,s):
       m.addConstr(X[i,m,s] <= Y[i,s])
       for i in TF for m in M[s] for s in S}

# TF capacity is not violated
# demand points that are opened * capacity consumption  of item l , is <= capacity of TF i 
FOUR = {(i,s):
       m.addConstr(quicksum(u[l]*quicksum(d[m][l][s]*X[i,m,s] for m in M[s]) for l in L) <= K[i][T]*Y[i,s])
           for i in TF for s in S}

# Demand points are assigned to the closest TF 
# ----??????????
FIVE = {(i,m,s):
        m.addConstr(quicksum(X[n,m,s] >= Y[i,s] for n in TF[m] and delta[n][m] <= delta[i][m]))
        for s in S for m in M[s] for i in TF[m]}

# Amount of item l transported from PF to TF in scenario S, is >= proportion of demand to be satisfied in SCW k 
SIX = {(s,i,k,l):
       m.addConstr(quicksum(F[j,i,l,s] for j in PF[i][k]) >= r[k][l]*quicksum(d[m][l][s]*X[i,m,s] for m in M[s]))
       for s in S for i in TF for k in K for l in L}

# capacity consumption of item l * amount of prepositioned inventory is <= capacity of TF
SEVEN = {j:
         m.addConstr(quicksum(u[l]*I[j,l] for l in L) <= quicksum(K[t][p]*Z[j,t] for t in T))
                     for j in PF}

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

