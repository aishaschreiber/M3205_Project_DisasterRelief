from gurobipy import *
import access_data_edit
import sys
import os

### ----- INSTANCE ? ----- ###
GET = access_data_edit.get_data_sets()
#SETS   
# Set of temporary facility locations (aka 'I' in the paper)
TF = GET['TF']
# Set of permanent facility (PF) locations J (aka 'J' in the paper)
PF = GET['PF']
# Set of service coverage windows
K = GET['K']
# Set of PF sizes
T = GET['T']
# Set of scenarios
S = GET['S']
# Set of items
L = GET['L']
# Set of PFs that can service TF i within SCW k  ( PFik ⊆ PFik', for k<k' )
PF_ik = GET['PF_ik']

# Set of demand points under disaster scenario s
M_s = GET['M_s']
# Set of TFs that are close enough to serve demand point m
TF_m = GET['TF_m']

#PARAMETERS
# Demand of point m in Ms for item l in L under scenario s in S 
D_sml = GET['D_sml']
# Proportion of demand for item l to be satisfied within service coverage window k in K
R_kl = GET['R_kl']
# Capacity of a PF of size t in T
KP_t = GET['KP_t']
# Capacity of the TF (size T) at location i in TF(m) 
KT_i = GET['KT_i']
# Capacity consumption of item l
u_l = GET['u_l']
# Acquisition, expected inventory holding and wastage costs cost of item l 
h_l = GET['h_l']
# Fixed cost of PF at location j of size t
c_jt = GET['c_jt']
# Distance between TF i and demand point m in M_s(s)
delta_im = GET['delta_im']

# C_s[s]
# C_s = GET['C_s']

##################################
##### Bender's Decomposition #####
##################################
#Master variable: Z, I, Y
#Sub variables: 
    #Clustering X, subject to Y*
    #Flow Distribution:F, subject to X*, Y*, I*

##########################
##### MASTER PROBLEM #####
##########################
LIPMP = Model("Master Problem")

# Master Variables
# 1, if TF i is opened under scenario s
Y = {(i,s): LIPMP.addVar(vtype=GRB.BINARY) for s in S for i in TF}
# 1, if PF j of size t is opened
Z = {(j,t): LIPMP.addVar(vtype=GRB.BINARY) for j in PF for t in T}
# prepositioned invenctory amount of item l at PF j
I = {(j,l): LIPMP.addVar() for j in PF for l in L}

# Master Objective
LIPMP.setObjective(quicksum(c_jt[(j,t)]*Z[j,t] for j in PF for t in T) + \
                   quicksum(h_l[l]*I[j,l] for j in PF for l in L),
                   GRB.MINIMIZE)

# Master Constraints

# capacity consumption of item l * amount of prepositioned inventory is <= capacity of TF
SEVEN = {j:
         LIPMP.addConstr(quicksum(u_l[l]*I[j,l] for l in L) <= quicksum(KP_t[t]*Z[j,t] for t in T))
         for j in PF}
    

   
# force the model to open at most one size of PF at each candidate location
NINE = {j:
        LIPMP.addConstr(quicksum(Z[j,t] for t in T)<= 1)
        for j in PF}

# ELEVEN: Y is a binary variable
# THIRTEEN: Z is a binary variable

FIFTEEN = {(s,m):
           LIPMP.addConstr(quicksum(Y[i,s] for i in TF_m[m])>=1 ) 
           for s in S for m in M_s[s]}

#Constraint 16
SIXTEEN  = {(s,i):
            LIPMP.addConstr(quicksum(Z[j,t] for j in PF_ik[(i,1)] for t in T)>= Y[i,s])
            for s in S for i in TF}
    

SEVENTEEN = {(s,l):
                   LIPMP.addConstr(quicksum(I[j,l] for j in PF)
                                   >=quicksum(D_sml[(s,m,l)]
                    for m in M_s[s] if (s,m,l) in D_sml))
                                   for s in S for l in L}

LIPMP.optimize()



#########################################
##### CSP SUB-PROBLEM: Clustering #####
#########################################
#Define P1,P2,Sd,Im,Ms
#CSP is separable over scenarios, solve for clustering 

CSP = Model("Clustering Subproblem") 

s = 0
# CSP Variables
X = {(i,m): CSP.addVar(vtype=GRB.BINARY) for i in TF for m in M_s[s]}

#No Objective, Just feasible Solution

EIGHTEEN = {m:
            CSP.addConstr(quicksum(X[i,m] for i in TF_m[m]) ==1)
            for m in M_s[s]} 

NINETEEN = {(m,i):
            CSP.addConstr(X[i,m] <= Y[i,s].x) 
            for m in M_s[s] for i in TF_m[m]}

TWENTY = {i:
          CSP.addConstr(quicksum(u_l[l]*D_sml[(s,m,l)]*X[i,m] for l in L for m in M_s[s]) \
                        <= KT_i[i] * Y[i,s].x) 
            for i in TF}

# CSP.optimize()

##################################
##### Reduced CSP SUB-PROBLEM ####
##################################
#It is equvalent to CSP after fixing the values of the X variables for which a unique closest TF exist.

######## NEW SETS ########
# Initialize dictionaries for Md and TFd
Md_s = {}
TFd_sm = {}

