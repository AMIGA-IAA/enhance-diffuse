import os
import configparser
import glob
import numpy as np
from astropy.io import fits

config_file = './params.cfg'
input_location = './Inputs'

def read_config(config_file, print_values=False):
    """
    Read parameters from configuration file.
    Input: configuration file in configparser format
    Output: dictionary with parameters
    """
    config_data = configparser.ConfigParser()
    config_data.read(config_file)
    config = config_data._sections['parameters']
    if print_values:
        for key, value in config.items():
            print(f'{key:12} : {value}')
    return config

def find_image_names(input_location):
    """ Gathers all fits files in the input folder
    Input: string location to search for files
    Output: list of files files in the input folder
    """
    location = os.path.join(input_location, '*fits')
    print(f'Looking for files following: {location}')
    fits_files = glob.glob(location)
    if len(fits_files) > 0:
        file_names = [os.path.basename(x) for x in fits_files]
        print('Files to process {}'.format(file_names))
    else:
        print('Warning, no files found')
    num_images = len(fits_files)
    print(f'Number of images {num_images}')
    return np.atleast_1d(fits_files)

def read_imsize(fits_files):
    """
    Read the size of the fits image
    """
    # First image as a reference
    hdulist_0 = fits.open(fits_files[0])
    data_shape_0 = hdulist_0[0].data.shape

    for image in fits_files:
        hdulist = fits.open(image)
        data_shape = hdulist[0].data.shape
        if data_shape != data_shape_0:
            msg = f'WARNING! Image size mismatch'\
                    f'First image size: {data_shape_0}' \
                    f'Image {image} size: {data_shape}'
            raise Exception(msg)
    print(f'Image size: {data_shape_0}')
    return data_shape_0



def main():
    config = read_config(config_file, print_values=True)
    fits_files = find_image_names(input_location)
    data_shape =  read_imsize(fits_files)

if __name__=="__main__":
    main()
