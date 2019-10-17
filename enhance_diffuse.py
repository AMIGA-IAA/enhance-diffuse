import os
import tempfile
import configparser
import glob
import numpy as np
import argparse
from astropy.io import fits

SEXTRACTOR_CMD = 'sex'

def get_args():
    """
    Get additional arguments parsed using the command line
    Returns args containing input_location and config_file
    """
    description = "Script to enhance the diffuse emission "\
                   "of a set of optical images."
    usage = "python enhance_diffuse.py"
    epilog = "The script requires some gnuastro packages..."
    parser = argparse.ArgumentParser(description=description,
                                     usage=usage,
                                     epilog=epilog)
    parser.add_argument('-i','--input', dest='input_location',
                        help='Location of folder containing the images. '\
                             'Default is ./Inputs',
                        default='./Inputs')
    parser.add_argument('-c','--config', dest='config_file',
                        help='Parameters file to use. Default is ./params.cfg',
                        default='./params.cfg')
    args = parser.parse_args()
    return args

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


def run_astnoisechisel(filename, config):
    """
    Run Gnuastro noisechisel and return the detection mask
    """

    with tempfile.NamedTemporaryFile() as fp:
        command = 'astnoisechisel {} -h0 '\
                     '--tilesize={},{} '\
                     '--qthresh={} '\
                     '--interpnumngb={} '\
                     '--detgrowquant={} '\
                     '--output={}.fits'.format(filename,
                                               config['tilesize'], config['tilesize'],
                                               config['qthresh'],
                                               config['interpnumngb'],
                                               config['detgrowquant'],
                                               fp.name)
        print('Executing:' + command)
        os.system(command)
        if fits.open(fp.name + '.fits')[2].name != 'DETECTIONS':
            raise Exception('Wrong selection detections fits')
        noisechisel_detection = fits.open(fp.name + '.fits')[2].data

    return noisechisel_detection


def run_sextractor_mask(filename, sexconf='Params/sex_point.conf'):
    """
    Run Sextractor and return the detection mask
    """

    with tempfile.NamedTemporaryFile() as fp:
        command = f'{SEXTRACTOR_CMD} {filename} '\
                  f'-c {sexconf} '\
                  f'-CHECKIMAGE_NAME {fp.name}.fits'

        print('Executing:' + command)
        os.system(command)
        sextractor_detection = fits.open(fp.name + '.fits')[0].data

    return sextractor_detection


def main():
    args = get_args()
    input_location = args.input_location
    config_file = args.config_file
    config = read_config(config_file, print_values=True)
    fits_files = find_image_names(input_location)
    data_shape =  read_imsize(fits_files)
    noisechisel_detection = run_astnoisechisel(fits_files[0], config)
    sextractor_detection = run_sextractor_mask(fits_files[0])

if __name__=="__main__":
    main()
