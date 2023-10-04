# -*- coding: utf-8 -*-
"""
Created on Thu Sep  7 09:11:57 2023

@author: maggi
"""

from gurobipy import *

import sys
import os

# Add a new directory to the Python path
new_directory = 'D:/UQ/2023 Semester2/MATH3205/Project/Program/M3205_Project_DisasterRelief-main/M3205_Project_DisasterRelief-main'

os.chdir(new_directory)

# Verify the change by printing the current working directory
current_directory = os.getcwd()
print("Current working directory:", current_directory)

import access_data_edit_2

### ----- INSTANCE 2 ----- ###
GET = access_data_edit_2.get_data_sets()
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
D_sml = GET['D_sml']
# dictoinary R_lk[(l,k)] Proportion of demand for item l to be satisfied within service coverage window k in K
R_kl = GET['R_kl']
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
# dictoinary delta_im[(i,m)] Distance between TF i and demand point m in M_s(s)
delta_im = GET['delta_im']

# dictoinary C_s[s]
# C_s = GET['C_s']

##### Bender's Decomposition 
#Master variable: Z, I, Y

#Sub variables: 
    #Clustering X, subject to Y*
    #Flow Distribution:F, subject to X*, Y*, I*


#Disaster Relief Benders 

###Master Problem
LIPMP = Model("Master Problem")

#Master Variables
# 1, if TF i is opened under scenario s
Y = {(i,s): LIPMP.addVar(vtype=GRB.BINARY) for s in S for i in TF}
# 1, if PF j of size t is opened
Z = {(j,t): LIPMP.addVar(vtype=GRB.BINARY) for j in PF for t in T}

# prepositioned invenctory amount of item l at PF j
I = {(j,l): LIPMP.addVar() for j in PF for l in L}


LIPMP.setObjective(quicksum(c_jt[(j,t)]*Z[j,t] for j in PF for t in T) + \
                   quicksum(h_l[l]*I[j,l] for j in PF for l in L),
                   GRB.MINIMIZE)

SEVEN = {j:
             LIPMP.addConstr(quicksum(u_l[l]*I[j,l] for l in L) <= quicksum(KP_t[t]*Z[j,t] for t in T))
                         for j in PF}
    
NINE = {j:
        LIPMP.addConstr(quicksum(Z[j,t] for t in T)<= 1)
        for j in PF}

#Constraint15
OpenLeastOneTF = {(s,m):
    LIPMP.addConstr(quicksum(Y[i,s] for i in TF_m[m])>=1 ) 
    for s in S for m in M_s[s]}
    
#Constraint16
EnoughCapacityFromPF  = {(s,i):
                         LIPMP.addConstr(quicksum(Z[j,t] for j in PF_ik[(i,1)] for t in T)>= Y[i,s])
                                         for s in S for i in TF}
#####Define this J1
######In Originial Formulation

#Constraint 17
EnoughInventory = {(s,l):
                   LIPMP.addConstr(quicksum(I[j,l] for j in PF)>=quicksum(D_sml[(s,m,l)]
                    for m in M_s[s] if (s,m,l) in D_sml))
                                   for s in S for l in L}
LIPMP.optimize()

#XXXX

#Subproblem1: Clustering

#Define P1,P2,Sd,Im,Ms

#######################################
#CSP is separable over scenarios, solve for clustering 
#######################################

CSP = Model("Clustering Subproblem") #####

#Variables
X = {(i,m,s): CSP.addVar(vtype=GRB.BINARY) for s in S for i in TF for m in M_s[s]}

#No Objective, Just feasible Solution

AssignEachDemand = {m:
                    CSP.addConstr(quicksum(X[i,m,s] for i in TF_m[m]) ==1)
                    for m in M_s[s]} #Here I should say for s in S too but X really should not depend on s

AssignDemandIfTFOpen = {(m,i):
                        CSP.addConstr(X[s,i,m] <= Y[i,s].x) 
                        for m in M_s[s] for i in TF_m}

DemandLessThanCapacity = {i:
                          CSP.addConstr(quicksum(D_sml[(s,m,l)]*X[i,m,s] for l in L for m in M_s[s])<=\
                                        K[t][p] * Y[i,s].x)
                              for i in TF_m[m]}
#CSP.optimize()

###########################
#ReducedCSP: If CSP is infeasible, check some alternatives 
#It is equvalent to CSP after fixing the values of the X variables for which a unique closest TF exist.
###########################

#Problems here: define 
M_s_d #the Set of demand points having alternative closest avaliable TFs 
M_s_d = {}

