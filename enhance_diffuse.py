import configparser

config_file = './params.cfg'

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

def main():
    config = read_config(config_file, print_values=True)

if __name__=="__main__":
    main()
