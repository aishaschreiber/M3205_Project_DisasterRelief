# M3205_Project_DisasterRelief
Aisha, Ruoxuan, Lucy

Steps to run model:
1. Ensure you have downloaded the files/folders: 'BendersLazy.py', 'CLFDIP Model Data Generation Tool' folder, access_data_edit.py
2. Ensure the working directory is the same as the 'CLFDIP Model Data Generation Tool' folder
3. 'BendersLazy.py' operates with a Verbose, thus setting Verbose = TRUE will ensure the output is printed. To run the model, just run 'BendersLazy.py'. 
4. To run the MIP formulation, use 'Simple_Layout.py'


CLFDIP Model Data Generation Tool is the folder that contains all the instances (provided by the Authors)
More Generate Instances is the folder that contains instances generated by us
'ImprovementIIS.py' contains the attempt at improving the model using IIS constraints. 
'Insights.py' and 'Insights.txt' contain code to compare the run time of the Benders Loop verses the MIP formulation.
