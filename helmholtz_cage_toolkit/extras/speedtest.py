import numpy as np
from numpy import sin, cos, arccos, ndarray
from time import time


dt = 128
n = 10000

def f1(vector: ndarray):
    return vector / (vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2) ** (1/2)

def f2(vector: ndarray):
    return vector / (vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2) ** (0.5)

def f3(vector: ndarray):
    return vector/np.linalg.norm(vector)


reps = 100_000
d0 = np.zeros(reps)
d1 = np.zeros(reps)
d2 = np.zeros(reps)

for i in range(reps):
    v1 = np.random.random(3)*1000
    v2 = np.random.random(3)*1000
    v3 = np.random.random(3)*1000
    t0 = time()
    output1 = f1(v1)
    t1 = time()
    output2 = f2(v2)
    t2 = time()
    output3 = f3(v3)
    t3 = time()
    d0[i] = t1-t0
    d1[i] = t2-t1
    d2[i] = t3-t2

scale = 1E-6
rd = 2
print(f"Method 1: {round(sum(d0)/len(d0)/scale, rd)} us.")
print(f"Method 2: {round(sum(d1)/len(d1)/scale, rd)} us.")
print(f"Method 3: {round(sum(d2)/len(d2)/scale, rd)} us.")
print("Factor:", round((sum(d1)/len(d1))/(sum(d0)/len(d0)), 2))

# print(f"Values: {output1}, {output2}, {output3}")
# print(f"Lengths: {len(output1)}, {len(output2)}, {len(output3)}")
# print(f"Min: {min(output1)}, {min(output2)}, {min(output3)}")
# print(f"Max: {max(output1)}, {max(output2)}, {max(output3)}")