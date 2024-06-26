## Compile OpenMM and MELD in HiPerGator, a step by step guide

### Brief introduction of OpenMM and MELD
OpenMM is a molecular dynamics simulation toolkit that allows users to introduce new features including new forces and new functional forms, new integration algorithm and new simulation protocols. Those features automatically work on all supported hardware types including CPUs and GPUs and show excellent performance. The source code of OpenMM is mostly composed of C++, C, Python, and CUDA. In order to compile OpenMM in HiPerGator, we need to find the right compilers that can work for the version of the OpenMM downloaded, if older versions of compilers are used, then it will likely cause bugs like variables not defined, or library not existed error. MELD has two parts: MELD-plugin (C/C++, CUDA) to install in OpenMM as external library and python API for users to define simulation parameters.

Here are the steps:
- [setup python virtual environment](#set-up-python-virtual-env) ->
- [compile OpenMM(version 8.1.0.dev-432b583) and test](#openmm-compilation) ->
- [compile Meld-plugin (c++/cuda, version 0.6.1) in OpenMM](#meld-plugin-compilation) ->
- [install Meld python interface in python virtual env and test](#meld-api-installation)

#### Prerequisite: enter a clean environment
Request and enter in a gpu node: 

```srun --nodes=1 --partition=gpu  --gres=gpu:a100:1 --mem-per-cpu 500mb -t 12:00:00 --pty /bin/bash -i``` and `cd /home/program/` 
Assuming we are working in `/home/program/` and no modules loaded now by `module list` and deactivate auto-loaded envs such as conda environment;

### Set up python virtual env

`module load python/3.11` and `python -m venv --system-site-packages Meld`, where Meld is the env name.

Activate virtual env with `source /home/program/Meld/bin/activate ` and set `PYTHONPATH` with
```bash
export PYTHONPATH=/home/program/Meld/lib/python3.11/site-packages/:$PYTHONPATH
```

`export LC_ALL=C` is needed if not set (The "C" locale turns off all internationalization, status/error messages in English, there is no distinction between characters and bytes, sorting is by raw byte values.)

### OpenMM compilation
Now we introduce the modules required for compilation for both OpenMM and MELD.
- ufrc (for HiPerGator) 
- doxygen/1.8.3.1 (documentation generator) 
- gcc/9.3.0 (the GNU compiler collection for C/C++ and others) 
- cmake/3.26.4 (generates build files from all CMakeLists.text) 
- netcdf/4.2 (network Common Data Form, is a set of software libraries and machine-independent data formats that support the creation, access, and sharing of array-oriented scientific data.) 
- ucx/1.15.0 (Unified Communication X, is an award winning, optimized production-proven communication framework for modern, high-bandwidth and low-latency networks.)  
- swig/3.0.8 (Simplified Wrapper and Interface Generator, is an open-source software tool used to connect computer programs or libraries written in C or C++ with scripting languages such as Python.)  
- cuda/11.4.3 (API that allows software to use certain types of GPU, gives direct access to the GPU\'s virtual instruction set and parallel computational elements for the execution of compute kernels.) 
- openmpi/4.1.5 (Message passing interface library for parallel process communication)

```bash
module load ufrc gcc/12.2.0 cuda/12.2 gcc/9.3.0 cmake/3.26.4 doxygen/1.8.3.1 cuda/11.4.3 openmpi/4.1.5 swig/3.0.8  netcdf/4.2
```

Download `OpenMM` from their repository by `cd OpenMM_cuda12; git clone https://github.com/openmm/openmm openmm` and `cd /home/program/OpenMM_cuda12`, the `openmm` folder should be downloaded inside.  Create a build folder with `mkdir build_cuda12; cd build_cuda12` and run the following cmd to build install files for OpenMM

```bash
cmake -DCMAKE_INSTALL_PREFIX:PATH=/home/program/OpenMM_cuda12/bin_cuda12/ -DOPENMM_DIR:PATH=/home/program/OpenMM_cuda12/bin_cuda12/ -DOPENMM_CUDA_COMPILER:PATH=/apps/compilers/cuda/12.2.0/bin/nvcc -DCUDA_CUDA_LIBRARY=/apps/compilers/cuda/12.2.0/lib64/stubs/libcuda.so ../openmm/
```

Then make and install with `make -j8; make -j8 install;`
There will probably be an error for `CommonCalcGayBerneForceKernel` due to the version of gcc compiler, we can load `cuda/11.4.3 gcc/9.3.0` 
then make and install again with `make -j8; make -j8 install;` to pass the rest of the build.
And install `Cython` with `pip install Cython` before building python part with `make PythonInstall`.

### Test the installation of OpenMM
```python
python -m openmm.testInstallation
```

### MELD plugin compilation
Similarly, download `meld` with `git clone https://github.com/maccallumlab/meld.git meld_cuda12` and `cd meld_cuda12/plugin/; mkdir build_cuda12`, then build plugin with
```bash
cmake -DCMAKE_INSTALL_PREFIX:PATH=/home/liweichang/program/OpenMM_cuda12/bin_cuda12/ -DOPENMM_DIR:PATH=/home/program/OpenMM_cuda12/bin_cuda12/ ../
``` 

and `make -j8; make -j8 install; make PythonInstall`

### MELD API installation
Then go back to the folder that has `setup.py` `cd ../../meld_cuda12/`, install required softwares with `pip install netCDF4 mrcfile ParmEd mdtraj`, finally `python setup.py install` will install MELD python APIs in current env. You can test the installation by simply `import meld`, `import openmm` and then run a test with `meld` setup file `system_setup.py`.

