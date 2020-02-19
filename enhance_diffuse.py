import os
import shutil
import tempfile
import configparser
import glob
import numpy as np
import argparse
from astropy.io import fits
from astropy.convolution import convolve
from astropy.convolution import Gaussian2DKernel


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
                             'Default is ./Inputs/',
                        default='./Inputs/')
    parser.add_argument('-o','--outputs', dest='output_location',
                        help='Location of folder containing the images. '\
                             'Default is ./outputs/',
                        default='./outputs/')
    parser.add_argument('--keep_tmp', action='store_true',
                        help='Do not delete temporary files. Default is False', default=False)
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

def get_tempfile(filename, tmp_dir='./tmp_img', prefix=''):
    """
    Returns a file name to store temporary images.
    """
    tempfile = os.path.join(tmp_dir, prefix+'_'+os.path.basename(filename))
    print('Producing temporary file: {}'.format(tempfile))
    return tempfile

def run_astnoisechisel(filename, config):
    """
    Run Gnuastro noisechisel and return the detection mask
    """
    tempfile = get_tempfile(filename, prefix='noisechisel')
    with open(tempfile, 'wb') as fp:
        command = 'astnoisechisel {} -h0 '\
                     '--tilesize={},{} '\
                     '--qthresh={} '\
                     '--interpnumngb={} '\
                     '--detgrowquant={} '\
                     '--output={}'.format(filename,
                                               config['tilesize'], config['tilesize'],
                                               config['qthresh'],
                                               config['interpnumngb'],
                                               config['detgrowquant'],
                                               fp.name)
        print('Executing: ' + command)
        os.system(command)
        if fits.open(fp.name)[2].name != 'DETECTIONS':
            raise Exception('Wrong selection detections fits')
        noisechisel_detection = fits.open(fp.name)[2].data

    return noisechisel_detection


def run_sextractor_mask(filename, sexconf='Params/sex_point.conf'):
    """
    Run Sextractor and return the detection mask
    """
    tempfile = get_tempfile(filename, prefix='sextractor')
    with open(tempfile, 'wb') as fp:
        command = f'{SEXTRACTOR_CMD} {filename} '\
                  f'-c {sexconf} '\
                  f'-CHECKIMAGE_NAME {fp.name}'

        print('Executing: ' + command)
        os.system(command)
        sextractor_detection = fits.open(fp.name)[0].data

    return sextractor_detection

def create_master_mask(fits_files, config, data_shape):
    """
    Combines the masks produced by astnoischisel and sextractor for each image
    into a master boolean mask with the detected sources
    """
    master_mask = np.zeros(data_shape).astype('bool')
    for fits_file in fits_files:
        noisechisel_detection = run_astnoisechisel(fits_file, config).astype('bool')
        sextractor_detection = run_sextractor_mask(fits_file).astype('bool')
        master_mask += noisechisel_detection
        master_mask += sextractor_detection
    return master_mask

def create_stacked_image(fits_files, data_shape):
    """
    Combines all the images into a single array
    """
    stacked = np.zeros(data_shape)
    for fits_file in fits_files:
        hdulist = fits.open(fits_file)
        data = hdulist[0].data
        stacked += data
    return stacked

def mask_image(image, mask):
    """
    Filters an array with an inverted mask
    """
    image[mask] = np.nan
    return image

def write_fits(master_mask,stacked_masked, reference_header, output_location):
    """
    Function to convert to fits files the master mask and the stacked image
    after being masked. It uses one image as a reference for the header
    information and saves the files in the output_location
    """
    out_mask = output_location+'/master_mask.fits'
    out_image = output_location+'/stacked_masked.fits'
    if os.path.exists(out_mask):
        os.remove(out_mask)
    if os.path.exists(out_image):
        os.remove(out_image)
    hdulist = fits.open(reference_header)
    hdulist[0].data = master_mask.astype(int)
    hdulist.writeto(out_mask)
    hdulist[0].data = stacked_masked
    hdulist.writeto(out_image)
    return out_mask, out_image

def rebin_image(image, smoothing):
    """
    Run swarp and return the binned masked combined image
    """

    command = 'swarp {} -c Params/swarp.conf'.format(image)
    print('Executing: ' + command)
    os.system(command)
    # Note that swarp outputs coadds.fits

    # Read swarp output image
    hdulist = fits.open('coadd.fits')
    header =  hdulist[0].header
    data =  hdulist[0].data
    # Fix data NaNs
    data[data == 0.0] = np.nan

    # Gaussian filter
    print(type(smoothing))
    kernel = Gaussian2DKernel(x_stddev=int(smoothing))
    data_gauss_astropy = convolve(data, kernel= kernel)
    outname = 'enhanced.fits'
    if os.path.isfile(outname):
        os.remove(outname)

    fits.writeto(outname, data_gauss_astropy, header)
    return


def main():
    # Read configuration
    args = get_args()
    config_file = args.config_file
    config = read_config(config_file, print_values=True)
    input_location = args.input_location
    output_location = args.output_location
    tmp_dir = './tmp_img'
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.mkdir(tmp_dir)
    if not os.path.exists(output_location):
        os.mkdir(output_location)
    # Find images
    fits_files = find_image_names(input_location)
    data_shape =  read_imsize(fits_files)
    # Create stacked images and masks
    master_mask = create_master_mask(fits_files, config, data_shape=data_shape)
    stacked_image = create_stacked_image(fits_files, data_shape=data_shape)
    stacked_masked = mask_image(stacked_image, master_mask)
    master_mask, staked_masked = write_fits(master_mask,stacked_masked,
                                     reference_header=fits_files[0],
                                     output_location=output_location)
    rebin_image(staked_masked, smoothing=config['smoothing'])
    # Remove temporary files if not needed:
    if not args.keep_tmp:
        print('Removing temporary files. To keep them use --keep_tmp')
        shutil.rmtree(tmp_dir)
    print('Output products in: {}'.format(output_location))


if __name__=="__main__":
    main()
