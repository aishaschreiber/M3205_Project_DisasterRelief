from gurobipy import *

# Import data from file
import csv

# Read in the data from csv and take each component and put it into a dictionary
complete_data = []
with open("CLFDIP Model Data Generation Tool\Instances (Sets and Parameters)\Pr01_S2.txt", 'r') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        complete_data.append(row)

# Get the idex of all the lines in the complete_data that start with "(" because they are the start of a new set
start_indexes = []
for i in range(len(complete_data)):
    if str(complete_data[i]).find('(') != -1:
        start_indexes.append(i)

"""
Get size of set from row in complete_data
"""
def get_set_size(row):
    return int(str(complete_data[row+1][0]).split('*')[1])

"""
Load the data from the complete_data into a dictionary
start: the row number of the start of the data
end: the row number of the end of the data
value_type: the type of the value in the dictionary (int or float)
"""
def load_into_dict(start, end, value_type):
    dict = {}
    for i in range(start, end):
        [key, value]  = complete_data[i][0].split(': ')
        # Format key
        key = key.split('-')
        if len(key) == 1:
            key = int(key[0])
        else:
            key = tuple([int(x) for x in key])
        # Format value
        value = value.split('; ')
        if value_type == 'int':
            value = [int(x) for x in value]
        elif value_type == 'float':
            value = [float(x) for x in value]
        # Add to dictionary
        dict[key] = value
    return dict

# Sets
#Set of temporary facility (TF) locations
I = range(get_set_size(start_indexes[0])+1) # TF
# Set of permanent facility (PF) locations
J = range(get_set_size(start_indexes[1])+1) # PF
# Set of service coverage windows
K = range(get_set_size(start_indexes[2])+1)
# Set of PF sizes
T = range(get_set_size(start_indexes[3])+1)
# Set of scenarios
S = range(get_set_size(start_indexes[4])+1)
# Set of items
L = range(get_set_size(start_indexes[5])+1)

"""
Set of PFs that can serve TF i within SCW k (J_ik ⊆ J_ik' , for k < k')
Take the 16th-66th rows of the complete_data and put them into a dictoinary J_ik[(i,k)]"""
J_ik = load_into_dict(start_indexes[6]+1, start_indexes[7], 'int')

"""
Set of demand points under disaster scenario s
Take the 68th-70th rows of the complete_data and put them into a dictoinary M_s[s]"""
M_s = load_into_dict(start_indexes[7]+1, start_indexes[8], 'int')

"""
Set of TFsthat are close enough to serve demand point m
Take the 72nd-854th rows of the complete_data and put them into a dictoinary I_m[m]"""
I_m = load_into_dict(start_indexes[8]+1, start_indexes[9], 'int') # TF_m

"""
Demand of point m for item l under scenario s
Take the 856th-3813th rows of the complete_data and put them into a dictoinary D_mls[(s,m,l)]"""
D_sml = load_into_dict(start_indexes[9]+1, start_indexes[10], 'float')

"""
Proportion of demand for item l to be satisfied within service coverage window k
Take the 3815th-3823th rows of the complete_data and put them into a dictoinary R_lk[(k,l)]"""
R_kl = load_into_dict(start_indexes[10]+1, start_indexes[11], 'float')
# Overwrite R_kl[0,0] with 0.33
R_kl[(0,0)] = [0.33]
# Overwrite R_kl[0,1] with 0.5
R_kl[(0,1)] = [0.5]
# Overwrite R_kl[0,2] with 0.2
R_kl[(0,2)] = [0.2]
# Overwrite R_kl[1,0] with 0.66
R_kl[(1,0)] = [0.66]
# Overwrite R_kl[1,1] with 0.8
R_kl[(1,1)] = [0.8]
# Overwrite R_kl[1,2] with 0.5
R_kl[(1,2)] = [0.5]

"""
Capacity of a PF of size t
Take the 3825th-3826th rows of the complete_data and put them into a dictoinary KP_t[t]"""
KP_t = load_into_dict(start_indexes[11]+1, start_indexes[12], 'float')
# JUST IGNORE THE DECIMAL PLACES

"""
Capacity of the TF at location i
Take the 3828th-3844th rows of the complete_data and put them into a dictoinary KT_i[i]"""
KT_i = load_into_dict(start_indexes[12]+1, start_indexes[13], 'int')

"""
Capacity consumption of item l
Take the 3846th-3847th rows of the complete_data and put them into a dictoinary u_l[l]"""
u_l = load_into_dict(start_indexes[13]+1, start_indexes[14], 'float')
# Overwrite u_l[0] with 0.15
u_l[0] = [0.15]
# Overwrite u_l[1] with 0.032
u_l[1] = [0.032]

