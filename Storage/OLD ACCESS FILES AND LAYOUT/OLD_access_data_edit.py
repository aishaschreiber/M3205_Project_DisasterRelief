import csv

# Read in the data from csv and take each component and put it into a dictionary
complete_data = []
with open("/Users/aishaschreiber/Documents/GitHub/M3205_Project_DisasterRelief/CLFDIP Model Data Generation Tool/Instances (Sets and Parameters)/Pr01_S2.txt", 'r') as csvfile:
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
I = range(get_set_size(start_indexes[0]))
# Set of permanent facility (PF) locations
J = range(get_set_size(start_indexes[1]))
# Set of service coverage windows
K = range(get_set_size(start_indexes[2]))
# Set of PF sizes
T = range(get_set_size(start_indexes[3]))
# Set of scenarios
S = range(get_set_size(start_indexes[4]))
# Set of items
L = range(get_set_size(start_indexes[5]))



"""
Set of PFs that can serve TF i within SCW k (J_ki ⊆ J_k'i , for k < k')
Take the 16th-66th rows of the complete_data and put them into a dictoinary J_ik[(i,k)]"""

J_ik = load_into_dict(start_indexes[6]+1, start_indexes[7], 'int')

"""
Set of demand points under disaster scenario s
Take the 68th-70th rows of the complete_data and put them into a dictoinary M_s[s]"""
M_s = load_into_dict(start_indexes[7]+1, start_indexes[8], 'int')
"""
Set of TFsthat are close enough to serve demand point m
Take the 72nd-854th rows of the complete_data and put them into a dictoinary I_m[m]"""
I_m = load_into_dict(start_indexes[8]+1, start_indexes[9], 'int')

"""
Demand of point m for item l under scenario s
Take the 856th-3813th rows of the complete_data and put them into a dictoinary D_mls[(m,l,s)]"""
D_mls = load_into_dict(start_indexes[9]+1, start_indexes[10], 'float')

"""
Proportion of demand for item l to be satisfied within service coverage window k
Take the 3815th-3823th rows of the complete_data and put them into a dictoinary R_lk[(l,k)]"""
R_lk = load_into_dict(start_indexes[10]+1, start_indexes[11], 'float')

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

data_sets = {
    #Set of temporary facility (TF) locations
    'TF': I,
    # Set of permanent facility (PF) locations
    'PF': J,
    # Set of service coverage windows
    'K': K, 
    # Set of PF sizes
    'T': T, 
    # Set of scenarios
    'S': S, 
    # Set of items
    'L': L,
    'PF_ik': J_ik,
    'M_s': M_s,
    'TF_m': I_m,
    'D_mls': D_mls,
    'R_lk': R_lk,
    'KP_t': KP_t,
    'KT_i': KT_i,
    'u_l': u_l,
    'h_l': h_l,
    'c_jt': c_jt,
    'delta_im': delta_im,
    'C_s': C_s
    }
def get_data_sets():
    return data_sets
