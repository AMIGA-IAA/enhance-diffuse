# enhance-diffuse
[![Build Status](https://travis-ci.org/AMIGA-IAA/enhance-diffuse.svg?branch=master)](https://travis-ci.org/AMIGA-IAA/enhance-diffuse)

# Dependencies

 - python 3.7.*
 - astropy 3.2.*
 - numpy 1.17.*
 - gnuastro 0.10.*
 - astromatic-swarp 2.38.*
 - astromatic-source-extractor 2.25.*

If you have `conda`, they can be satisfied with the environment enhance-diffuse created with the command:

`conda env create -f environment.yml`

# Usage

`python enhance_diffuse.py`

```bash
optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_LOCATION, --input INPUT_LOCATION
                        Location of folder containing the images. Default is
                        ./Inputs/
  -o OUTPUT_LOCATION, --outputs OUTPUT_LOCATION
                        Location of folder containing the images. Default is
                        ./outputs/
  --keep_tmp            Do not delete temporary files. Default is False
  -c CONFIG_FILE, --config CONFIG_FILE
                        Parameters file to use. Default is ./params.cfg
```
