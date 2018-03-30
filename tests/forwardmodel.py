'''

Test `feasibgs.forwardmodel`


'''
import numpy as np 
from astropy.cosmology import FlatLambdaCDM

# -- local -- 
import env
from feasibgs import util as UT
from feasibgs import catalogs as Cat 
from feasibgs import forwardmodel as FM

# -- plotting --
import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.rcParams['text.usetex'] = True
mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['axes.linewidth'] = 1.5
mpl.rcParams['axes.xmargin'] = 1
mpl.rcParams['xtick.labelsize'] = 'x-large'
mpl.rcParams['xtick.major.size'] = 5
mpl.rcParams['xtick.major.width'] = 1.5
mpl.rcParams['ytick.labelsize'] = 'x-large'
mpl.rcParams['ytick.major.size'] = 5
mpl.rcParams['ytick.major.width'] = 1.5
mpl.rcParams['legend.frameon'] = False


def GamaLegacy_matchSpectra(): 
    ''' match galaxies from the GAMA-Legacy catalog to 
    BGS templates and then plot their spectra
    '''
    # read in GAMA-Legacy catalog 
    cata = Cat.GamaLegacy()
    gleg = cata.Read()

    redshift = gleg['gama-spec']['z_helio']  # redshift
    absmag_ugriz = cata.AbsMag(gleg, kcorr=0.1, H0=70, Om0=0.3) # ABSMAG k-correct to z=0.1 
    
    # BGS templates
    bgs3 = FM.BGStree() 
    bgstemp = FM.BGStemplates(wavemin=1500.0, wavemax=2e4)
    mabs_temp = bgs3.meta['SDSS_UGRIZ_ABSMAG_Z01'] # template absolute magnitude 

    # pick 10 random galaxies from the GAMA-legacy sample
    # and then find the closest template
    i_rand = np.random.choice(range(absmag_ugriz.shape[1]), size=10) 
    
    # meta data of [z, M_r0.1, 0.1(g-r)]
    gleg_meta = np.vstack([
        redshift[i_rand], 
        absmag_ugriz[2,i_rand], 
        absmag_ugriz[1,i_rand] - absmag_ugriz[2,i_rand]]).T
    match, _ = bgs3.Query(gleg_meta)
    
    # velocity dispersion 
    vdisp = np.repeat(100.0, len(i_rand)) # [km/s]
    
    flux, wave, meta = bgstemp.Spectra(
            gleg['gama-photo']['modelmag_r'][i_rand], 
            redshift[i_rand], 
            vdisp,
            seed=1, templateid=match, silent=False) 
    
    fig = plt.figure(figsize=(12,6))
    sub1 = fig.add_subplot(121)
    sub2 = fig.add_subplot(122)
    sub1.scatter(absmag_ugriz[2,:], absmag_ugriz[1,:] - absmag_ugriz[2,:], c='k', s=2) 
    for ii, i in enumerate(i_rand): 
        sub1.scatter(mabs_temp[match[ii],2], mabs_temp[match[ii],1] - mabs_temp[match[ii],2],
                color='C'+str(ii), s=30, edgecolors='k', marker='^', label='Template')
        sub1.scatter(absmag_ugriz[2,i], absmag_ugriz[1,i] - absmag_ugriz[2,i], 
                color='C'+str(ii), s=30, edgecolors='k', marker='s', label='GAMA object')
        if ii == 0: 
            sub1.legend(loc='lower left', markerscale=3, handletextpad=0., prop={'size':20})

        # plot template spectra
        sub2.plot(wave, flux[ii], c='C'+str(ii)) 
    sub1.set_xlabel('$M_{0.1r}$', fontsize=20) 
    sub1.set_xlim([-14., -24]) 
    sub1.set_ylim([-0.2, 1.2])
    sub2.set_xlabel('wavelength', fontsize=20) 
    sub2.set_xlim([1.5e3, 2e4]) 
    sub2.set_ylim([0., 25.]) 
    fig.savefig(UT.fig_dir()+"GamaLegacy_matchSpectra.png", bbox_inches='tight')
    plt.close() 
    return None


