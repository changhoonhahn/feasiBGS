#!/bin/bash/

dir_spec="/Users/ChangHoon/data/feasiBGS/spectra/gamadr3_legacydr7/"

export OMP_NUM_THREADS=1 

for skymodel in "KS" "newKS"; do 
    f_str="g15.sim_spectra.mockexp_block.480.iexp0."$skymodel"sky"
    f_spec=$dir_spec$f_str".fits"
    f_redr=$dir_spec$f_str".rr.fits"
    f_zout=$dir_spec$f_str".rr.h5"

    rrdesi --mp 4 --zbest $f_redr --output $f_zout $f_spec
done