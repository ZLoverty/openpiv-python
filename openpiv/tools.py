#!/usr/bin/env python
"""The openpiv.tools module is a collection of utilities and tools.
"""

__licence__ = """
Copyright (C) 2011  www.openpiv.net

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import glob
import sys
import os.path
import multiprocessing

import numpy as np
import scipy.misc
import matplotlib.pyplot as pl
import matplotlib.patches as pt
import matplotlib.image as mpltimg



def display_vector_field( filename, on_img=False, image_name='None', window_size=32, scaling_factor=1, **kw):
    """ Displays quiver plot of the data stored in the file 
    
    
    Parameters
    ----------
    filename :  string
        the absolute path of the text file

    on_img : Bool, optional
        if True, display the vector field on top of the image provided by image_name

    image_name : string, optional
        path to the image to plot the vector field onto when on_img is True

    window_size : int, optional
        when on_img is True, provide the interogation window size to fit the background image to the vector field

    scaling_factor : float, optional
        when on_img is True, provide the scaling factor to scale the background image to the vector field
    
    Key arguments   : (additional parameters, optional)
        *scale*: [None | float]
        *width*: [None | float]
    
    
    See also:
    ---------
    matplotlib.pyplot.quiver
    
        
    Examples
    --------
    --- only vector field
    >>> openpiv.tools.display_vector_field('./exp1_0000.txt',scale=100, width=0.0025) 

    --- vector field on top of image
    >>> openpiv.tools.display_vector_field('./exp1_0000.txt', on_img=True, image_name='exp1_001_a.bmp', window_size=32, scaling_factor=70, scale=100, width=0.0025)
    
    """
    
    a = np.loadtxt(filename)
    fig=pl.figure()
    pl.hold(True)
    if on_img: # plot a background image
        im = imread(image_name)
        im = negative(im) #plot negative of the image for more clarity
        imsave('neg.jpg', im)
        im = mpltimg.imread('neg.jpg')
        xmax=np.amax(a[:,0])+window_size/(2*scaling_factor)
        ymax=np.amax(a[:,1])+window_size/(2*scaling_factor)
        implot = pl.imshow(im, origin='lower', cmap="Greys_r",extent=[0.,xmax,0.,ymax])
    invalid = a[:,4].astype('bool')
    fig.canvas.set_window_title('Vector field, '+str(np.count_nonzero(invalid))+' wrong vectors')
    valid = ~invalid
    pl.quiver(a[invalid,0],a[invalid,1],a[invalid,2],a[invalid,3],color='r',**kw)
    pl.quiver(a[valid,0],a[valid,1],a[valid,2],a[valid,3],color='b',**kw)
    pl.draw()
    pl.show()

def imread( filename, flatten=0 ):
    """Read an image file into a numpy array
    using scipy.misc.imread
    
    Parameters
    ----------
    filename :  string
        the absolute path of the image file
    flatten :   bool
        True if the image is RGB color or False (default) if greyscale
        
    Returns
    -------
    frame : np.ndarray
        a numpy array with grey levels
        
        
    Examples
    --------
    
    >>> image = openpiv.tools.imread( 'image.bmp' )
    >>> print image.shape 
        (1280, 1024)
    
    
    """
    
    return scipy.misc.imread( filename, flatten=flatten).astype(np.int32)

def imsave( filename, arr ):
    """Write an image file from a numpy array
    using scipy.misc.imread
    
    Parameters
    ----------
    filename :  string
        the absolute path of the image file that will be created
    arr : 2d np.ndarray
        a 2d numpy array with grey levels
        
    Example
    --------
    
    >>> image = openpiv.tools.imread( 'image.bmp' )
    >>> image2 = openpiv.tools.negative(image)
    >>> imsave( 'negative-image.tif', image2)
    
    """
    
    if np.amax(arr) < 256 and np.amin(arr) >= 0:
        scipy.misc.imsave( filename, arr )
    else:
        raise ValueError('please provide a 2d array of grey levels (value in [0, 255])')

def save( x, y, u, v, mask, filename, fmt='%8.4f', delimiter='\t' ):
    """Save flow field to an ascii file.
    
    Parameters
    ----------
    x : 2d np.ndarray
        a two dimensional array containing the x coordinates of the 
        interrogation window centers, in pixels.
        
    y : 2d np.ndarray
        a two dimensional array containing the y coordinates of the 
        interrogation window centers, in pixels.
        
    u : 2d np.ndarray
        a two dimensional array containing the u velocity components,
        in pixels/seconds.
        
    v : 2d np.ndarray
        a two dimensional array containing the v velocity components,
        in pixels/seconds.
        
    mask : 2d np.ndarray
        a two dimensional boolen array where elements corresponding to
        invalid vectors are True.
        
    filename : string
        the path of the file where to save the flow field
        
    fmt : string
        a format string. See documentation of numpy.savetxt
        for more details.
    
    delimiter : string
        character separating columns
        
    Examples
    --------
    
    >>> openpiv.tools.save( x, y, u, v, 'field_001.txt', fmt='%6.3f', delimiter='\t')
    
    """
    # build output array
    out = np.vstack( [m.ravel() for m in [x, y, u, v, mask] ] )
            
    # save data to file.
    np.savetxt( filename, out.T, fmt=fmt, delimiter=delimiter )

def display( message ):
    """Display a message to standard output.
    
    Parameters
    ----------
    message : string
        a message to be printed
    
    """
    sys.stdout.write(message)
    sys.stdout.write('\n')
    sys.stdout.flush()

class Multiprocesser():
    def __init__ ( self, data_dir, pattern_a, pattern_b  ):
        """A class to handle and process large sets of images.

        This class is responsible of loading image datasets
        and processing them. It has parallelization facilities
        to speed up the computation on multicore machines.
        
        It currently support only image pair obtained from 
        conventional double pulse piv acquisition. Support 
        for continuos time resolved piv acquistion is in the 
        future.
        
        
        Parameters
        ----------
        data_dir : str
            the path where image files are located 
            
        pattern_a : str
            a shell glob patter to match the first 
            frames.
            
        pattern_b : str
            a shell glob patter to match the second
            frames.

        Examples
        --------
        >>> multi = openpiv.tools.Multiprocesser( '/home/user/images', 'image_*_a.bmp', 'image_*_b.bmp')
    
        """
        # load lists of images 
        self.files_a = sorted( glob.glob( os.path.join( os.path.abspath(data_dir), pattern_a ) ) )
        self.files_b = sorted( glob.glob( os.path.join( os.path.abspath(data_dir), pattern_b ) ) )
        
        # number of images
        self.n_files = len(self.files_a)
        
        # check if everything was fine
        if not len(self.files_a) == len(self.files_b):
            raise ValueError('Something failed loading the image file. There should be an equal number of "a" and "b" files.')
            
        if not len(self.files_a):
            raise ValueError('Something failed loading the image file. No images were found. Please check directory and image template name.')

    def run( self, func, n_cpus=1 ):
        """Start to process images.
        
        Parameters
        ----------
        
        func : python function which will be executed for each 
            image pair. See tutorial for more details.
        
        n_cpus : int
            the number of processes to launch in parallel.
            For debugging purposes use n_cpus=1
        
        """

        # create a list of tasks to be executed.
        image_pairs = [ (file_a, file_b, i) for file_a, file_b, i in zip( self.files_a, self.files_b, xrange(self.n_files) ) ]
        
        # for debugging purposes always use n_cpus = 1,
        # since it is difficult to debug multiprocessing stuff.
        if n_cpus > 1:
            pool = multiprocessing.Pool( processes = n_cpus )
            res = pool.map( func, image_pairs )
        else:
            for image_pair in image_pairs:
                func( image_pair )
                

def negative( image):
    """ Return the negative of an image
    
    Parameter
    ----------
    image : 2d np.ndarray of grey levels

    Returns
    -------
    (255-image) : 2d np.ndarray of grey levels

    """
    return (255-image)


def display_windows_sampling( x, y, window_size, skip=0,  method='standard'):
    """ Displays a map of the interrogation points and windows
    
    
    Parameters
    ----------
    x : 2d np.ndarray
        a two dimensional array containing the x coordinates of the 
        interrogation window centers, in pixels.
        
    y : 2d np.ndarray
        a two dimensional array containing the y coordinates of the 
        interrogation window centers, in pixels.

    window_size : the interrogation window size, in pixels
    
    skip : the number of windows to skip on a row during display. 
           Recommended value is 0 or 1 for standard method, can be more for random method
           -1 to not show any window

    method : can be only <standard> (uniform sampling and constant window size)
                         <random> (pick randomly some windows)
    
    Examples
    --------
    
    >>> openpiv.tools.display_windows_sampling(x, y, window_size=32, skip=0, method='standard')

    
    """
    
    fig=pl.figure()
    pl.hold(True)
    if skip < 0 or skip +1 > len(x[0])*len(y):
        fig.canvas.set_window_title('interrogation points map')
        pl.scatter(x, y, color='g') #plot interrogation locations
    else:
        nb_windows = len(x[0])*len(y)/(skip+1)
        #standard method --> display uniformly picked windows
        if method == 'standard':
            pl.scatter(x, y, color='g')#plot interrogation locations (green dots)
            fig.canvas.set_window_title('interrogation window map')
            #plot the windows as red squares
            for i in range(len(x[0])):
                for j in range(len(y)):
                    if j%2 == 0:
                        if i%(skip+1) == 0:
                            x1 = x[0][i] - window_size/2
                            y1 = y[j][0] - window_size/2
                            pl.gca().add_patch(pt.Rectangle((x1, y1), window_size, window_size, facecolor='r', alpha=0.5))
                    else:
                        if i%(skip+1) == 1 or skip==0:
                            x1 = x[0][i] - window_size/2
                            y1 = y[j][0] - window_size/2
                            pl.gca().add_patch(pt.Rectangle((x1, y1), window_size, window_size, facecolor='r', alpha=0.5))
        #random method --> display randomly picked windows
        elif method == 'random':
            pl.scatter(x, y, color='g')#plot interrogation locations
            fig.canvas.set_window_title('interrogation window map, showing randomly '+str(nb_windows)+' windows')
            for i in range(nb_windows):
                k=np.random.randint(len(x[0])) #pick a row and column index
                l=np.random.randint(len(y))
                x1 = x[0][k] - window_size/2
                y1 = y[l][0] - window_size/2
                pl.gca().add_patch(pt.Rectangle((x1, y1), window_size, window_size, facecolor='r', alpha=0.5))
        else:
            raise ValueError('method not valid: choose between standard and random')
    pl.draw()
    pl.show()
   
