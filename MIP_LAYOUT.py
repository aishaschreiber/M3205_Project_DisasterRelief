from gurobipy import *
import access_data_edit


def SimpleLayout(instance: str, verbose: bool = True, valid15 = True, valid16 = True, valid17 = True) -> dict:
    """
    Solves a mixed-integer programming (MIP) problem for disaster relief facility layout optimization.
    
    Args:
    - instance (str): the name of the instance to be solved
    - verbose (bool): whether to print the optimization progress (default True)
    - valid15 (bool): whether to use valid inequality 15 (default True)
    - valid16 (bool): whether to use valid inequality 16 (default True)
    - valid17 (bool): whether to use valid inequality 17 (default True)
    
    Returns:
    - dict: a dictionary containing the objective value, the opened permanent facilities, and the runtime
    """    

    GET = access_data_edit.get_data_sets(instance)
    # SETS
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

    # PARAMETERS
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

    LP = Model("Attempt1")

    if not verbose:
        LP.setParam("OutputFlag", 0)

    # VARIABLES
    # 1, if demand point m in assigned to TF i for scenario s
    X = {(i, s, m): LP.addVar(vtype=GRB.BINARY) for s in S for i in TF for m in M_s[s]}

    # 1, if TF i is opened under scenario s
    Y = {(i, s): LP.addVar(vtype=GRB.BINARY) for s in S for i in TF}

    # amount of item l transported from PJ j to TF i under scenario s
    F = {(j, i, l, s): LP.addVar() for s in S for j in PF for i in TF for l in L}

    # 1, if PF j of size t is opened
    Z = {(j, t): LP.addVar(vtype=GRB.BINARY) for j in PF for t in T}

    # prepositioned invenctory amount of item l at PF j
    I = {(j, l): LP.addVar() for j in PF for l in L}

    # OBJECTIVE
    LP.setObjective(quicksum(c_jt[(j, t)]*Z[j, t] for j in PF for t in T)
                    + quicksum(h_l[l]*I[j,l] for j in PF for l in L), GRB.MINIMIZE)

    # CONSTRAINTS
    # Each demand point assigned to one TF
    TWO = {(s, m):
           LP.addConstr(quicksum(X[i, s, m] for i in TF_m[m]) == 1)
           for s in S for m in M_s[s]}

    # Demand points only assigned to TFs that are open
    THREE = {(i, m, s):
             LP.addConstr(X[i, s, m] <= Y[i, s])
             for i in TF for s in S for m in M_s[s]}

    # TF capacity is not violated
    # demand points that are opened * capacity consumption  of item l , is <= capacity of TF i
    FOUR = {(i, s):
            LP.addConstr(quicksum(u_l[l] * quicksum(u_l[l] * D_sml[(s, m, l)] * X[i, s, m]
                                                    for m in M_s[s] if (s, m, l) in D_sml) for l in L) 
                                                    <= KT_i[i]*Y[i, s]) for i in TF for s in S}

    # Demand points are assigned to the closest TF
    FIVE = {(i, s, m):
            LP.addConstr(quicksum(X[n, s, m] for n in TF_m[m]
                                  if delta_im[(n, m)] <= delta_im[(i, m)]) >= Y[i, s])
                                  for s in S for m in M_s[s] for i in TF_m[m]}

    # Amount of item l transported from PF to TF in scenario S, is >= proportion of demand to be satisfied in SCW k
    SIX = {(s, i, k, l):
            LP.addConstr(quicksum(F[j, i, l, s] for j in PF_ik[(i, k)])
            >= R_kl[(k, l)]*quicksum(D_sml[(s, m, l)]*X[i, s, m] for m in M_s[s] if (s, m, l) in D_sml))
            for s in S for i in TF for k in K for l in L}

    # capacity consumption of item l * amount of prepositioned inventory is <= capacity of TF
    SEVEN = {j:
            LP.addConstr(quicksum(u_l[l]*I[j,l] for l in L) <= quicksum(KP_t[t]*Z[j,t] for t in T))
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

    # VALID INEQUALITIES

    if valid15:
        FIFTEEN = {(s,m):
                LP.addConstr(quicksum(Y[i,s] for i in TF_m[m]) >=1)
                for s in S for m in M_s[s]}
    if valid16:
        SIXTEEN = {(s,i):
                LP.addConstr(quicksum(Z[j,t] for j in PF_ik[(i,1)] for t in T) >= Y[i,s])
                for s in S for i in TF}
    if valid17:
        SEVENTEEN = {(s,l):
                    LP.addConstr(quicksum(I[j,l] for j in PF)
                    >= quicksum(D_sml[(s,m,l)]
                    for m in M_s[s] if (s,m,l) in D_sml))
                    for s in S for l in L}

    LP.optimize()

    if verbose:
        print("Opened Permanent Facility")
    openedPF = []
    for t in T:
        for j in PF:
            if Z[j, t].x > 0.9:
                if verbose:
                    print("\t PF ", j, " with capacity ", t)
                information = {"PF": j, "Size": t, }

                for l in L:
                    if verbose:
                        print("\t\t Item ", l, " Prepositioned: ", I[j, l].x)
                    information["Item" + str(l) + "Prepositioned"] = I[j, l].x

                openedPF.append(information)

    if verbose:
        print("Opened Temporary Facility")
    for s in S:
        if verbose:
            print("\t Scenario ", s)
        for i in TF:
            if Y[i, s].x > 0.9:
                if verbose:
                    print("\t\t TF", i)

    return {"ObjectiveValue": LP.objVal, "OpenedPFs": openedPF, "Time": LP.Runtime}


# This is what runs when you run this file
if __name__ == '__main__':
    default_instance = 'CLFDIP Model Data Generation Tool\Instances (Sets and Parameters)\Pr01_S2.txt'
    dictionary = SimpleLayout(default_instance, verbose=True)
    print(dictionary)
