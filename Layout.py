from gurobipy import *
import access_data_edit

GET = access_data_edit.get_data_sets()
#SETS   
# TF = range(76+1) # Set of temporary facility locations (aka 'I' in the paper)
TF = GET['TF']
# PF = range(34+1) # Set of permanent facility (PF) locations J (aka 'J' in the paper)
PF = GET['PF']
# K = range(2+1) # Set of service coverage windows
K = GET['K']
# T = range(1+1) # Set of PF sizes
T = GET['T']
# S = range(1+1) # Set of scenarios
S = GET['S']
# L = range(2+1) # Set of items
L = GET['L']
# dictionary J_ik[(i,k)] Set of PFs that can service TF i within SCW k  ( PFik ⊆ PFik', for k<k' )
PF_ik = GET['PF_ik']

# dictionary M_s[s] Set of demand points under disaster scenario s
M_s = GET['M_s']
# dictionary I_m[m]: Set of TFs that are close enough to serve demand point m
TF_m = GET['TF_m']

#PARAMETERS
# dictoinary D_mls[(m,l,s)] Demand of point m in Ms for item l in L under scenario s in S 
D_mls = GET['D_mls']
# dictoinary R_lk[(l,k)] Proportion of demand for item l to be satisfied within service coverage window k in K
R_lk = GET['R_lk']
# dictoinary KP_t[t] Capacity of a PF of size t in T
KP_t = GET['KP_t']
# dictoinary KT_i[i] Capacity of the TF (size T) at location i in TF(m) 
KT_i = GET['KT_i']
# dictoinary u_l[l]Capacity consumption of item l
u_l = GET['u_l']
# dictoinary h_l[l] Acquisition, expected inventory holding and wastage costs cost of item l 
h_l = GET['h_l']
# dictoinary c_jt[(j,t)] Fixed cost of PF at location j of size t
c_jt = GET['c_jt']
# dictoinary delta_im[(i,m)] Distance between TF i in TF and demand point m in M(s)
delta_im = GET['delta_im']

# dictoinary C_s[s]
C_s = GET['C_s']


m = Model("Attempt1")

#VARIABLES
# 1, if demand point m in assigned to TF i for scenario s
X = {(i,m,s): m.addVar(vtype=GRB.BINARY) for s in S for i in TF for m in M_s[s]}

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
    quicksum(c_jt[(j,t)][0]*Z[j,t] for j in PF for t in T)+
    quicksum(h_l[l][0]*I[j,l] for j in PF for l in L),
    GRB.MINIMIZE)

# # CONSTRAINTS


# # Each demand point assigned to one TF
# TWO = {(s,m):
#         m.addConstr(quicksum(X[s,i,m] for i in TF_m[m]) == 1)
#             for s in S for m in M_s[s]}

# # Demand points only assigned to TFs that are open
# THREE = {(i,m,s):
#         m.addConstr(X[i,m,s] <= Y[i,s])
#         for i in TF for m in M_s[s] for s in S}

# # TF capacity is not violated
# # demand points that are opened * capacity consumption  of item l , is <= capacity of TF i 
# FOUR = {(i,s):
#         m.addConstr(quicksum(u_l[l][0]*quicksum(D_mls[(m,l,s)][0]*X[i,m,s] for m in M_s[s]) for l in L) <= KT_i[i][0]*Y[i,s])
#             for i in TF for s in S}

# # Demand points are assigned to the closest TF 
# # ----??????????
# FIVE = {(i,m,s):
#         m.addConstr(quicksum(X[n,m,s] >= Y[i,s] for n in TF_m[m] and delta_im[(n,m)][0] <= delta_im[(i,m)][0]))
#         for s in S for m in M_s[s] for i in TF_m[m]}

# # Amount of item l transported from PF to TF in scenario S, is >= proportion of demand to be satisfied in SCW k 
# SIX = {(s,i,k,l):
#         m.addConstr(quicksum(F[j,i,l,s] for j in PF_ik[(i,k)]) >= R_lk[(l,k)][0]*quicksum(D_mls[(m,l,s)][0]*X[i,m,s] for m in M_s[s]))
#         for s in S for i in TF for k in K for l in L}

# capacity consumption of item l * amount of prepositioned inventory is <= capacity of TF
SEVEN = {j:
          m.addConstr(quicksum(u_l[l][0]*I[j,l] for l in L) <= quicksum(KP_t[t][0]*Z[j,t] for t in T))
                      for j in PF}

# the amount of items that can be shipped from a PF under each scenario is limited by the prepositioned amount
EIGHT = {(j,l,s):
          m.addConstr(quicksum(F[j,i,l,s] for i in TF) <= I[j,l])
          for j in PF for l in L for s in S}

# force the model to open at most one size of PF at each candidate location
NINE = {j:
        m.addConstr(quicksum(Z[j,t] for t in T) <= 1)
        for j in PF}

# # TEN: X is a binary varialbe
# # ELEVEN: Y is a binary variable
# # TWELVE: F >= 0 variable
# # THIRTEEN: Z is a binary variable
# # FOURTEEN: I >= 0 variable

m.optimize()

