# https://medium.com/@gauravvij/want-to-benchmark-your-gpus-for-deep-learning-3266d7703f7f
#
# https://catalog.ngc.nvidia.com/orgs/nvidia/containers/cuda/tags
FROM nvcr.io/nvidia/cuda:12.6.1-base-ubuntu24.04
RUN git clone https://github.com/linux-rdma/perftest && \
    cd perftest/ && \
    ./autogen.sh && \
    ./configure && \
    make && \
    make install

# Benchmarking
RUN nvidia-smi cuda-benchmarks

# GPU utilization
RUN nvidia-smi --query-gpu=utilization.gpu --format=csv

# GPU memory allocation
RUN nvidia-smi --query-gpu=memory.total,memory.used --format=csv

# temperature
RUN nvidia-smi --query-gpu=temperature.gpu --format=csv

# power usage
RUN nvidia-smi --query-gpu=power.draw --format=csv

# I/O and Throughput for InfiniBand:
RUN ib_write_bw -d mlx5_0 -a

# CUDA BandwidthTest:
RUN bandwidthTest

# Criteria for Evaluation:
# - GPU Utilization: High utilization indicates efficient use of the GPU.
# - Memory Usage: Keep an eye on both GPU memory usage and overall allocation.
# - Temperature and Power Consumption: Track these to ensure your GPU is not overheating or drawing excessive power.
# - I/O and Throughput: Measure bandwidth (for both PCIe and InfiniBand if available), which will help determine data transfer efficiency between components.

# Additional Metrics:
# - Latency: If your benchmark tools support it, latency measurements can provide insight into how quickly the GPU responds to tasks.
# - Error Rates: Especially in cases where workloads are very intensive, error rates or retries in the I/O system can indicate performance degradation.