"""
Acquisition, expected inventory holding and wastage costs cost of item l
Take the 3850th-3852th rows of the complete_data and put them into a dictoinary h_l[l]"""
h_l = load_into_dict(start_indexes[14]+1, start_indexes[15], 'float')
# Overwrite h_l[0] with 0.1
h_l[0] = [0.1]

"""
Fixed cost of PF at location j of size t
Take the 3854th-3881th rows of the complete_data and put them into a dictoinary c_jt[(j,t)]"""
c_jt = load_into_dict(start_indexes[15]+1, start_indexes[16], 'int')

"""
Distance between TF i and demand point m
Take the 3883th-17193 rows of the complete_data and put them into a dictoinary delta_im[(i,m)]"""
delta_im = load_into_dict(start_indexes[16]+1, start_indexes[17], 'float')

"""
Pairs of demand points m and temporary facilities i for each scenario s
Take the 17195th-17197th rows of the complete_data and put them into a dictoinary C_s[s]"""
# This needed a custom function because it is a list of tuples
C_s = {}
for i in range(start_indexes[17]+1, len(complete_data)):
    [key, value]  = complete_data[i][0].split(': ')
    # Format key
    key = int(key)
    # Format value
    value = value.split('; ')
    value = [(int(x.split('-')[0]), int(x.split('-')[1])) for x in value]
    # Add to dictionary
    C_s[key] = value



# Dictionary of demand points with multiple closest TFs
Md_s = {}


# Dictionary of closest TF for each demand point
Id_sm = {}
# For each scenario s in S
for s in S:
    multiples = []
    # For each demand point m in M_s[s]
    for m in M_s[s]:
        # Find the closest distance
        closest_distance = 1000000
        # For each TF i in I_m[m]
        for i in I_m[m]:
            if delta_im[(i,m)][0] < closest_distance:
                closest_distance = delta_im[(i,m)][0]
        # Find the TFs that are that distance away
        closest_TFs = []
        # For each TF i in I_m[m]
        for i in I_m[m]:
            if delta_im[(i,m)][0] == closest_distance:
                closest_TFs.append(i)
        # Add to dictionary
        Id_sm[(s,m)] = closest_TFs
        if len(closest_TFs) > 1:
            multiples.append(m)
    Md_s[s] = multiples



###################################################################################################################################################################################

## Create a logic based benders decomposition model


# Make model and define variables and constraints
LIPMP = Model("LIPMP")

# Add variables
# Y: Binary variable indicating if TF i is opened under scenario s
Y_is = {(i,s): LIPMP.addVar(vtype=GRB.BINARY) for s in S for i in I}

# Z: Binary variable indicating if PF j of size t is opened
Z_jt = {(j,t): LIPMP.addVar(vtype=GRB.BINARY) for j in J for t in T}

# I: Prepositioned inventory amount of item l at PF j
I_jl = {(j,l): LIPMP.addVar() for j in J for l in L}

# Set objective function
# Objective function (1) minimizes the total cost of opening TFs and PFs, and prepositioning items.
LIPMP.setObjective(quicksum(c_jt[j,t][0]*Z_jt[j,t] for j in J for t in T) + quicksum(h_l[l][0]*I_jl[j,l] for j in J for l in L), GRB.MINIMIZE)

# Add constraints
# Constraints (7) limit the amount of prepositioned items by the PF capacity if it is opened.
for j in J:
    LIPMP.addConstr(quicksum(u_l[l][0]*I_jl[j,l] for l in L) <= quicksum(KP_t[t][0]*Z_jt[j,t] for t in T))

# Constraints (9) force the model to open at most one size of PF at each candidate location.
for j in J:
    LIPMP.addConstr(quicksum(Z_jt[j,t] for t in T) <= 1)

# VALID INEQUALITIES
# The valid inequalities are added to the model to strengthen the linear relaxation of the model.

# The first valid inequality set is a corollary of constraints (2) and it makes sure that there 
# is an eligible TF location that is opened, for each demand point under each scenario. 
# Eq. (15) defines the corresponding expression.
for s in S:
    for m in M_s[s]:
        LIPMP.addConstr(quicksum(Y_is[i,s] for i in I_m[m]) >= 1)

# The second valid inequality set benefits from the SCW definition and is a corollary of constraints (6). 
# It makes sure that for each opened TF there is at least one selected PF location of any size within the 
# smallest SCW. Eq. (16) defines the valid inequality where is assumed to be the smallest window.
for s in S:
    for i in I:
        LIPMP.addConstr(quicksum(Z_jt[j,t] for j in J_ik[i,1] for t in T) >= Y_is[i,s])

# The last valid inequality set is defined as a consequence of the demand satisfaction property. 
# Eq. (17) defines the valid inequality set, which ensures that for each scenario and item type, 
# the total amount of stored is enough to cover all demand.
for s in S:
    for l in L:
        LIPMP.addConstr(quicksum(I_jl[j,l] for j in J) >= quicksum(D_sml[s,m,l][0] for m in M_s[s]))

