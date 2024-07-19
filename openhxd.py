import os
print(os.path.abspath(__file__).split("\\").pop(-1))
#print("\\".join(os.path.abspath(__file__).split("\\").pop(-1))+"\\gb_dump.hexd")
#os.system(os.path.abspath(__file__)+"\\gb_dump.hexd")