def matchGamaLegacy(): 
    ''' match galaxies from the GAMA-Legacy catalog to 
    BGS templates and compare the meta data 
    '''
    # read in GAMA-Legacy catalog 
    cata = Cat.GamaLegacy()
    gleg = cata.Read()

    redshift = gleg['gama-spec']['z_helio']  # redshift

    # calculate ABSMAG k-correct to z=0.1 
    absmag_ugriz = cata.AbsMag(gleg, kcorr=0.1, H0=70, Om0=0.3) 
    
    # BGS templates
    bgs3 = FM.BGStree() 
    mabs_temp = bgs3.meta['SDSS_UGRIZ_ABSMAG_Z01'] # absolute magnitude 

    fig = plt.figure(figsize=(12,6))
    sub = fig.add_subplot(121)
    sub.scatter(absmag_ugriz[2,:], absmag_ugriz[1,:] - absmag_ugriz[2,:], 
            c='k', s=2, label='GAMA object') 
    sub.scatter(mabs_temp[:,2], mabs_temp[:,1] - mabs_temp[:,2], 
            c='C0', s=2, label='Template') 
    sub.legend(loc='lower left', markerscale=5, handletextpad=0, prop={'size': 15}) 
    sub.set_xlabel('$M_{0.1r}$', fontsize=20) 
    sub.set_xlim([-14., -24]) 
    sub.set_ylabel('$^{0.1}(g-r)$', fontsize=20) 
    sub.set_ylim([-0.2, 1.2])

    # pick 10 random galaxies from the GAMA-legacy sample
    # and then find the closest template
    i_rand = np.random.choice(range(absmag_ugriz.shape[1]), size=10) 
    
    # meta data of [z, M_r0.1, 0.1(g-r)]
    gleg_meta = np.vstack([
        redshift[i_rand], 
        absmag_ugriz[2,i_rand], 
        absmag_ugriz[1,i_rand] - absmag_ugriz[2,i_rand]]).T
    match, _ = bgs3.Query(gleg_meta)
    
    sub = fig.add_subplot(122)
    for ii, i in enumerate(i_rand): 
        sub.scatter(mabs_temp[match[ii],2], mabs_temp[match[ii],1] - mabs_temp[match[ii],2],
                color='C'+str(ii), s=30, linewidth=0, marker='^', label='Template')
        sub.scatter(absmag_ugriz[2,i], absmag_ugriz[1,i] - absmag_ugriz[2,i], 
                color='C'+str(ii), s=30, linewidth=0, marker='s', label='GAMA object')
        sub.plot([mabs_temp[match[ii],2], mabs_temp[match[ii],1] - mabs_temp[match[ii],2]],
                [absmag_ugriz[2,i], absmag_ugriz[1,i] - absmag_ugriz[2,i]], 
                color='C'+str(ii))
        if ii == 0: sub.legend(loc='lower left', prop={'size':20})
    sub.set_xlabel('$M_{0.1r}$', fontsize=20) 
    sub.set_xlim([-14., -24]) 
    sub.set_ylim([-0.2, 1.2])
    fig.savefig(UT.fig_dir()+"matchGamaLegacy.png", bbox_inches='tight')
    plt.close() 
    return None


def BGStemplates(): 
    ''' An attempt to better understand the BGS templates
    '''
    bgs3 = FM.BGStree() 
    
    fig = plt.figure(figsize=(12,6))
    # redshift distribution of the templates 
    sub1 = fig.add_subplot(121) 
    _ = sub1.hist(bgs3.meta['Z'], bins=50, range=(0., 1.), histtype='stepfilled')
    sub1.set_xlabel('Redshift', fontsize=20) 
    sub1.set_xlim([0., 0.8]) 
    
    # M_r0.1 vs (g-r)0.1 of the templates
    Mabs = bgs3.meta['SDSS_UGRIZ_ABSMAG_Z01'] # absolute magnitude 

    sub2 = fig.add_subplot(122)
    sub2.scatter(Mabs[:,2], Mabs[:,1] - Mabs[:,2], c='k', s=2) 
    sub2.set_xlabel(r'$M_{0.1r}$', fontsize=20)
    sub2.set_xlim([-14., -24.]) 
    sub2.set_ylabel(r'$^{0.1}(g - r)$', fontsize=20)
    sub2.set_ylim([-0.2, 1.3]) 
    fig.subplots_adjust(wspace=0.3) 
    fig.savefig(UT.fig_dir()+"BGStemplates.png", bbox_inches='tight')
    plt.close() 
    return None


if __name__=="__main__": 
    GamaLegacy_matchSpectra()
