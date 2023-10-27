from MAIN_BENDERS import BendersLazy
from MIP_LAYOUT import SimpleLayout

def comparisonMIPBenders() -> None:
    """
    This function compares the results of the SimpleLayout and BendersLazy classes for multiple instances.
    It writes the results to a text file and prints them to the console.
    """
    instances = ["CLFDIP Model Data Generation Tool\Instances (Sets and Parameters)\Pr01_S2.txt",
                "CLFDIP Model Data Generation Tool\Instances (Sets and Parameters)\Pr01_S3.txt",
                "CLFDIP Model Data Generation Tool\Instances (Sets and Parameters)\Pr01_S4.txt",]

    for instance in instances:
        simple = SimpleLayout(instance, verbose=False)
        benders = BendersLazy(instance, verbose=False)

        # write to text file
        f = open("insights.txt", "a")
        f.write("Instance: " + instance + "\n")
        f.write("Simple Layout" + "\n")
        f.write(str(simple) + "\n")
        f.write("Running Benders" + "\n")
        f.write(str(benders) + "\n")
        f.close()


        print("Instance: ", instance)
        print("Simple Layout")
        print(simple)
        print("Running Benders")
        print(benders)

def validInequalities() -> None:
    """
    Generates and writes to file a set of valid inequalities for the CLFDIP model using different layout options.

    Returns:
    None
    """
    
    instance = "CLFDIP Model Data Generation Tool\Instances (Sets and Parameters)\Pr01_S2.txt"

    options= [[False, False, False],
            [True, True, True],
                [True, True, False],
                [False, False, True],
                [True, False, True],
                [False, True, False],
                [False, True, True],
                [True, False, False]]



    for option in options:
        simple = SimpleLayout(instance, verbose=True, extra1=option[0], extra2=option[1], extra3=option[2])

        # write to text file
        f = open("insights2.txt", "a")
        f.write("Option: " + str(option) + "\n")
        f.write(str(simple))
        f.write("\n")
        f.close()


        print("Instance: ", instance)
        print("Simple Layout")
        print(simple)
