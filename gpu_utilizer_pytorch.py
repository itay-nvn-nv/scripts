import time
import subprocess
import os
import sys
import importlib
import threading
import numpy as np

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
    print("torch package not found, installing it:")
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
        print("WandB pip package not found, installing it:")
        install_package("wandb")
        import wandb
        importlib.reload(wandb)
        print("WandB logging enabled.")
        wandb_logger = True
else:
    print("env var WANDB_API_KEY is either not set or is empty.")

# check if pynvml is installed
try:
    import pynvml
    print("pynvml package found.")
except ImportError:
    print("pynvml package not found, installing it:")
    install_package("pynvml")
    import pynvml
    importlib.reload(pynvml)

# Configuration
DURATION = 600  # seconds - Total script runtime
WARMUP_DURATION = 10  # seconds - Initial warmup period
TARGET_UTILIZATION = 0.7  # Target average GPU utilization (70%)
MATRIX_SIZE = 2048  # Adjust matrix size to influence GPU load
TRANSFER_SIZE_MB = 50  # Size of data to transfer between GPUs (MB)
TRANSFER_INTERVAL = 1  # seconds - How frequently to perform transfers

# Initialize pynvml
pynvml.nvmlInit()

# Initialize wandb
if wandb_logger:
    print("Logger: wandb")
    wandb.init(project="logistic-map-cuda", config={
        "data_points": 16*1024**2,
        "range": (0, 4),
        "duration": DURATION,
        "warmup_duration": WARMUP_DURATION,
        "target_utilization": TARGET_UTILIZATION,
        "matrix_size": MATRIX_SIZE,
        "transfer_size_mb": TRANSFER_SIZE_MB
    })
else:
    print("Logger: pytorch native")

def get_gpu_utilization(handle):
    return pynvml.nvmlDeviceGetUtilizationRates(handle).gpu / 100.0

def get_gpu_memory_utilization(handle):
    memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
    return memory_info.used / memory_info.total

def check_nvlink_support(handle, peer_index):
    """Check if NVLink is supported between two GPUs."""
    try:
        pynvml.nvmlDeviceGetNvLinkUtilizationCounter(handle, peer_index, 0)
        return True
    except pynvml.NVMLError:
        return False

def get_nvlink_stats(handle, peer_index):
    """Gets NVLink RX/TX utilization counters for a given link."""
    try:
        rx = pynvml.nvmlDeviceGetNvLinkUtilizationCounter(handle, peer_index, 0)  # 0 = RX
        tx = pynvml.nvmlDeviceGetNvLinkUtilizationCounter(handle, peer_index, 1)  # 1 = TX
        return rx, tx
    except pynvml.NVMLError:
        return 0, 0

def transfer_data_gpu_to_gpu(gpu0, gpu1, size_mb=100):
    """Transfers data between two GPUs using PyTorch and measures time."""
    device0 = torch.device(f"cuda:{gpu0}")
    device1 = torch.device(f"cuda:{gpu1}")

    data = torch.randn(size_mb * 256, 1024, dtype=torch.float32, device=device0)
    start_time = time.time()
    data = data.to(device1)
    torch.cuda.synchronize(device=device0)
    torch.cuda.synchronize(device=device1)
    transfer_time = time.time() - start_time
    return transfer_time

