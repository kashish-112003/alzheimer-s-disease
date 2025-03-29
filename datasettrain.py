import os
import shutil
default_dir = r"C:\Users\KIIT\Desktop\split_dataset\train"
root_dir = "./"
#test_dir = default_dir + "test/"
train_dir = default_dir + "train/"
work_dir = root_dir + "dataset/"

if os.path.exists(work_dir):
    shutil.rmtree(work_dir)
    

os.mkdir(work_dir)
shutil.copytree(train_dir, work_dir)
#copy_tree(test_dir, work_dir)
print("Working Directory Contents:", os.listdir(work_dir))


