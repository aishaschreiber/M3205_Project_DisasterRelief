import csv



def get_data_sets(instance : str):

    complete_data = []
    with open(instance, 'r') as textfile:
        for line in textfile:
            complete_data.append(line.strip())  # Remove leading/trailing whitespace
            
    # Get the idex of all the lines in the complete_data that start with "(" because they are the start of a new set
    start_indexes = []
    for i in range(len(complete_data)):
        if str(complete_data[i]).find('(') != -1:
            start_indexes.append(i)
            
    """
    Get size of set from row in complete_data
    """
    def get_set_size(row):
        return int(complete_data[row+1].split('*')[1])

    """
    Load the data from the complete_data into a dictionary
    start: the row number of the start of the data
    end: the row number of the end of the data
    value_type: the type of the value in the dictionary (int or float)
    """

    def load_into_dict(start, end, value_type):
        my_dict = {}
        for i in range(start, end):
            line = complete_data[i]
            key_str, value_str = line.split(': ')
            # Format key
            key_parts = key_str.split('-')
            if len(key_parts) == 1:
                key = int(key_parts[0])
            else:
                key = tuple(map(int, key_parts))
            # Format value by splitting on semicolons
            values = [float(val.replace(',', '.')) for val in value_str.split(';')]
            # Convert value to a single element if there's only one element in the list
            if len(values) == 1:
                values = values[0]
            # Add to dictionary
            my_dict[key] = values
        return my_dict

    def load_into_dict2(start, end, value_type):
        my_dict = {}
        for i in range(start, end):
            line = complete_data[i]
            key_str, value_str = line.split(': ')
            # Format key
            key_parts = key_str.split('-')
            if len(key_parts) == 1:
                key = int(key_parts[0])
            else:
                key = tuple(map(int, key_parts))
            # Format value by splitting on semicolons
            values = [float(val.replace(',', '.')) for val in value_str.split(';')]
            # Convert value to a single element if there's only one element in the list
            # if len(values) == 1:
            #     values = values[0]
            # Add to dictionary
            my_dict[key] = values
        return my_dict



    # Sets
    #Set of temporary facility (TF) locations
    TF = range(get_set_size(start_indexes[0])+1)
    # Set of permanent facility (PF) locations
    PF = range(get_set_size(start_indexes[1])+1)
    # Set of service coverage windows
    K = range(get_set_size(start_indexes[2])+1)
    # Set of PF sizes
    T = range(get_set_size(start_indexes[3])+1)
    # Set of scenarios
    S = range(get_set_size(start_indexes[4])+1)
    # Set of items
    L = range(get_set_size(start_indexes[5])+1)



    """
    Set of PFs that can serve TF i within SCW k (J_ki ⊆ J_k'i , for k < k')
    Take the 16th-66th rows of the complete_data and put them into a dictoinary J_ik[(i,k)]"""

    PF_ik = load_into_dict2(start_indexes[6]+1, start_indexes[7], 'int')

    """
    Set of demand points under disaster scenario s
    Take the 68th-70th rows of the complete_data and put them into a dictoinary M_s[s]"""
    M_s = load_into_dict(start_indexes[7]+1, start_indexes[8], 'int')
    """
    Set of TFsthat are close enough to serve demand point m
    Take the 72nd-854th rows of the complete_data and put them into a dictoinary I_m[m]"""
    TF_m = load_into_dict(start_indexes[8]+1, start_indexes[9], 'int')

    """
    Demand of point m for item l under scenario s
    Take the 856th-3813th rows of the complete_data and put them into a dictoinary D_mls[(m,l,s)]"""
    D_sml = load_into_dict(start_indexes[9]+1, start_indexes[10], 'float')

    """
    Proportion of demand for item l to be satisfied within service coverage window k
    Take the 3815th-3823th rows of the complete_data and put them into a dictoinary R_lk[(l,k)]"""
    R_kl = load_into_dict(start_indexes[10]+1, start_indexes[11], 'float')

    """
    Capacity of a PF of size t
    Take the 3825th-3826th rows of the complete_data and put them into a dictoinary KP_t[t]"""
    KP_t = load_into_dict(start_indexes[11]+1, start_indexes[12], 'int')

    """
    Capacity of the TF at location i
    Take the 3828th-3844th rows of the complete_data and put them into a dictoinary KT_i[i]"""
    KT_i = load_into_dict(start_indexes[12]+1, start_indexes[13], 'int')

    """
    Capacity consumption of item l
    Take the 3846th-3847th rows of the complete_data and put them into a dictoinary u_l[l]"""
    u_l = load_into_dict(start_indexes[13]+1, start_indexes[14], 'int')

    """
    Acquisition, expected inventory holding and wastage costs cost of item l
    Take the 3850th-3852th rows of the complete_data and put them into a dictoinary h_l[l]"""
    h_l = load_into_dict(start_indexes[14]+1, start_indexes[15], 'int')

    """
    Fixed cost of PF at location j of size t
    Take the 3854th-3881th rows of the complete_data and put them into a dictoinary c_jt[(j,t)]"""
    c_jt = load_into_dict(start_indexes[15]+1, start_indexes[16], 'int')

    """
    Distance between TF i and demand point m
    Take the 3883th-17193 rows of the complete_data and put them into a dictoinary delta_im[(i,m)]"""
    delta_im = load_into_dict(start_indexes[16]+1, start_indexes[17], 'int')

    """
    Pairs of demand points m and temporary facilities i for each scenario s
    Take the 17195th-17197th rows of the complete_data and put them into a dictoinary C_s[s]"""
    # This needed a custom function because it is a list of tuples
    # C_s = {}
    # for i in range(start_indexes[17]+1, len(complete_data)):
    #     [key, value]  = complete_data[i][0].split(': ')
    #     # Format key
    #     key = int(key)
    #     # Format value
    #     value = value.split('; ')
    #     value = [(int(x.split('-')[0]), int(x.split('-')[1])) for x in value]
    #     # Add to dictionary
    #     C_s[key] = value

    data_sets = {
        #Set of temporary facility (TF) locations
        'TF': TF,
        # Set of permanent facility (PF) locations
        'PF': PF,
        # Set of service coverage windows
        'K': K, 
        # Set of PF sizes
        'T': T, 
        # Set of scenarios
        'S': S, 
        # Set of items
        'L': L,
        'PF_ik': PF_ik,
        'M_s': M_s,
        'TF_m': TF_m,
        'D_sml': D_sml,
        'R_kl': R_kl,
        'KP_t': KP_t,
        'KT_i': KT_i,
        'u_l': u_l,
        'h_l': h_l,
        'c_jt': c_jt,
        'delta_im': delta_im,
        # 'C_s': C_s
        }

    return data_sets
