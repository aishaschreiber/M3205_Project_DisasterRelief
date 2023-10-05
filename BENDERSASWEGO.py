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

LIPMP.setParam('OutputFlag', 0)
LIPMP.optimize()

# Set of closed Tfs
closed_TFs = {}
for s in S:
    tfs = []
    for i in TF:
        if Y[i,s].x < 0.9:
            tfs.append(i)
    closed_TFs[s] = tfs
        

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

CSP.setParam('OutputFlag', 0)
CSP.optimize()


#####################################
# CREATING NEW SETS FOR REDUCED CSP #
#####################################

avail_TFs = {}
for s in S:
    available_tfs = []
    for i in TF:
        if Y[i,s].x > 0.9:
            available_tfs.append(i)
            
    avail_TFs[s] = available_tfs
    
# Initialize dictionaries
Md_s = {} # set demand points with multiple TFs
TFd_sm = {} #dictionary: key demand point: values multiple TFs
TFu_sm = {} #dictionary: key demand point: values unique TF  

for s in S:
    multi_demandpts = set()
    multi_Tfs = {}
    unique_Tf = {}
    
    for m in M_s[s]:
        closest_distance = float('inf')
        closest_TFs = []
        
        for i in avail_TFs[s]:
            distance = delta_im[(i,m)]
            if distance < closest_distance:
                closest_distance = distance
                closest_TFs = [i]
            elif distance == closest_distance:
                closest_TFs.append(i)
        # check for multiple TFs at equal distance
            if len(closest_TFs) > 1:
                multi_demandpts.add(m)
                multi_Tfs[m] = closest_TFs
            else:
                unique_Tf[m] = closest_TFs[0]
    
    Md_s[s] = multi_demandpts
    TFd_sm[s] = multi_Tfs
    TFu_sm[s] = unique_Tf
    
##### Calculate the remaining capacity at each TF

Kd_si = {} # dictionary: key TF: values remaining capacity
for s in S:
    Kd = {}
    for i in avail_TFs[s]:
        total_demand_at_TF = 0
        for m in TFu_sm[s]:
            if TFu_sm[s][m] == i:
                demand_at_m = sum(D_sml[(s,m,l)] for l in L)
                total_demand_at_TF += demand_at_m
        Kd[i] = KT_i[i] - total_demand_at_TF
    Kd_si[s] = Kd
 
  
# P1(s)    
# Set of violated scenarios
# Set of violated TFs
# if Kd_si[s]
P1 = {}
for s in S:
    tf = []
    for i in avail_TFs[s]:
        if Kd_si[s][i] < 0:
            tf.append(i)
    P1[s] = tf
 
    
# Dictionary: Key- TFs: Values- demand points assigned to that TF
YES = {}
for s in S:
    listofm = {}
    for i in avail_TFs[s]:
        m_assignedto_i = []
        for m in M_s[s]:
            #Check if the m has a unique TF - which means it has been assigned to that TF
            if TFu_sm[s][m] == i:
            #then append this m
                m_assignedto_i.append(m)
        listofm[i] = m_assignedto_i
    YES[s] = listofm
        


# P2(s,i)       
# Set of closed TFs that are closer to at least one demand point assigned to TF i in scenario s





# FAKE represents a dictionary s:m:TFS where it will gives a list of alernative closed Tfs to a demand point m
FAKE = {}

# P2 represents a dictionary: key - tuples (s,i), values - list of alternative tfs
# P2 = {}


# find current distance
for s in S:
    # p2s = {}
    for i in avail_TFs[s]:
        for m in YES[s][i]:
            tfs = []
            current_distance = delta_im[(i,m)]
            for a in closed_TFs[s]:
                distance_to_closedTF = delta_im[(a,m)]
                if distance_to_closedTF < current_distance:
                    #add this TF to the list of possible alternatives (P2)    
                    tfs.append(a)
            p2s[m] = tfs
    
    
    FAKE[s] = p2s
    # P2[s,i] = tfs

            

            


