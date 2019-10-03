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
    location = os.path.join(input_location, '*fits')
    print(f'Looking for files in {location}')
    files = glob.glob(location)
    if len(files) > 0:
        print('Files to process {}'.format(files))
    else:
        print('Warning, no files found')

def main():
    config = read_config(config_file, print_values=True)
    find_image_names(input_location)

if __name__=="__main__":
    main()
