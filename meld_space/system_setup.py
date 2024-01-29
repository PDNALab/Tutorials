#!/usr/bin/env python
# encoding: utf-8
import numpy as np
import meld
from meld import system
from meld.comm import MPICommunicator
from meld import comm, vault
from meld import system
from meld.remd import ladder, adaptor, leader
from meld.system.scalers import LinearRamp,ConstantRamp
import openmm.unit as  u

N_REPLICAS = 2
N_STEPS = 5
BLOCK_SIZE = 1
def gen_state_templates(index, templates):                                           

    n_templates = len(templates)
    print((index,n_templates,index%n_templates))
    a = system.subsystem.SubSystemFromPdbFile(templates[index%n_templates])
    #Note that it does not matter which forcefield we use here to build
    #as that information is not passed on, it is used for all the same as
    #in the setup part of the script
    b = system.builder.SystemBuilder(forcefield="ff14sbside")
    c = b.build_system([a])
    pos = c._coordinates
    c._box_vectors=np.array([0.,0.,0.])
    vel = np.zeros_like(pos)
    alpha = 1 #index / (N_REPLICAS - 1.0)
    energy = 0
    return system.state.SystemState(pos, vel, alpha, energy,c._box_vectors)

def gen_state(s, index):
    state = s.get_state_template()
    state.alpha = index / (N_REPLICAS - 1.0)
    return state

def setup_system():
    template = "./1ake.pdb" 
    p = meld.AmberSubSystemFromPdbFile(template)
    build_options = meld.AmberOptions(
      forcefield="ff14sbside",
      implicit_solvent_model="gbNeck2",
      use_big_timestep=True,
      cutoff=1.8*u.nanometer
    )

    builder = meld.AmberSystemBuilder(build_options)
    s = builder.build_system([p]).finalize()
    s.temperature_scaler = meld.ConstantTemperatureScaler(300.0 * u.kelvin) 

    # create the options
    options = meld.RunOptions(
        timesteps = 10,
        minimize_steps = 0
    )

    # create a store
    store = vault.DataStore(gen_state(s,0), N_REPLICAS, s.get_pdb_writer(), block_size=BLOCK_SIZE)
    store.initialize(mode='w')
    store.save_system(s)
    store.save_run_options(options)
 
    # create and store the remd_runner
    l = ladder.NearestNeighborLadder(n_trials=100)
    policy = adaptor.AdaptationPolicy(2.0, 1, 1)
    a = adaptor.EqualAcceptanceAdaptor(n_replicas=N_REPLICAS, adaptation_policy=policy)
 
    remd_runner = leader.LeaderReplicaExchangeRunner(N_REPLICAS, max_steps=N_STEPS, ladder=l, adaptor=a)
    store.save_remd_runner(remd_runner)
 
    # create and store the communicator
    c = comm.MPICommunicator(s.n_atoms, N_REPLICAS)
    store.save_communicator(c)
 
    # create and save the initial states
    states = [gen_state(s, i) for i in range(N_REPLICAS)]                                  
    store.save_states(states, 0)
 
    # save data_store
    store.save_data_store()
 
 
setup_system()
