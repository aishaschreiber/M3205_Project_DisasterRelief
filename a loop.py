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

Md_s = {}
TFd_sm = {}
TFu_sm = {}

# For each scenario s in S
for s in S:
    multiples_Md = set()  # Use a set to store demand points with multiple TFs for Md
    multiples_TFd = {}    # Use a dictionary to store demand points with multiple TFs for TFd
    Unique_TFd = {}
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
        else:
            Unique_TFd[m] = closest_TFs
    Md_s[s] = multiples_Md
    TFd_sm[s] = multiples_TFd
    TFu_sm[s] = Unique_TFd
    
    
Kd = {} # where Kd is the remaining capacity of Tf i

#Calculate the initial capacity at a TF
for i in TF:
    Kd[i] = KT_i[i] 
# Calculate the demand at the TF according to if the demand point m is assigned there from the CSP problem
for i in TF:    
    for m in M_s[s]:
        #if X[i,m].x > 0.9:
            demand_at_m = sum(D_sml[(s,m,l)] for l in L)
# Calculate the remaining capacity at the TF
            Kd[i] -= demand_at_m

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

# FIFTEEN = {(s,m):
#             LIPMP.addConstr(quicksum(Y[i,s] for i in TF_m[m])>=1 ) 
#             for s in S for m in M_s[s]}

# #Constraint 16
# SIXTEEN  = {(s,i):
#             LIPMP.addConstr(quicksum(Z[j,t] for j in PF_ik[(i,1)] for t in T)>= Y[i,s])
#             for s in S for i in TF}
    

# SEVENTEEN = {(s,l):
#                     LIPMP.addConstr(quicksum(I[j,l] for j in PF)
#                                     >=quicksum(D_sml[(s,m,l)]
#                     for m in M_s[s] if (s,m,l) in D_sml))
#                                     for s in S for l in L}

#NO LINEAR RELAXATION NOW



##################################################################################
LIPMP.setParam('OutputFlag',0)


for kk in range(10):
    LIPMP.optimize()
    CutsAdded = 0 
    for s in S:
        print(s,", ###### we are in the loop")
        # define subproblem here
        CSP = Model("Clustering Subproblem") 
        CSP.setParam('OutputFlag',0)
        X = {(i,m): CSP.addVar(vtype=GRB.BINARY) for i in TF for m in M_s[s]}
        EIGHTEEN = {m:
            CSP.addConstr(quicksum(X[i,m] for i in TF_m[m]) ==1)
            for m in M_s[s]} 

        NINETEEN = {(m,i):
            CSP.addConstr(X[i,m] <= Y[i,s].x) 
            for m in M_s[s] for i in TF_m[m]}

        TWENTYNTY = {i:
          CSP.addConstr(quicksum(u_l[l]*D_sml[(s,m,l)]*X[i,m] for l in L for m in M_s[s]) \
                        <= KT_i[i] * Y[i,s].x) 
            for i in TF}

        CSP.optimize()
        
        
        print("#####CSP Solved")
        if CSP.status == GRB.INFEASIBLE:
            print("CSP Infeasible")
        # Make the set (Kd_si) Potential write a function with input X[i,m].x

        
        # Define reduced here
            ReducedCSP = Model("CheckForAlternative")
            ReducedCSP.setParam('OutputFlag',0)
            
            
            Xd = {(i,m): ReducedCSP.addVar(vtype=GRB.BINARY) for m in Md_s[s] for i in TFd_sm[s][m]}
            #Im thinking here for the TFd_sm, should only leave the alternative TF (Much less variable, better preformance)

            #No objective 

            #Constraints
            Constraint24 = {m:
                    ReducedCSP.addConstr(quicksum(Xd[i,m] for i in TFd_sm[s][m]) == 1) for m in Md_s[s]}

            Constraint25 = {i:
                        ReducedCSP.addConstr(quicksum(u_l[l]*D_sml[(s,m,l)]*Xd[i,m] for m in Md_s[s] for l in L) 
                        <= Kd_si[s][i]) 
                        for i in TFd_sm[s][m]}

                           
            ReducedCSP.optimize()
            
            
            print("XXXXXXXXXXXXX")
            XXXXXXXXXXXXXXXXX
            if ReducedCSP.status == GRB.INFEASIBLE:
                
                
                # Generate some new set, S_d, P1, P2
                
                
                print("ReducedCSP Infeasible")
                #LIPMP.addConstr(quicksum(Y[p,s] for p in P2)>= Y[i,s] for s in S_d for i in P1[s]) #LBBD Cut 
                CutsAdded +=1
                
            else:
                
                #Define FDSP
                
                
                
                
                
                # third ...
                for l in L:
                    FDSP.optimize()
                    if FDSP.status == GRB.INFEASIBLE:
                        #LIPMP.addConstr() ## Duality cut (UP)
                        CutsAdded +=1
    if CutsAdded == 0:
        break   
    

##Really Strange Points
#1. We have used for s in S when generating the data Md_s..., this causes an issue because the s will be passed to ReducedCSP
# which might not be the same s used in CSP
# (Im thinking write a function to generate the Md_s, TFs_sm)

#2. KeyError: (1, 2759.0), where does 2759.0 come from!! at line 195
#Probably caused by 1 
