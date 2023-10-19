from BendersLazy import BendersLazy
from RUNNINGBENDERS import RunningBenders
from Simple_Layout import SimpleLayout

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
