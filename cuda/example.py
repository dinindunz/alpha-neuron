import pycuda.driver as cuda
import pycuda.autoinit
from pycuda.compiler import SourceModule
import numpy as np

# Define CUDA kernel
mod = SourceModule("""
__global__ void add_arrays(float *a, float *b, float *c, int n) {
    int idx = threadIdx.x + blockIdx.x * blockDim.x;
    if (idx < n) {
        c[idx] = a[idx] + b[idx];
    }
}
""")

# Define arrays
n = 256
a = np.random.randn(n).astype(np.float32)
b = np.random.randn(n).astype(np.float32)
c = np.zeros_like(a)

# Allocate memory on the GPU
a_gpu = cuda.mem_alloc(a.nbytes)
b_gpu = cuda.mem_alloc(b.nbytes)
c_gpu = cuda.mem_alloc(c.nbytes)

# Copy data to GPU
cuda.memcpy_htod(a_gpu, a)
cuda.memcpy_htod(b_gpu, b)

# Launch kernel
block_size = 32
grid_size = (n + block_size - 1) // block_size
add_arrays = mod.get_function("add_arrays")
add_arrays(a_gpu, b_gpu, c_gpu, np.int32(n), block=(block_size, 1, 1), grid=(grid_size, 1, 1))

# Copy result back to CPU
cuda.memcpy_dtoh(c, c_gpu)
print("Result:", c)
