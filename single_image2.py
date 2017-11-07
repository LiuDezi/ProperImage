#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  single_image2.py
#
#  Copyright 2017 Bruno S <bruno@oac.unc.edu.ar>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
"""single_image module from ProperImage,
for coadding astronomical images.

Written by Bruno SANCHEZ

PhD of Astromoy - UNC
bruno@oac.unc.edu.ar

Instituto de Astronomia Teorica y Experimental (IATE) UNC
Cordoba - Argentina

Of 301
"""

import os

from six.moves import range

import numpy as np
from numpy import ma

from scipy import signal as sg

from astropy.io import fits
from astropy.stats import sigma_clip
from astropy.modeling import fitting
from astropy.modeling import models
from astropy.convolution import convolve  # _fft, convolve
from astropy.nddata.utils import extract_array

import sep

from . import numpydb as npdb
#from . import utils
from .image_stats import ImageStats

try:
    import pyfftw
    _fftwn = pyfftw.interfaces.numpy_fft.fft2
    _ifftwn = pyfftw.interfaces.numpy_fft.ifft2
except:
    _fftwn = np.fft.rfft2
    _ifftwn = np.fft.rifft2


class Bunch(dict):

    def __dir__(self):
        return self.keys()

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(attr)


class SingleImage(object):
    """Atomic processor class for a single image.
    Contains several tools for PSF measures, and different coadding
    building structures.

    It includes the pixel matrix data, as long as some descriptions.
    For statistical values of the pixel matrix the class' methods need to be
    called.


    Parameters
    ----------
    img : `~numpy.ndarray` or :class:`~ccdproc.CCDData`,
                `~astropy.io.fits.HDUList`  or a `str` naming the filename.
        The image object to work with

    mask: `~numpy.ndarray` or a `str` naming the filename.
        The mask image
    """

    def __init__(self, img=None, mask=None):
        self.attached_to = img
        self.zp = 1.
        self.imagedata = img
        self.dbname = os.path.abspath('._'+str(id(self))+'SingleImage')
        self.mask = mask

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._clean()

    def __repr__(self):
        return 'SingleImage instance for {}'.format(self.attached_to)

    def _clean(self):
        print('cleaning... ')
        try:
            os.remove(self.dbname+'.dat')
            os.remove(self.dbname+'.map')
        except:
            print('Nothing to clean. (Or something has failed)')

    @property
    def attached_to(self):
        return self.__attached_to
    @attached_to.setter
    def attached_to(self, img):
        if type(img) is str:
            self.__attached_to = img
        else:
            self.__attached_to = img.__class__.__name__

    @property
    def imagedata(self):
        return self.__imagedata
    @imagedata.setter
    def imagedata(self, img):
        if isinstance(img, str):
            pixeldata = fits.getdata(img)
            header = fits.getheader(img)
            self.__imagedata = Bunch({'pixeldata': ma.asarray(pixeldata)})
            self.__imagedata['header'] = header
        elif isinstance(img, np.ndarray):
            self.__imagedata = {'pixeldata': img}

    @property
    def pixeldata(self):
        return self.imagedata['pixeldata'].data
    @property
    def pixelmasked(self):
        return self.imagedata['pixeldata']
    @property
    def header(self):
        return self.imagedata['header']

    @property
    def mask(self):
        return self.__imagedata['pixeldata'].mask
    @mask.setter(self, mask):
    def mask(self, mask):
        if isinstance(mask, str):
            self.__imagedata['pixeldata'].mask = fits.getdata(mask)
        elif mask is None:
            mask = ma.masked_invalid(self.__imagedata['pixeldata'].data)
            self.__imagedata['pixeldata'].mask = mask.mask

    @property
    def background(self):
        """Image background subtracted property of SingleImage.
        The background is estimated using sep.

        Returns
        -------
        numpy.array 2D
            a background subtracted image is returned

        """
        return self.imagedata['background']

    @background.setter
    def background(self, maskthresh=None)
        if maskthresh is not None:
            back = sep.Background(self.pixeldata,
                                  mask=self.mask,
                                  maskthresh=maskthresh)
            self.__imagedata['background'] = back
        else:
            back = sep.Background(self.pixeldata,
                                  mask=self.mask)
            self.__imagedata['background'] = back
        return self._bkg_sub_img

