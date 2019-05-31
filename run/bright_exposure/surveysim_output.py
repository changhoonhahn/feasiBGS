#!/bin/python 
'''
scripts to check outputs from hacked surveysim  
'''
import os 
import numpy as np 
import desisurvey.etc as detc
# --- astropy --- 
import astropy.units as u
from astropy.io import fits
# -- feasibgs -- 
from feasibgs import util as UT
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


def extractBGS(fname, notwilight=True): 
    """ extra data on bgs exposures from surveysim output 

    no cosmics split adds 20% to margin
    total BGS time: 2839 hours
    total BGS minus twilight: 2372
    assuming 7.5 deg^2 per field
    assumiong 68% open-dome fraction
    """
    total_hours = 2839
    if notwilight: total_hours = 2372

    open_hours = total_hours*0.68
    
    ssout = fits.open(fname)[1].data # survey sim output 
    tiles = fits.open(os.path.join(UT.dat_dir(), 'bright_exposure', 'desi-tiles.fits'))[1].data # desi-tiles
    
    isbgs = (tiles['PROGRAM'] == 'BRIGHT') # only bgs 
    
    uniq_tiles, iuniq = np.unique(ssout['TILEID'], return_index=True)  
    print('%i unique tiles out of %i total exposures' % (len(uniq_tiles), len(ssout['TILEID'])))

    _, ssbgs, bgsss = np.intersect1d(ssout['TILEID'][iuniq], tiles['TILEID'][isbgs], return_indices=True)  
    print('%i total BGS fields: ' % len(ssbgs))
    print('approx. BGS coverage [#passes]: %f' % (float(len(ssbgs)) * 7.5 / 14000.)) 
    
    exps = {
        'nexp':     np.zeros(len(ssbgs)).astype(int),
        'texptot':  np.zeros(len(ssbgs)),
        'texps':    np.zeros((len(ssbgs), 25)), 
        'snr2max':  np.zeros(len(ssbgs)),
        'snr2arr':  np.zeros((len(ssbgs), 25)), 
        'ra':       np.zeros(len(ssbgs)), 
        'dec':      np.zeros(len(ssbgs)),
        'mjd':      np.zeros((len(ssbgs), 25)),
        'airmass':  np.zeros((len(ssbgs), 25)),
        'seeing':   np.zeros((len(ssbgs), 25)),
        'transp':   np.zeros((len(ssbgs), 25))
    }

    for i in range(len(ssbgs)): 
        isexps = (ssout['TILEID'] == ssout['TILEID'][iuniq][ssbgs[i]]) 
        nexp = np.sum(isexps)

        exps['nexp'][i]         = nexp
        exps['texps'][i,:nexp]  = ssout['EXPTIME'][isexps] 
        exps['texptot'][i]      = np.sum(ssout['EXPTIME'][isexps]) 
        exps['snr2max'][i]      = np.max(ssout['SNR2FRAC'][isexps]) 
        exps['snr2arr'][i,:nexp]= ssout['SNR2FRAC'][isexps]
        exps['ra'][i]           = tiles['RA'][isbgs][bgsss[i]]
        exps['dec'][i]          = tiles['DEC'][isbgs][bgsss[i]]
        exps['mjd'][i,:nexp]    = ssout['MJD'][isexps]
        exps['airmass'][i,:nexp]= ssout['AIRMASS'][isexps]
        exps['seeing'][i,:nexp] = ssout['SEEING'][isexps]
        exps['transp'][i,:nexp] = ssout['TRANSP'][isexps]
    #print(exps['texptot'].max()) 
    #pickle.dump(exps, open('bgs.%s.p' % os.path.basename(fname).strip('.fits'), 'wb'))
    return exps 


