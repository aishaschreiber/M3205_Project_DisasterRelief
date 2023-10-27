from gurobipy import *
import access_data_edit

# This file is wrapped in a verbose function. 
# To run the benders loop, go to the BOTTOM OF THE FILE and ensure you have selected your desired instance
# Here you can decide whether you want to print the outputs (by setting verbose to True)
# Then run the whole file

def BendersLazy(instance: str, verbose: bool = True) -> dict:

    GET = access_data_edit.get_data_sets(instance)
    # SETS: defined using the access file that loads in the instances
    
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

    if not verbose:
        LIPMP.setParam("OutputFlag",0)

    # Master Variables
    # 1, if TF i is opened under scenario s
    Y = {(i, s): LIPMP.addVar(vtype=GRB.BINARY) for s in S for i in TF}
    # 1, if PF j of size t is opened
    Z = {(j, t): LIPMP.addVar(vtype=GRB.BINARY) for j in PF for t in T}
    # prepositioned invenctory amount of item l at PF j
    I = {(j, l): LIPMP.addVar() for j in PF for l in L}

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

    ##### LINEAR RELAXATION ####

    FIFTEEN = {(s,m):
            LIPMP.addConstr(quicksum(Y[i,s] for i in TF_m[m])>=1 ) 
            for s in S for m in M_s[s]}

    SIXTEEN  = {(s,i):
                LIPMP.addConstr(quicksum(Z[j,t] for j in PF_ik[(i,1)] for t in T)>= Y[i,s])
                for s in S for i in TF} 

    SEVENTEEN = {(s,l):
                    LIPMP.addConstr(quicksum(I[j,l] for j in PF)
                                    >=quicksum(D_sml[(s,m,l)]
                        for m in M_s[s] if (s,m,l) in D_sml))
                                    for s in S for l in L}
    
    ##########################
    # End of Master Problem

    ###################################################################
    # This function is used in the sub-problems to define some new sets
    
    def AvailableTF(Y):
        avail_TFs = {}
        for s in S:
            available_tfs = []
            for i in TF:
                if Y[i, s] > 0.9:
                    available_tfs.append(i)
            avail_TFs[s] = available_tfs

        closed_TFs = {}
        for s in S:
            tfs = []
            for i in TF:
                if Y[i, s] < 0.9:
                    tfs.append(i)
            closed_TFs[s] = tfs
        return avail_TFs, closed_TFs

    
    ######## BENDERS DECOMPOSITION #############
    
    # The Benders Loop is defined in a Callback function

    def Callback(model, where):
        if where == GRB.Callback.MIPSOL:
            YV = LIPMP.cbGetSolution(Y)
            IV = LIPMP.cbGetSolution(I)
            CutsAdded = 0
            for s in S:
                    # define clustering subproblem here
                    CSP = Model("Clustering Subproblem")

                    if not verbose:
                        CSP.setParam("OutputFlag", 0)

                    # CSP Variables
                    X = {(i,m): CSP.addVar(vtype=GRB.BINARY) for i in TF for m in M_s[s]}

                    #No Objective, Just feasiblility check

                    EIGHTEEN = {m:
                                CSP.addConstr(quicksum(X[i, m] for i in TF_m[m]) ==1)
                                for m in M_s[s]} 

                    NINETEEN = {(m,i):
                                CSP.addConstr(X[i, m] <= YV[i,s])
                                for m in M_s[s] for i in TF_m[m]}

                    TWENTY = {i:
                            CSP.addConstr(quicksum(u_l[l]*D_sml[(s, m, l)]*X[i, m] for l in L for m in M_s[s]) \
                                            <= KT_i[i] * YV[i, s])
                                for i in TF}      

                    CSP.optimize()
                    if verbose:
                        print("CSP Solved")

                    if CSP.status == GRB.INFEASIBLE:
                        if verbose:
                            print("CSP Infeasible")

                        #################Define some new set########################## (Until Line517)
                        avail_TFs = {}
                        for b in S:
                            available_tfs = []
                            for i in TF:
                                if YV[i, b] > 0.9:
                                    available_tfs.append(i)
                            avail_TFs[b] = available_tfs

                        closed_TFs = {}
                        for b in S:
                            tfs = []
                            for i in TF:
                                if YV[i, b] < 0.9:
                                    tfs.append(i)
                            closed_TFs[b] = tfs
                        Md_s = {}  # set demand points with multiple TFs
                        TFd_sm = {}  # dictionary: key demand point: values multiple TFs
                        TFu_sm = {}  # dictionary: key demand point: values unique TF

                        for b in S:
                            multi_demandpts = set()
                            multi_Tfs = {}
                            unique_Tf = {}

                            for m in M_s[b]:
                                closest_distance = float('inf')
                                closest_TFs = []

                                for i in avail_TFs[b]:
                                    distance = delta_im[(i, m)]
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

                            Md_s[b] = multi_demandpts
                            TFd_sm[b] = multi_Tfs
                            TFu_sm[b] = unique_Tf

                        Mu_s = {b: [value for value in M_s[b] if value not in Md_s.get(b, [])] for b in M_s}

                        II = []
                        for b in S:
                            for m in Md_s[b]:
                                for i in TFd_sm[b][m]:
                                    if i not in II:
                                        II.append(i)

                        Reverse_Id = {}
                        for b in S:
                            Id = {}
                            for i in II:
                                mlist = []
                                for m in TFd_sm[b]:
                                    if i in TFd_sm[b][m]:
                                        mlist.append(m)
                                if len(mlist) > 0:
                                    Id[i] = mlist
                            Reverse_Id[b] = Id

                        Reverse_Iu = {}
                        for b in S:
                            Iu = {}
                            for m in TFu_sm[b]:
                                i = TFu_sm[b][m]        
                                if TFu_sm[b][m] not in Iu:
                                    Iu[i] = []
                                Iu[i].append(m)
                            Reverse_Iu[b] = Iu

                        Kd_si = {}
                        for b in S:
                            Kd = {}
                            for i in avail_TFs[b]:
                                total_demand_at_TF = 0
                                for m in TFu_sm[b]:
                                    if TFu_sm[b][m] == i:
                                        demand_at_m = sum(D_sml[(b,m,l)] for l in L)
                                        total_demand_at_TF += demand_at_m
                                Kd[i] = KT_i[i] - total_demand_at_TF
                            Kd_si[b] = Kd

                        Sd = []
                        for b in S:
                            for i in Kd_si[b]:
                                if Kd_si[b][i] < 0:
                                    if b not in Sd:
                                        Sd.append(b)
                        P1 = {}
                        for b in Sd:
                            tf = []
                            for i in avail_TFs[b]:
                                if Kd_si[b][i] < 0:
                                    tf.append(i)
                            P1[b] = tf

                        CURRENT_ASSIGNED = {}
                        for b in S:
                            listofm = {}
                            for i in avail_TFs[b]:
                                m_assignedto_i = []
                                for m in M_s[b]:
                                    # Check if the m has a unique TF - which means it has been assigned to that TF
                                    if TFu_sm[b][m] == i:
                                        # then append this m
                                        m_assignedto_i.append(m)
                                listofm[i] = m_assignedto_i
                            CURRENT_ASSIGNED[b] = listofm

                        # ALTERNATIVES represents a dictionary [s][m][TFs] where it will gives a list of alernative closed Tfs to a demand point m
                        ALTERNATIVES = {}
                        for b in S:
                            fk1 = {}
                            for i in avail_TFs[b]:
                                fk2 = {}
                                for m in CURRENT_ASSIGNED[b][i]:
                                    tfs = []
                                    # current distance to assigned TF
                                    current_distance = delta_im[(i, m)]
                                    for a in closed_TFs[b]:
                                        # distance to each closed TF
                                        distance_to_closedTF = delta_im[(a, m)]
                                        if distance_to_closedTF < current_distance:
                                            # add this TF to the list of possible alternatives (P2)    
                                            tfs.append(a)
                                    fk2[m] = tfs
                                fk1[i] = fk2
                            ALTERNATIVES[b] = fk1

                        # P2(s,i): dictionary: Key- (s,i) tuple. Values- closed TFs with a demand point thats closer (TFs are inside FAKE)     
                        # (s,i): represents the TF that the m is CURRENTLY ASSIGNED TO
                        P2 = {}
                        for b in Sd:
                            for i in CURRENT_ASSIGNED[b]:
                                # print(i)
                                altlist = []
                                # Find all the alternative closedTFs available for each tuple (s,i)
                                # This means, we need to find all the demand points assigned to each i (and then find their alternative TFs)
                                for m in CURRENT_ASSIGNED[b][i]:
                                    # for m in ALTERNATIVES.get(s,  {}):
                                    for tf in ALTERNATIVES[b][i][m]:
                                        if tf not in altlist:
                                            altlist.append(tf)
                                    P2[(b, i)] = altlist

                        #################Finish defining new set##########################

                        ##### Define ReducedCSP here
                        ReducedCSP = Model("CheckForAlternatives")

                        Xd = {(i, m): ReducedCSP.addVar(vtype=GRB.BINARY) for i in Reverse_Id[s] for m in Md_s[s]}

                        # No objective

                        # Constraints
                        Constraint24 = {m:
                                ReducedCSP.addConstr(quicksum(Xd[i,m] for i in TFd_sm[s][m]) == 1) for m in Md_s[s]}

                        Constraint25 = {i:
                                    ReducedCSP.addConstr(quicksum(u_l[l]* quicksum(D_sml[(s,m,l)]*Xd[i,m] for m in Reverse_Id[s][i]) for l in L) 
                                    <= Kd_si[s][i])
                                    for i in Reverse_Id[s]}

                        ReducedCSP.setParam("OutputFlag", 0)
                        ReducedCSP.optimize()

                        if ReducedCSP.status != GRB.INFEASIBLE:
                            if verbose:
                                print("ReducedCSP Solved")

                        if ReducedCSP.status == GRB.INFEASIBLE:
                            if verbose:
                                print("ReducedCSP Infeasible")
                            for d in Sd:
                                for i in P1[d]:                         
                                    LIPMP.cbLazy(quicksum(Y[p,d] for p in P2[(d,i)]) - Y[i, d] >= 0)  # LBBD Cut
                                    CutsAdded += 1

                    if CSP.status != GRB.INFEASIBLE or ReducedCSP.status != GRB.INFEASIBLE:

                        for l in L:
                            # print("##### We are with Item", l)

                            if CSP.status != GRB.INFEASIBLE:
                                D_bar = {(s, i, l): quicksum(D_sml[(s, m, l)] * X[i, m].x for m in M_s[s]) for i in TF}

                            if CSP.status == GRB.INFEASIBLE and ReducedCSP.status != GRB.INFEASIBLE:

                                D_bar = {}

                                for i in TF:
                                    if i in Reverse_Id[s]:
                                        D_bar[(s, i, l)] = quicksum(D_sml[(s, m, l)] * Xd[i, m].x for m in Md_s[s])
                                    elif i in Reverse_Iu[s]:
                                        D_bar[(s, i, l)] = quicksum(D_sml[(s, m, l)] for m in Reverse_Iu[s][i])
                                    else:
                                        D_bar[(s, i, l)] = 0

                            avail_TFs, closed_TFs = AvailableTF(YV)

                            DFDSP = Model("Dual of Flow Distribution Sub-Problem")
                            # We define the dual of flow distribution problem

                            Phi = {j: DFDSP.addVar(lb = 0) for j in PF}
                            Theta = {(i,k): DFDSP.addVar(ub = 0) for i in TF for k in K}

                            DFDSP.setObjective(quicksum(Phi[j] * IV[j,l] for j in PF) + quicksum(Theta[i,k] * R_kl[k,l] * D_bar[(s,i,l)] * YV[i,s] for i in TF for k in K))

                            Constraint33 = {(j, i):
                                            DFDSP.addConstr((quicksum(Theta[i, k] for k in K if j in PF_ik[i, k]) + Phi[j]) <= 0)
                                            for j in PF for i in TF}

                            #########################################
                            DFDSP.setParam("OutputFlag", 0)
                            DFDSP.optimize()
                            if DFDSP.status != GRB.INFEASIBLE:
                                if verbose:
                                    print("DFDSP Solved")

                            if DFDSP.status == GRB.UNBOUNDED:
                                if verbose:
                                    print("DFDSP Unbounded")
                                LIPMP.cbLazy(quicksum(Phi[j].UnbdRay * I[j,l] for j in PF) +
                                                quicksum(Theta[i, k].UnbdRay * R_kl[k, l] * D_bar[(s, m, l)] * Y[i, s]) <= 0)
                                # print("DFDSP Cut added for item ", l)
                                CutsAdded += 1

    LIPMP.setParam('LazyConstraints', 1)
    LIPMP.optimize(Callback)

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
                        print("\t\t Item ", l, " Prepositioned: ", I[j,l].x)
                    information["Item" + str(l) + "Prepositioned"] = I[j,l].x

                openedPF.append(information)

    if verbose:
        print("Opened Temporary Facility")
    for s in S:
        if verbose:
            print("\t Scenario ", s)
        for i in TF:
            if Y[i, s].x > 0.9:
                if verbose:
                    print("\t\t TF",i)

    return {"ObjectiveValue": LIPMP.objVal, "OpenedPFs": openedPF, "Time": LIPMP.Runtime}


    ###################################
    ####### End of Benders Loop #######
    ###################################
    
#########################################
# This is what runs when you click play #
if __name__ == "__main__":
    default_instance = "CLFDIP Model Data Generation Tool/Instances (Sets and Parameters)/Pr01_S2.txt"
    dictionary = BendersLazy(default_instance, verbose=True)
    # Set verbose to true to print

