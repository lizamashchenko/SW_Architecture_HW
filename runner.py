import subprocess
import time

# path = "no_lock_test.py"
# path = "pessimistic_lock.py"
path = "optimistic_lock.py"

start_time = time.time()

processes = [
    subprocess.Popen(["python", path]),
    subprocess.Popen(["python", path]),
    subprocess.Popen(["python", path]),
]

for p in processes:
    p.wait()

end_time = time.time()
print(f"Done, with execution Time: {end_time - start_time:.4f} seconds")