def format_time(seconds):
    """Format time in a human-readable format."""
    if seconds < 60:
        return f"{seconds:.3f}s"
    minutes = int(seconds // 60)
    seconds = seconds % 60
    return f"{minutes}m {seconds:.3f}s"

# Check if CUDA is available and get GPU information
if not torch.cuda.is_available():
    print("CUDA is not available.")
    sys.exit(1)

num_gpus = torch.cuda.device_count()
print(f"CUDA is available. Number of GPUs: {num_gpus}")

if num_gpus == 1:
    # Single GPU mode - simple utilization test
    print("Running in single GPU mode")
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    device = torch.device("cuda:0")
    
    print(f"GPU 0: {torch.cuda.get_device_name(0)}")
    print(f"  Memory Allocated: {torch.cuda.memory_allocated(0) / 1024**2:.2f} MB")
    print(f"  Memory Cached: {torch.cuda.memory_reserved(0) / 1024**2:.2f} MB")
    
    # Create data on GPU
    x = torch.linspace(0, 4, 16*1024**2).cuda()
    
    # Main loop for single GPU
    try:
        iteration = 0
        start_time = time.time()
        end_time = start_time + DURATION
        
        while time.time() < end_time:
            x = x * (1.0 - x)
            
            # Log stats periodically
            if iteration % 5000 == 0:
                time_elapsed = time.time() - start_time
                util = get_gpu_utilization(handle)
                mem_util = get_gpu_memory_utilization(handle)
                max_val = x.max().item()
                
                print(f"\nIteration {iteration}:")
                print(f"Time elapsed: {format_time(time_elapsed)}")
                print(f"Max value: {max_val:.6e}")
                print(f"GPU Utilization: {util*100:.1f}%")
                print(f"Memory Usage: {mem_util*100:.1f}%")
                
                if wandb_logger:
                    wandb.log({
                        "iteration_number": iteration,
                        "max_value": max_val,
                        "time_elapsed": time_elapsed,
                        "gpu_util": util,
                        "gpu_mem": mem_util
                    })
            
            iteration += 1
            
    except KeyboardInterrupt:
        print("\nStopping the run...")

else:
    # Multi-GPU mode - check NVLink support first
    print("Running in multi-GPU mode")
    
    # Initialize GPU handles and devices
    gpu_handles = []
    devices = []
    nvlink_supported = False
    
    # Check NVLink support between all GPU pairs
    for i in range(num_gpus):
        handle = pynvml.nvmlDeviceGetHandleByIndex(i)
        gpu_handles.append(handle)
        devices.append(torch.device(f"cuda:{i}"))
        print(f"\nGPU {i}: {torch.cuda.get_device_name(i)}")
        print(f"  Memory Allocated: {torch.cuda.memory_allocated(i) / 1024**2:.2f} MB")
        print(f"  Memory Cached: {torch.cuda.memory_reserved(i) / 1024**2:.2f} MB")
        
        # Check NVLink support
        for j in range(num_gpus):
            if i != j:
                if check_nvlink_support(handle, j):
                    nvlink_supported = True
                    print(f"  NVLink supported to GPU {j}")
                else:
                    print(f"  NVLink not supported to GPU {j}")
    
    if nvlink_supported:
        print("\nNVLink testing enabled")
    else:
        print("\nNVLink not supported - running in PCIe mode only")
    
    # Create data on each GPU
    gpu_tensors = []
    for i in range(num_gpus):
        with torch.cuda.device(i):
            tensor = torch.linspace(0, 4, 16*1024**2).cuda()
            gpu_tensors.append(tensor)
    
    # Initialize transfer monitoring
    last_rx_tx = {i: {j: (0, 0) for j in range(num_gpus) if i != j} for i in range(num_gpus)}
    transfer_timer = None
    
    def transfer_monitor():
        global transfer_timer
        for i in range(num_gpus):
            for j in range(num_gpus):
                if i != j:
                    transfer_time = transfer_data_gpu_to_gpu(i, j, TRANSFER_SIZE_MB)
                    print(f"\nTransfer from GPU{i} to GPU{j}: {transfer_time:.4f}s")
                    
                    if nvlink_supported:
                        rx, tx = get_nvlink_stats(gpu_handles[i], j)
                        last_rx, last_tx = last_rx_tx[i][j]
                        rx_diff = rx - last_rx
                        tx_diff = tx - last_tx
                        print(f"NVLink stats GPU{i}->GPU{j}: RX diff={rx_diff}, TX diff={tx_diff}")
                        last_rx_tx[i][j] = (rx, tx)
        
        transfer_timer = threading.Timer(TRANSFER_INTERVAL, transfer_monitor)
        transfer_timer.start()
    
    # Main loop for multi-GPU
    try:
        iteration = 0
        start_time = time.time()
        warmup_end_time = start_time + WARMUP_DURATION
        end_time = start_time + DURATION
        
        # Start transfer monitoring
        transfer_monitor()
        
        while time.time() < end_time:
            # Perform computation on each GPU
            for i, tensor in enumerate(gpu_tensors):
                with torch.cuda.device(i):
                    tensor.mul_(1.0 - tensor)
            
            # Log stats periodically
            if iteration % 5000 == 0:
                time_elapsed = time.time() - start_time
                
                # Get GPU stats using pynvml
                for i, handle in enumerate(gpu_handles):
                    util = get_gpu_utilization(handle)
                    mem_util = get_gpu_memory_utilization(handle)
                    max_val = gpu_tensors[i].max().item()
                    
                    print(f"\nIteration {iteration}, GPU {i}:")
                    print(f"Time elapsed: {format_time(time_elapsed)}")
                    print(f"Max value: {max_val:.6e}")
                    print(f"GPU Utilization: {util*100:.1f}%")
                    print(f"Memory Usage: {mem_util*100:.1f}%")
                    
                    if wandb_logger:
                        wandb.log({
                            "iteration_number": iteration,
                            f"gpu_{i}_max_value": max_val,
                            "time_elapsed": time_elapsed,
                            f"gpu_{i}_util": util,
                            f"gpu_{i}_mem": mem_util
                        })
            
            iteration += 1
            
    except KeyboardInterrupt:
        print("\nStopping the run...")
    
    finally:
        if transfer_timer:
            transfer_timer.cancel()

if wandb_logger:
    wandb.finish()
pynvml.nvmlShutdown() 