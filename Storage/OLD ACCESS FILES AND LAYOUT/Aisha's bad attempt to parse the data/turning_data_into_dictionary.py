# THIS IS AN EXAMPLE CODE OF TURNING THEIR DATA INTO THE FORMAT WE NEED 

# This is only a small snippet of the data

# J_ik (at each line, i-k: list of PF locations separated by semicolons)
mydata = """0-0: 0; 1; 2; 3; 4; 8; 16; 22; 23; 24; 25; 26; 27; 29; 30; 31; 32
0-1: 0; 1; 2; 3; 4; 5; 6; 7; 8; 9; 10; 11; 12; 13; 14; 15; 16; 17; 18; 19; 20; 21; 22; 23; 24; 25; 26; 27; 28; 29; 30; 31; 32; 33; 34
0-2: 0; 1; 2; 3; 4; 5; 6; 7; 8; 9; 10; 11; 12; 13; 14; 15; 16; 17; 18; 19; 20; 21; 22; 23; 24; 25; 26; 27; 28; 29; 30; 31; 32; 33; 34
1-0: 0; 1; 2; 3; 4; 8; 16; 22; 23; 24; 25; 26; 27; 29; 30; 31; 32
1-1: 0; 1; 2; 3; 4; 5; 6; 7; 8; 9; 10; 11; 12; 13; 14; 15; 16; 17; 18; 19; 20; 21; 22; 23; 24; 25; 26; 27; 28; 29; 30; 31; 32; 33; 34
1-2: 0; 1; 2; 3; 4; 5; 6; 7; 8; 9; 10; 11; 12; 13; 14; 15; 16; 17; 18; 19; 20; 21; 22; 23; 24; 25; 26; 27; 28; 29; 30; 31; 32; 33; 34"""


# Initalize an empty dictionary
mydata_dict = {}

# Split the data into lines
lines = mydata.split('\n')

# Loop throuhg the lines to extract keys and values
for line in lines:
    parts = line.split(':')
    if len(parts) == 2:
        key = parts[0].strip()
        values = parts[1].strip().split(';')
        values = [int(val.strip()) for val in values]  # Convert values to integers
        mydata_dict[key] = values


# Print the resulting dictionary
print(mydata_dict)


