##################################################################################################################################################################################

# Loop through algorithms
for _ in range(10):
    # Solve the LIPMP
    LIPMP.optimize()

    # Get list of opened TFs
    opened_TFs = []
    for i in I:
        if Y_is[i,s].X == 1:
            opened_TFs.append(i)


    # Create an dictionary to store the assignment of demand points to TFs
    X_sim_bar = {}
    for s in S:
        for i in I:
            for m in M_s[s]:
                X_sim_bar[(s,i,m)] = 0

    # Make M_s_dash which is the set demand points with alternative closest TFs
    M_s_dash = {}
    for s in S:
        M_s_dash[s] = []

    # Make I_sm_dash which is the set of closest TFs for each demand point with alternative closest TFs
    I_sm_dash = {}
    for s in S:
        for m in M_s[s]:
            I_sm_dash[(s,m)] = []

    # Make K_si_dash which is the remaining capacity of TF i under scenario s after assigning demand points with unique closest TFs
    K_si_dash = {}
    for s in S:
        for i in I:
            K_si_dash[(s,i)] = 0



    # Solve CSP algorithmically for each scenario
    for s in S:
        # Set CSP to feasible until proven otherwise
        CSP_infeasible = False
        CSP_infeasible_noOption = False
        
        # Assign demand points to closest TFs that is opened and set M_s_dash and I_sm_dash
        for m in M_s[s]:
            # Find the closest distance
            closest_distance = 1000000
            for i in I_m[m]:
                if delta_im[(i,m)][0] < closest_distance:
                    closest_distance = delta_im[(i,m)][0]
            # Find the TFs that are that distance away
            closest_TFs = []
            for i in I_m[m]:
                if delta_im[(i,m)][0] == closest_distance:
                    closest_TFs.append(i)
            # If no TF is close enough to serve demand point m
            if len(closest_TFs) == 0:
                CSP_infeasible = True
                CSP_infeasible_noOption = True
                break
            else:
                # Assign demand point m to closest TF
                X_sim_bar[(s,closest_TFs[0],m)] = 1
                # If there are multiple closest TFs
                if len(closest_TFs) > 1:
                    # Add to M_s_dash
                    M_s_dash[s].append(m)
                    # Add to I_sm_dash
                    I_sm_dash[(s,m)] = closest_TFs

        # Check constraint 20 is satisfied
        for i in I:
            if sum(u_l[l][0]*sum(D_sml[(s,m,l)][0]*X_sim_bar[(s,i,m)] for m in M_s[s]) for l in L):
                CSP_infeasible = True
                break
    
    if CSP_infeasible == True and CSP_infeasible_noOption == False:
        # Set K_si_dash values 
        for s in S:
            for i in I:
                K_si_dash[(s,i)] = KT_i[i][0] - sum(u_l[l][0]*sum(D_sml[(s,m,l)][0]*X_sim_bar[(s,i,m)] for m in M_s[s] if m not in M_s_dash[s]) for l in L)

        # Set of scenarios that are infeasible
        S_dash = []

        # Set of TFs that have violated capacity under scenario s 
        P1_s = {}

        # Set of TF that are closed but are close to atleast one demand point that is violating a capacity constraint 
        P2_si = {}

        # Solve the reduced CSP
        for s in S:
            RCSP = Model("RCSP")

            # Add variables
            X_im = {(i,m): RCSP.addVar(vtype=GRB.BINARY) for i in I_sm_dash[(s,m)] for m in M_s_dash[s]}

            # Add constraints
            for m in M_s_dash[s]:
                RCSP.addConstr(quicksum(X_im[i,m] for i in I_sm_dash[(s,m)]) == 1)

            for i in I_sm_dash[(s,m)]:
                RCSP.addConstr(sum(u_l[l][0]*sum(D_sml[(s,m,l)][0]*X_im[(i,m)] for m in M_s_dash[s]) for l in L)<= K_si_dash[(s,i)])

            # Solve the RCSP
            RCSP.optimize()

            # If the RCSP is infeasible
            if RCSP.status == GRB.INFEASIBLE:
                S_dash.append(s)

                # Add to P1_s
                P1_s[s] = []
                for i in I_sm_dash:
                    if K_si_dash[(s,i)] < 0:
                        P1_s[s].append(i)

                    # Add to P2_si
                    P2_si[(s,i)] = []
                    

        if len(S_dash) != 0:
            # Generate logic based Benders cuts
            pass

    if CSP_infeasible == False & len(S_dash) == 0:
        # Solve DFDSP
        pass

        if DFDSP_unbounded == True:
            # Generate duality-based cuts
            pass

    if CSP_infeasible == False & len(S_dash) != 0 & DFDSP_unbounded == False:
        # Stop
        break
