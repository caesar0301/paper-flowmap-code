paper-flowmap-code
==================
Data and analyzing code for paper flowmap


Dependence
----------

* Install `requirements.txt`

    $ pip install -r requirements.txt

* Install `matplotlib`

    $ export http_proxy=http://jackfan.com:4000
    $ pip install -U numpy pytz cycler tornado pyparsing
    $ yum install -y freetype-devel libpng-devel

    $ wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py -O - | python
    $ pip install -U distribute && pip install -U matplotlib

* To use `read_shp()` of `networkx`, install `GDAL` and `osgeo` module

    $ yum install -y gdal-python gdal-devel hdf5-devel

    $ ln -s /usr/lib64/libhdf5.so /usr/lib64/libhdf5.so.6
    $ ln -s /usr/lib64/libhdf5_hl.so /usr/lib64/libhdf5_hl.so.6

    $ python -c "from osgeo import ogr"

**Tested on CentOS 6.5.**