def surveysim_output(): 
    ''' read in surveysim output that Jeremy provided and check the exposures
    with super high exptime. 
    '''
    # read in exposures output from surveysim 
    #fexp = os.path.join(UT.dat_dir(), 'bright_exposure', 'exposures_surveysim.fits') 
    #fexp = os.path.join(UT.dat_dir(), 'bright_exposure', 'exposures_surveysim_master.fits')
    fexp = os.path.join(UT.dat_dir(), 'bright_exposure', 'exposures_surveysim_fork_nocorr.fits') 
    exps = extractBGS(fexp) 
    
    nexp    = exps['nexp']
    ra      = exps['ra']
    dec     = exps['dec']
    mjds    = exps['mjd'] 
    texptot = exps['texptot']  
    texps   = exps['texps']  
    snr2max = exps['snr2max'] 
    snr2arr = exps['snr2arr']
    airmass = exps['airmass'] 
    seeing  = exps['seeing']
    print('')  
    print('tile exposures for the longest time has...')
    print('texp=%f' % (texptot.max()/60.)) 
    print('nexp=%i' % nexp[np.argmax(texptot)]) 
    print('texps=', texps[np.argmax(texptot),:nexp[np.argmax(texptot)]]) 
    print('airmass=', airmass[np.argmax(texptot),:nexp[np.argmax(texptot)]])  
    print('seeing=', seeing[np.argmax(texptot),:nexp[np.argmax(texptot)]])  
    print('')  

    superhigh = (texptot > 60*60.) # tiles exposed for longer than 60 mins 
    print('%i exposures with very high exposure times' % np.sum(superhigh)) 
    for i in np.arange(len(texptot))[superhigh]: 
        # get sky parameters for given ra, dec, and mjd
        moon_ill, moon_alt, moon_sep, sun_alt, sun_sep = get_thetaSky(
            np.repeat(ra[i], nexp[i]), 
            np.repeat(dec[i], nexp[i]), 
            mjds[i,:nexp[i]])
        exp_factor = np.array([detc.bright_exposure_factor(moon_ill[_i], moon_alt[_i], np.array([moon_sep[_i]]), 
                                                  np.array([sun_alt[_i]]), np.array([sun_sep[_i]]), np.array([airmass[i,_i]])) 
                      for _i in range(nexp[i])]).flatten() 
        print('---') 
        print(exp_factor)
        print(texps[i,:nexp[i]])
        print(snr2arr[i,:nexp[i]])
    raise ValueError
    
    # exposures longer than 30 mins 
    superhigh = (texp > 30.*60.) 
    print('%i exposures with very high exposure times' % np.sum(superhigh)) 
    exp_factor = np.array([detc.bright_exposure_factor(moon_ill[i], moon_alt[i], np.array([moon_sep[i]]), 
                                              np.array([sun_alt[i]]), np.array([sun_sep[i]]), np.array([airm[i]])) 
                  for i in range(len(moon_ill))])
    print(exp_factor.flatten()[superhigh]) 
    print(texp[superhigh]) 

    fig = plt.figure(figsize=(20, 5)) 
    # moon: alt vs ill
    sub = fig.add_subplot(141) 
    sub.scatter(moon_alt, moon_ill, c='k', s=1) 
    sub.scatter(moon_alt[superhigh], moon_ill[superhigh], c='C1', s=5) 
    sub.set_xlabel('Moon Altitude', fontsize=20)
    sub.set_xlim([-90., 90.])
    sub.set_ylabel('Moon Illumination', fontsize=20)
    sub.set_ylim([0., 1.])
    # moon: sep vs ill
    sub = fig.add_subplot(142) 
    sub.scatter(moon_sep, moon_ill, c='k', s=1) 
    sub.scatter(moon_sep[superhigh], moon_ill[superhigh], c='C1', s=5) 
    sub.set_xlabel('Moon Separation', fontsize=20)
    sub.set_xlim([0., 180.])
    sub.set_ylabel('Moon Illumination', fontsize=20)
    sub.set_ylim([0., 1.])
    # sun: alt vs sep 
    sub = fig.add_subplot(143) 
    sub.scatter(sun_alt, sun_sep, c='k', s=1) 
    sub.scatter(sun_alt[superhigh], sun_sep[superhigh], c='C1', s=5) 
    sub.set_xlabel('Sun Altitude', fontsize=20)
    sub.set_xlim([-90., 0.])
    sub.set_ylabel('Sun Separation', fontsize=20)
    sub.set_ylim([40., 180.])
    # airmass 
    sub = fig.add_subplot(144) 
    sub.scatter(sun_alt, airm, c='k', s=1) 
    sub.scatter(sun_alt[superhigh], airm[superhigh], c='C1', s=5) 
    sub.set_xlabel('Sun Altitude', fontsize=20)
    sub.set_xlim([-90., 0.])
    sub.set_ylabel('Airmass', fontsize=20)
    sub.set_ylim([0.9, 2.])

    fig.savefig(fexp.replace('.fits', '.png'), bbox_inches='tight') 
    return None 


def get_thetaSky(ra, dec, mjd) : 
    ''' given RA, Dec, and mjd time return sky parameters at kitt peak 
    '''
    import ephem 
    from astropy.time import Time
    import desisurvey.config
    import desisurvey.utils as dutils
    config = desisurvey.config.Configuration()

    mayall = ephem.Observer()
    mayall.lat = config.location.latitude().to(u.rad).value
    mayall.lon = config.location.longitude().to(u.rad).value
    mayall.elevation = config.location.elevation().to(u.m).value
    # Configure atmospheric refraction model for rise/set calculations.
    mayall.pressure = 1e3 * config.location.pressure().to(u.bar).value
    mayall.temp = config.location.temperature().to(u.C).value

    # observed time (MJD) 
    mjd_time = Time(mjd, format='mjd')

    moon_alt    = np.zeros(len(mjd))
    moon_ra     = np.zeros(len(mjd))
    moon_dec    = np.zeros(len(mjd)) 
    moon_ill    = np.zeros(len(mjd))
    sun_alt     = np.zeros(len(mjd))
    sun_ra      = np.zeros(len(mjd))
    sun_dec     = np.zeros(len(mjd)) 
    for i in range(len(mjd)):
        mayall.date = mjd_time.datetime[i] 
        _moon = ephem.Moon()
        _moon.compute(mayall) 
        _sun = ephem.Sun()
        _sun.compute(mayall) 
        
        moon_alt[i] = 180./np.pi*_moon.alt
        moon_ra[i]  = 180./np.pi*_moon.ra
        moon_dec[i] = 180./np.pi*_moon.dec
        moon_ill[i] = _moon.moon_phase
        sun_alt[i] = 180./np.pi*_sun.alt
        sun_ra[i]  = 180./np.pi*_sun.ra
        sun_dec[i] = 180./np.pi*_sun.dec

    moon_sep    = np.diag(dutils.separation_matrix(moon_ra, moon_dec, np.atleast_1d(ra), np.atleast_1d(dec)))
    sun_sep     = np.diag(dutils.separation_matrix(sun_ra, sun_dec, np.atleast_1d(ra), np.atleast_1d(dec)))
    return moon_ill, moon_alt, moon_sep, sun_alt, sun_sep


if __name__=="__main__": 
    surveysim_output()