# For each scenario s in S
for s in S:
    multiples_Md = set()  # Use a set to store demand points with multiple TFs for Md
    multiples_TFd = {}    # Use a dictionary to store demand points with multiple TFs for TFd
    # For each demand point m in M_s[s]
    for m in M_s[s]:
        # Find the closest distance
        closest_distance = float('inf')
        closest_TFs = []
        # For each TF i in TF_m[m]
        for i in TF_m[m]:
            distance = delta_im[(i, m)]
            if distance < closest_distance:
                closest_distance = distance
                closest_TFs = [i]
            elif distance == closest_distance:
                closest_TFs.append(i)
        # Check if there are multiple TFs at equal distance
        if len(closest_TFs) > 1:
            multiples_Md.add(m)              # Add the demand point to Md
            multiples_TFd[m] = closest_TFs   # Add the demand point to TFd
    Md_s[s] = multiples_Md
    TFd_sm[s] = multiples_TFd

# Md contains the set of demand points that have multiple TFs of equal distance in each scenario
# TFd contains the dictionary of demand points with multiple TFs of equal distance for each scenario












# Kd_si # The remaining capacity of TF i after assigning the demand points to this TF
# Need to know which demands points were assigned to which TF
# for example Kd_si = {1: 45, 2, 62} where 1 and 2 are TFs and 46 62 are there respective remaining capacities

# Dictionary of TFs and their remaining capacities (given that the previous demand points are assigned)
Kd_si = {}
for s in S:
    for m in M_s[s]:
        for i in TFd_sm:
            #if demand point m is assigned to TF i
            if X[i,m].x > 0.9:
                #then sum up the demand at that TF
                demand_at_TF[i] = sum(D_sml[(s,m,l)] for l in L)
                #find remaining demand
                remaining_demand = []
                amount = KT_i[i] - demand_at_TF[i]
                remaining_demand.append(amount)
            # Add to dictionary
            KD_si[(s,i)] = remaining_demand
    

# ReducedCSP = Model("CheckForAlternative")

# X = {(i,m): ReducedCSP.addVar(vtype=GRB.BINARY) for i in TF for m in M_s[s]}

# #No objective 

# #Constraints
# Constraint24 = {m:
#         ReducedCSP.addConstr(quicksum(X[i,m] for i in TFd_sm) == 1) for m in Md_s[s]}

# Constraint25 = {i:
#             ReducedCSP.addConstr(quicksum(u_l[l]*D_sml[(s,m,l)]*X[i,m] for m in Md_s[s] for l in L) 
#             <= Kd_si[s][i]) 
#             for i in TFd_sm}

# # ReducedCSP.optimize()


# ##########################
# #### FDSP is seperable over scenarios and item types 
# ##########################
# FDSP = Model("Flow Distribution Sub-Problem")

# #Define a D_Bar
# D_bar = {(s,i,l): quicksum(D_sml[(s,m,l)]*X[i,s,m].x for m in M_s[s])
#          for s in S for i in TF for l in L}

# #Variables
# # amount of item l transported from PJ j to TF i under scenario s
# F = {(j,i,l,s): FDSP.addVar() for s in S for j in PF for i in TF for l in L}

# #No Objective

# #Constraint29
# FlowGreaterThanSCW = {(i,k):
#                      FDSP.addConstr(quicksum(F[j,i,l,s] for j in PF[k,i]) >= (r[k,l] * D_bar[(s,i,l)]))
#                      for i in TF for k in K}

# #Constraint30
# FlowLessThanInventory = {j:
#                          FDSP.addConstr(quicksum(F[j,i,l,s] for i in TF)<= quicksum(I[j,l].x for l in L))
#     for j in PF}

# #FDSP.optimize()

# ############################
# #If a feasible solution of the LIPMP is also feasible for CSP and FDSP sub-problems, it is also feasible for the original CLFDIP Problem 
# ############################
    
# # #Benders Loop 
# # for k in range(1):
# #     LIPMP.optimize()
# #     CalcObj = 0
# #     for s in S:########
# #         for i in P[1]: ###########
# #             if XXXXXX: ##CSP Infeasible
# #                 LIPMP.addConstr(quicksum(Y[s,p] for p in P2)>= Y[s,i] for s in Sd for i in P1[s])
# #                     if XXXXX ##FDSP infeasible 
# #                         LIPMP.addConstr(quicksum(FlowLessThanInventory[j].pi * I[j,l] for j in PF) +\ 
# #                                         quicksum(FlowGreaterThanSW[i,k].pi * r[k,l]*D[i,l] * Y[s,i] for i in TF for k in K) <=0)
# #                         #####Should be \theta[r,j], but how would represent the extreme value here
# # ###############################

# #Define S_d P1 P2 for ReducedCSP
# S_d #Set of scenarios which infeasible clusters are found 

# P1 #Set of TF whose capacity is violated under scenario s in S_d 
# P2 #Set of previously closed TF locations which are closer to at least one demand point assigned to TF i in scenario S in S_d 

# #This loop is based on the Algorithm Flow Chart 
# for kk in range(10):
#     LIPMP.optimize()
#     CutsAdded = 0 
#     for s in S:
        
        
        
#         # define subproblem here
        
        
        
        
#         CSP.optimize()
        
        
        
        
#         if CSP.status == GRB.INFEASIBLE:
            
#             # Make the set
            
            
            
#             # Define reduced here
            
            
#             ReducedCSP.optimize()
#             if ReducedCSP.status == GRB.INFEASIBLE:
#                 #LIPMP.addConstr(quicksum(Y[p,s] for p in P2)>= Y[i,s] for s in S_d for i in P1[s]) #LBBD Cut 
#                 CutsAdded +=1
                
#             else:
                
#                 # third ...
#                 for l in L:
#                     FDSP.optimize()
#                     if FDSP.status == GRB.INFEASIBLE:
#                         #LIPMP.addConstr() ## Duality cut (UP)
#                         CutsAdded +=1
#     if CutsAdded == 0:
#         break
    




