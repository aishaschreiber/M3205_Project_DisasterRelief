from gurobipy import *

# Import data from file
import csv


# Instances
Instance = ["CLFDIP Model Data Generation Tool\Instances (Sets and Parameters)\Pr01_S2.txt", 
            "CLFDIP Model Data Generation Tool\Instances (Sets and Parameters)\Pr01_S3.txt",
            "CLFDIP Model Data Generation Tool\Instances (Sets and Parameters)\Pr01_S4.txt"]

Results = {}

for instance in Instance:

    # Read in the data from csv and take each component and put it into a dictionary
    complete_data = []
    with open(instance, 'r') as csvfile:
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





    # Initialise CLFDIP
    CLFDIP = Model("CLFDIP")

    # DECISION VARIABLES
    # X: Binary variable indicating clustering decisions, i.e. if demand point m is assigned to TF i for scenario s
    X_ism = {(i,s,m): CLFDIP.addVar(vtype=GRB.BINARY) for s in S for i in I for m in M_s[s]}

    # Y: Binary variable indicating if TF i is opened under scenario s
    Y_is = {(i,s): CLFDIP.addVar(vtype=GRB.BINARY) for s in S for i in I}

    # F: Amount of item l transported from PF j to TF i under scenario s
    F_jils = {(j,i,l,s): CLFDIP.addVar() for s in S for j in J for i in I for l in L}

    # Z: Binary variable indicating if PF j of size t is opened
    Z_jt = {(j,t): CLFDIP.addVar(vtype=GRB.BINARY) for j in J for t in T}

    # I: Prepositioned inventory amount of item l at PF j
    I_jl = {(j,l): CLFDIP.addVar() for j in J for l in L}

    # OBJECTIVE FUNCTION
    # Minimizes the total pre-disaster cost due to opening permanent facilities, and the acquisition and holding cost of prepositioned inventory
    #   Minimise the the cost of opening PFs (the cost * whether they are opened for each PF) 
    #   and the cost of prepositioning items at PFs (the cost * the amount of items prepositioned for each PF and item type)
    CLFDIP.setObjective(quicksum(c_jt[j,t][0]*Z_jt[j,t] for j in J for t in T) + quicksum(h_l[l][0]*I_jl[j,l] for j in J for l in L), GRB.MINIMIZE)

    # CONSTRAINTS
    # Constraints (2) make sure that each demand point under each scenario is assigned to one of the TFs in the Im set, 
    # which contains the facilities that are close enough to serve the demand point.
    for s in S:
        for m in M_s[s]:
            # Exactly one TF is assigned to each demand point
            CLFDIP.addConstr(quicksum(X_ism[i,s,m] for i in I_m[m]) == 1)

    # Constraints (3) allow demand point assignments only to the opened TFs
    for s in S:
        for m in M_s[s]:
            for i in I_m[m]:
                # If TF i is not opened, then it cannot be assigned to any demand point
                CLFDIP.addConstr(X_ism[i,s,m] <= Y_is[i,s])

    # Constraints (4) ensure that TF capacity is not violated
    for s in S:
        for i in I:
            # The amount of items that are assigned to TF i under scenario s cannot exceed the capacity of the TF
            CLFDIP.addConstr(quicksum(u_l[l][0] * quicksum(D_sml[s,m,l][0]*X_ism[i,s,m] for m in M_s[s]) for l in L) <= KT_i[i][0]*Y_is[i,s])

    ### Note: Although constraints (3) become redundant along with (4), they are kept to obtain a tighter linear relaxation of the model.

    # Constraints (5) ensure that demand points are assigned to the closest available TFs
    # Assignments of demand points to the closest available TF is provided by Eq. (5), 
    # using the closest assignment constraints defined by Church and Cohon (1976).
    for s in S:
        for m in M_s[s]:
            for i in I_m[m]:
                # 
                CLFDIP.addConstr(quicksum(X_ism[n,s,m] for n in I_m[m] if delta_im[n,m]<= delta_im[i,m]) >= Y_is[i,s])

    # Constraints (6) state that for each item at a TF under a scenario, rkl proportion of the total demand 
    # must be satisfied within kth service coverage window. Fig. 2 below illustrates the SCWs and corresponding 
    # sets. Note that the windows define only upper limits on the distance to avoid being over-restrictive, 
    # therefore the demand regarding the largest window can be satisfied by the PFs that are within the smaller windows ().
    for s in S:
        for i in I:
            for l in L:
                for k in K:
                    CLFDIP.addConstr(quicksum(F_jils[j,i,l,s] for j in J_ik[i,k]) >= R_kl[k,l][0]*quicksum(D_sml[s,m,l][0]*X_ism[i,s,m] for m in M_s[s]))

    # Constraints (7) limit the amount of prepositioned items by the PF capacity if it is opened.
    for j in J:
        CLFDIP.addConstr(quicksum(u_l[l][0]*I_jl[j,l] for l in L) <= quicksum(KP_t[t][0]*Z_jt[j,t] for t in T))

    # Constraints (8) state the amount of items that can be shipped from a PF under each scenario is limited by the prepositioned amount
    for s in S:
        for j in J:
            for l in L:
                CLFDIP.addConstr(quicksum(F_jils[j,i,l,s] for i in I) <= I_jl[j,l])

    # Constraints (9) force the model to open at most one size of PF at each candidate location.
    for j in J:
        CLFDIP.addConstr(quicksum(Z_jt[j,t] for t in T) <= 1)

    # Finally, (10), (11), (12), (13), (14) define the binary and positive variables. In the model, 
    # and I_jl variables are left as continuous variables to reduce the number of integer variables. This can be justified 
    # since the flow variables will not be the actual amount that is carried in a disaster situation and a post-disaster 
    # routing model will be deciding the real transportation amount. Although the inventory decisions will be executed right away, 
    # rounding the inventory values could be insignificant compared to fixed cost of facilities in a realistic setting.

    # VALID INEQUALITIES
    # The valid inequalities are added to the model to strengthen the linear relaxation of the model.

    # The first valid inequality set is a corollary of constraints (2) and it makes sure that there 
    # is an eligible TF location that is opened, for each demand point under each scenario. 
    # Eq. (15) defines the corresponding expression.
    for s in S:
        for m in M_s[s]:
            CLFDIP.addConstr(quicksum(Y_is[i,s] for i in I_m[m]) >= 1)

    # The second valid inequality set benefits from the SCW definition and is a corollary of constraints (6). 
    # It makes sure that for each opened TF there is at least one selected PF location of any size within the 
    # smallest SCW. Eq. (16) defines the valid inequality where is assumed to be the smallest window.
    for s in S:
        for i in I:
            CLFDIP.addConstr(quicksum(Z_jt[j,t] for j in J_ik[i,1] for t in T) >= Y_is[i,s])

    # The last valid inequality set is defined as a consequence of the demand satisfaction property. 
    # Eq. (17) defines the valid inequality set, which ensures that for each scenario and item type, 
    # the total amount of stored is enough to cover all demand.
    for s in S:
        for l in L:
            CLFDIP.addConstr(quicksum(I_jl[j,l] for j in J) >= quicksum(D_sml[s,m,l][0] for m in M_s[s]))

    CLFDIP.optimize()

    print("DONE")

    # CHECK IF CONSTRAINTS ARE SATISFIED

    # Check if constraint 2 is satisfied
    # Each demand point is assigned to exactly one TF
    for s in S:
        for m in M_s[s]:
            if sum([X_ism[i,s,m].x for i in I_m[m]]) != 1:
                print("Constraint 2 not satisfied for s = " + str(s) + ", m = " + str(m))

    # Check if constraint 3 is satisfied
    # If TF i is not opened, then it cannot be assigned to any demand point
    for s in S:
        for m in M_s[s]:
            for i in I_m[m]:
                if X_ism[i,s,m].x > Y_is[i,s].x:
                    print("Constraint 3 not satisfied for s = " + str(s) + ", m = " + str(m) + ", i = " + str(i))

    # Check if constraint 4 is satisfied
    # The amount of items that are assigned to TF i under scenario s cannot exceed the capacity of the TF
    for s in S:
        for i in I:
            if sum([u_l[l][0] * sum([D_sml[s,m,l][0]*X_ism[i,s,m].x for m in M_s[s]]) for l in L]) > KT_i[i][0]*Y_is[i,s].x:
                print("Constraint 4 not satisfied for s = " + str(s) + ", i = " + str(i))

    # Check if constraint 5 is satisfied
    # For each demand point, the closest available TF is assigned
    for s in S:
        for m in M_s[s]:
            for i in I_m[m]:
                if sum([X_ism[n,s,m].x for n in I_m[m] if delta_im[n,m]<= delta_im[i,m]]) < Y_is[i,s].x:
                    print("Constraint 5 not satisfied for s = " + str(s) + ", m = " + str(m) + ", i = " + str(i))

    # Check if constraint 6 is satisfied
    # For each item at a TF under a scenario, rkl proportion of the total demand must be satisfied within kth service coverage window
    for s in S:
        for i in I:
            for l in L:
                for k in K:
                    if sum(F_jils[j,i,l,s].x for j in J_ik[i,k]) < R_kl[k,l][0]*sum(D_sml[s,m,l][0]*X_ism[i,s,m].x for m in M_s[s]):
                        print("Constraint 6 not satisfied for s = " + str(s) + ", i = " + str(i) + ", l = " + str(l) + ", k = " + str(k))
                        print("LHS = " + str(sum(F_jils[j,i,l,s].x for j in J_ik[i,k])))
                        print("RHS = " + str(R_kl[k,l][0]*sum(D_sml[s,m,l][0]*X_ism[i,s,m].x for m in M_s[s])))

    # Check if constraint 7 is satisfied
    # The amount of prepositioned items cannot exceed the capacity of the PF if it is opened
    for j in J:
        if sum([u_l[l][0]*I_jl[j,l].x for l in L]) > sum([KP_t[t][0]*Z_jt[j,t].x for t in T]):
            print("Constraint 7 not satisfied for j = " + str(j))

    # Check if constraint 8 is satisfied
    # The amount of items that can be shipped from a PF under each scenario is limited by the prepositioned amount
    for s in S:
        for j in J:
            for l in L:
                if sum([F_jils[j,i,l,s].x for i in I]) > I_jl[j,l].x:
                    print("Constraint 8 not satisfied for s = " + str(s) + ", j = " + str(j) + ", l = " + str(l))
                    print("LHS = " + str(sum([F_jils[j,i,l,s].x for i in I])))
                    print("RHS = " + str(I_jl[j,l].x))

    # Check if constraint 9 is satisfied
    # At most one size of PF can be opened at each candidate location
    for j in J:
        if sum([Z_jt[j,t].x for t in T]) > 1:
            print("Constraint 9 not satisfied for j = " + str(j))

    # Print the solution
    print("Solution:")

    # Print the open PFs and the items that are prepositioned at them
    facilities = []
    for j in J:
        for t in T:
            if Z_jt[j,t].x == 1:
                print("PF " + str(j) + " of size " + str(t) + " is opened and the following items are prepositioned at it:")
                Items = []
                for l in L:
                    if I_jl[j,l].x > 0.001:
                        Items.append((l, round(I_jl[j,l].x)))
                print(Items)
                facilities.append([j, t, Items])


    print("")
    print("")

    # # For each scenario, print TF assignments and the amount of items that are shipped from each PF to each TF
    # for s in S:
    #     print("Scenario " + str(s) + ":")
    #     # For each TF print 
    #     for i in I:
    #         if Y_is[i,s].x == 1:
    #             demand_points = []
    #             for m in M_s[s]:
    #                 if X_ism[i,s,m].x == 1:
    #                     demand_points.append(m)
    #             if len(demand_points) > 0:
    #                 print("TF " + str(i) + ":")
    #                 # For each PF print how much goes to each TF
    #                 for j in J:
    #                     for l in L:
    #                         if F_jils[j,i,l,s].x > 0:
    #                             print("    " + str(round(F_jils[j,i,l,s].x)) + " of item " + str(l) + " comes from PF " + str(j))
                    
    #                 # Print the demand points that are assigned to the TF
    #                 print("    Demand points assigned:")
    #                 demand_points = []
    #                 for m in M_s[s]:
    #                     if X_ism[i,s,m].x == 1:
    #                         demand_points.append(m)
    #                 print(demand_points)
    #                 print("")
    #     print("")
    #     print("")

    # Print the objective value and the run time
    print("Objective value: " + str(CLFDIP.objVal))
    print("Run time: " + str(CLFDIP.Runtime))



    Results[instance] = [CLFDIP.objVal, CLFDIP.Runtime, facilities]