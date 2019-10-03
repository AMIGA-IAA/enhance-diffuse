import os
import configparser
import glob

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
    return fits_files

def main():
    config = read_config(config_file, print_values=True)
    fits_files = find_image_names(input_location)

if __name__=="__main__":
    main()
