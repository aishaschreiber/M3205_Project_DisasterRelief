from gurobipy import *
import access_data_edit

GET = access_data_edit.get_data_sets()
#SETS   
# TF = range(76+1) # Set of temporary facility locations (aka 'I' in the paper)
# TF = GET['TF']
TF = range(76+1)
# PF = range(34+1) # Set of permanent facility (PF) locations J (aka 'J' in the paper)
# PF = GET['PF']
PF = range(34+1)
# K = range(2+1) # Set of service coverage windows
# K = GET['K']
K = range(2+1)
# T = range(1+1) # Set of PF sizes
# T = GET['T']
T = range(1+1)
# S = range(1+1) # Set of scenarios
# S = GET['S']
S = range(1+1)
# L = range(2+1) # Set of items
# L = GET['L']
L = range(2+1)
# dictionary J_ik[(i,k)] Set of PFs that can service TF i within SCW k  ( PFik ⊆ PFik', for k<k' )
PF_ik = GET['PF_ik']

# dictionary M_s[s] Set of demand points under disaster scenario s
M_s = GET['M_s']
# dictionary I_m[m]: Set of TFs that are close enough to serve demand point m
TF_m = GET['TF_m']

#PARAMETERS
# dictoinary D_mls[(m,l,s)] Demand of point m in Ms for item l in L under scenario s in S 
D_sml = GET['D_mls']
# dictoinary R_lk[(l,k)] Proportion of demand for item l to be satisfied within service coverage window k in K
# R_kl = GET['R_lk']
R_kl = {(0,0): 0.33,
        (0,1): 0.5,
        (0,2): 0.2,
        (1,0): 0.66,
        (1,1): 0.8,
        (1,2): 0.5,
        (2,0): 1,
        (2,1): 1,
        (2,2): 1}
# dictoinary KP_t[t] Capacity of a PF of size t in T
KP_t = GET['KP_t']
# dictoinary KT_i[i] Capacity of the TF (size T) at location i in TF(m) 
KT_i = GET['KT_i']
# dictoinary u_l[l]Capacity consumption of item l
# u_l = GET['u_l']
u_l = {0: 0.15, 1: 0.032, 2: 2}
# dictoinary h_l[l] Acquisition, expected inventory holding and wastage costs cost of item l 
# h_l = GET['h_l']
h_l = {0: 0.1, 1: 5, 2: 2}
# dictoinary c_jt[(j,t)] Fixed cost of PF at location j of size t
c_jt = GET['c_jt']
# dictoinary delta_im[(i,m)] Distance between TF i and demand point m in M_s(s)
delta_im = GET['delta_im']

# dictoinary C_s[s]
C_s = GET['C_s']


LP = Model("Attempt1")

#VARIABLES
# 1, if demand point m in assigned to TF i for scenario s
X = {(i,s,m): LP.addVar(vtype=GRB.BINARY) for s in S for i in TF for m in M_s[s]}

# 1, if TF i is opened under scenario s
Y = {(i,s): LP.addVar(vtype=GRB.BINARY) for s in S for i in TF}

# amount of item l transported from PJ j to TF i under scenario s
F = {(j,i,l,s): LP.addVar() for s in S for j in PF for i in TF for l in L}

# 1, if PF j of size t is opened
Z = {(j,t): LP.addVar(vtype=GRB.BINARY) for j in PF for t in T}

# prepositioned invenctory amount of item l at PF j
I = {(j,l): LP.addVar() for j in PF for l in L}


#OBJECTIVE
LP.setObjective(
    quicksum(c_jt[(j,t)][0]*Z[j,t] for j in PF for t in T)+
    quicksum(h_l[l]*I[j,l] for j in PF for l in L),
    GRB.MINIMIZE)

# # CONSTRAINTS


# Each demand point assigned to one TF
TWO = {(s,m):
        LP.addConstr(quicksum(X[i,s,m] for i in TF_m[m]) == 1)
            for s in S for m in M_s[s]}

