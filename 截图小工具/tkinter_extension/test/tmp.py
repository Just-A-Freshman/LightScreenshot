from subprocess import Popen

save_path = r"D:\Learning\Python.learning\Python项目\截图小工具\src\image\default_save\619x229_3521001994.png"


import os

os.system(f"start '{save_path}'")

process = Popen(['start', save_path], shell=True)
process.wait()
