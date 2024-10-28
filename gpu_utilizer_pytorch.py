import time
import subprocess
import os
import sys
import importlib

def install_package(package_name):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"Package '{package_name}' installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while installing package '{package_name}': {e}")

# check torch is installed
try:
    import torch
    wandb_logger = True
    print("torch package found.")
except ImportError:
    print("torch pacakage not found, installing it:")
    install_package("torch")
    import torch
    importlib.reload(torch)

# check if wandb api token exists AND if wandb pip package is installed
wandb_logger = False
wandb_api_key = os.getenv("WANDB_API_KEY")
if wandb_api_key:
    print(f"env var WANDB_API_KEY found")
    try:
        import wandb
        print("WandB logging enabled.")
        wandb_logger = True
    except ImportError:
        print("WandB pip pacakage not found, installing it:")
        install_package("wandb")
        import wandb
        importlib.reload(wandb)
        print("WandB logging enabled.")
        wandb_logger = True
else:
    print("env var WANDB_API_KEY is either not set or is empty.")

# Initialize wandb
if wandb_logger:
    print("Logger: wandb")
    wandb.init(project="logistic-map-cuda", config={
        "data_points": 16*1024**2,
        "range": (0, 4)
    })
else:
    print("Logger: pytorch native")

# Create data on GPU
x = torch.linspace(0, 4, 16*1024**2).cuda()

# init loop data
iteration = 0
start_time = time.time()
duration_minutes = 600
duration_limit = duration_minutes * 60

# Main loop
try:
    while True:
        x = x * (1.0 - x)
        # Log tensor stats every 5000 iterations
        if iteration % 5000 == 0:
            max_val = x.max().item()
            time_elapsed = round(time.time() - start_time, 3)
            result = subprocess.run(
                ['nvidia-smi',
                 '--query-gpu=utilization.gpu,memory.used,memory.total',
                 '--format=csv,nounits,noheader'],
                stdout=subprocess.PIPE)
            gpu_info = result.stdout.decode('utf-8').strip().split('\n')
            for idx, gpu in enumerate(gpu_info):
                util_str, mem_used_str, mem_total_str = gpu.split(', ')
                util = float(util_str)
                mem_used = float(mem_used_str)
                mem_total = float(mem_total_str)
            print(f"=> Iteration {iteration}:")
            print(f"Max = {max_val}, Time = {time_elapsed}")
            print(f"GPU {idx}: Utilization: {util}%, Memory: {mem_used}/{mem_total} MiB")
            if wandb_logger:
                wandb.log({
                "iteration_number": iteration,
                "max_value": max_val,
                "time_elapsed": time_elapsed,
                "gpu_util": util,
                "gpu_mem": mem_used
                })
            print()
        iteration += 1
        if time_elapsed > duration_limit:
            print("Runtime exceeded 30 minutes. Stopping the loop.")
            break
except KeyboardInterrupt:
    print("Stopping the run...")

finally:
    if wandb_logger:
        wandb.finish()