# Demand points only assigned to TFs that are open
THREE = {(i,m,s):
        LP.addConstr(X[i,s,m] <= Y[i,s])
        for i in TF for s in S for m in M_s[s]}

# TF capacity is not violated
# demand points that are opened * capacity consumption  of item l , is <= capacity of TF i 
FOUR = {(i,s):
        LP.addConstr(quicksum(u_l[l]*quicksum(u_l[l]*D_sml[(s,m,l)][0]*X[i,s,m] 
                    for m in M_s[s] if (s,m,l) in D_sml) for l in L) 
                     <= KT_i[i][0]*Y[i,s])
                    for i in TF for s in S}

# Demand points are assigned to the closest TF 
FIVE = {(i,s,m):
        LP.addConstr(quicksum(X[n,s,m] for n in TF_m[m] 
        if delta_im[(n,m)][0] <= delta_im[(i,m)][0]) >= Y[i,s])
        for s in S for m in M_s[s] for i in TF_m[m]}

# Amount of item l transported from PF to TF in scenario S, is >= proportion of demand to be satisfied in SCW k 
SIX = {(s,i,k,l):
        LP.addConstr(quicksum(F[j,i,l,s] for j in PF_ik[(i,k)])
        >= R_kl[(k,l)]*quicksum(D_sml[(s,m,l)][0]*X[i,s,m] for m in M_s[s] if (s,m,l) in D_sml))
        for s in S for i in TF for k in K for l in L}


# capacity consumption of item l * amount of prepositioned inventory is <= capacity of TF
SEVEN = {j:
          LP.addConstr(quicksum(u_l[l]*I[j,l] for l in L) <= quicksum(KP_t[t][0]*Z[j,t] for t in T))
                      for j in PF}

# the amount of items that can be shipped from a PF under each scenario is limited by the prepositioned amount
EIGHT = {(j,l,s):
          LP.addConstr(quicksum(F[j,i,l,s] for i in TF) <= I[j,l])
          for j in PF for l in L for s in S}

# force the model to open at most one size of PF at each candidate location
NINE = {j:
        LP.addConstr(quicksum(Z[j,t] for t in T) <= 1)
        for j in PF}

# # TEN: X is a binary varialbe
# # ELEVEN: Y is a binary variable
# # TWELVE: F >= 0 variable
# # THIRTEEN: Z is a binary variable
# # FOURTEEN: I >= 0 variable

#VALID INEQUALITIES

FIFTEEN = {(s,m):
           LP.addConstr(quicksum(Y[i,s] for i in TF_m[m]) >=1)
           for s in S for m in M_s[s]}
   
SIXTEEN = {(s,i):
            LP.addConstr(quicksum(Z[j,t] for j in PF for t in T) >= Y[i,s])
            for s in S for i in TF}
   
SEVENTEEN = {(s,l):
             LP.addConstr(quicksum(I[j,l] for j in PF) 
                          >= quicksum(D_sml[(s,m,l)][0]
                        for m in M_s[s] if (s,m,l) in D_sml))
            for s in S for l in L}


LP.optimize()

print('PFs that are open')
for j in PF:
    for t in T:
        if Z[j,t].x > 0.9:
            print(Z[j,t].x)

print('TFs that are open')
for i in TF:
    print([Y[i,s].x for s in S])
            
for j in PF:
    for t in T:
        if Z[j,t].x > 0.9:
            print('Item amount at PF',j, [I[j,l].x for l in L])

print('Amount we are delivering to TF in each scenario')
for i in TF:
    for j in PF:
        for t in T:
            if Z[j,t].x > 0.9:
                for s in S:
                    if Y[i,s].x > 0.9:
                        print('From',j,'To',i,[[round(F[(j,i,l,s)].x, 2) for l in L] for s in S])

print('Amount of each item at each TF in each scenario')
for s in S:
    for l in L:
        print(s,l,sum(F[(j,i,l,s)].x for i in TF for j in PF))
   
print('Demand for each scenario and each item')
for s in S:
    for l in L:
        print(s,l,sum(D_sml[(s,m,l)][0] for m in M_s[s]))