# for s in S:
#     for m in M_s:
#         min_distance = float('inf')  # Initialize minimum distance to positive infinity
#         closest_tfs = set()  # Initialize an empty set for closest TFs
        
#         for tf in TF_m:
#             # Calculate the distance between demand point m and TF tf using your distance calculation method
#             distance = delta_im[tf,m]
            
#             if distance < min_distance:
#                 min_distance = distance
#                 closest_tfs = {tf}  # Reset the set with a single closest TF
#             elif distance == min_distance:
#                 closest_tfs.add(tf)  # Add TF to the set if it's equally close

#         M_s_d[m][s] = closest_tfs  # Assign the set of closest TFs to demand point m in M_s_d

K_d #The remaining capacity of TF_i after assigning the demand points that have unique closest TF 
#Need access to the assigned variables

TF_m_d #The set of equidistant TFs for a demand point m in M_s_d

ReducedCSP = Model("CheckForAlternative")

X = {(i,m,s): ReducedCSP.addVar(vtype=GRB.BINARY) for s in S for i in TF for m in M_s[s]}

#No objective 

#Constraints
Constraint24 = {m:
        ReducedCSP.addConstr(quicksum(X[i,m,s] for i in TF_m_d) == 1) for m in M_s_d[s]}

Constraint25 = {i:
            ReducedCSP.addConstr(quicksum(u_l[l]*quicksum(D_sml[(s,m,l)]*X[i,m,s] for m in M_s_d[s]) for l in L) <= K_d[s][i]) 
            for i in TF_m_d}

#ReducedCSP.optimize()


##########################
#FDSP is seperable over scenarios and item types 
##########################
FDSP = Model("Flow Distribution Sub-Problem")

#Define a D_Bar
D_bar = {(s,i,l): quicksum(D_sml[(s,m,l)]*X[i,s,m].x for m in M_s[s])
         for s in S for i in TF for l in L}

#Variables
# amount of item l transported from PJ j to TF i under scenario s
F = {(j,i,l,s): FDSP.addVar() for s in S for j in PF for i in TF for l in L}

#No Objective

#Constraint29
FlowGreaterThanSCW = {(i,k):
                     FDSP.addConstr(quicksum(F[j,i,l,s] for j in PF[k,i]) >= (r[k,l] * D_bar[(s,i,l)]))
                     for i in TF for k in K}

#Constraint30
FlowLessThanInventory = {j:
                         FDSP.addConstr(quicksum(F[j,i,l,s] for i in TF)<= quicksum(I[j,l].x for l in L))
    for j in PF}

#FDSP.optimize()

############################
#If a feasible solution of the LIPMP is also feasible for CSP and FDSP sub-problems, it is also feasible for the original CLFDIP Problem 
############################
    
# #Benders Loop 
# for k in range(1):
#     LIPMP.optimize()
#     CalcObj = 0
#     for s in S:########
#         for i in P[1]: ###########
#             if XXXXXX: ##CSP Infeasible
#                 LIPMP.addConstr(quicksum(Y[s,p] for p in P2)>= Y[s,i] for s in Sd for i in P1[s])
#                     if XXXXX ##FDSP infeasible 
#                         LIPMP.addConstr(quicksum(FlowLessThanInventory[j].pi * I[j,l] for j in PF) +\ 
#                                         quicksum(FlowGreaterThanSW[i,k].pi * r[k,l]*D[i,l] * Y[s,i] for i in TF for k in K) <=0)
#                         #####Should be \theta[r,j], but how would represent the extreme value here
# ###############################

#Define S_d P1 P2 for ReducedCSP
S_d #Set of scenarios which infeasible clusters are found 

P1 #Set of TF whose capacity is violated under scenario s in S_d 
P2 #Set of previously closed TF locations which are closer to at least one demand point assigned to TF i in scenario S in S_d 

#This loop is based on the Algorithm Flow Chart 
for kk in range(10):
    LIPMP.optimize()
    CutsAdded = 0 
    for s in S:
        CSP.optimize()
        if CSP.status == GRB.INFEASIBLE:
            ReducedCSP.optimize()
            if ReducedCSP.status == GRB.INFEASIBLE:
                #LIPMP.addConstr(quicksum(Y[p,s] for p in P2)>= Y[i,s] for s in S_d for i in P1[s]) #LBBD Cut 
                CutsAdded +=1

        for l in L:
            FDSP.optimize()
            if FDSP.status == GRB.INFEASIBLE:
                #LIPMP.addConstr() ## Duality cut (UP)
                CutsAdded +=1
    if CutsAdded == 0:
        break
    




