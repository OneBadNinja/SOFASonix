from distutils.core import setup

setup(
  name="SOFASonix",
  packages=["SOFASonix"],
  version="1.0.6",
  license='BSD 3-Clause',
  description="A Lightweight Python API for the AES69-2015 Spatially Oriented Format for Acoustics (SOFA) File Format",
  author='Ioseb Laghidze',
  author_email='developer@artisan-one.com',
  url='https://github.com/OneBadNinja/SOFASonix/',
  download_url='https://github.com/OneBadNinja/SOFASonix/archive/1.0.6.tar.gz',
  keywords=['SOFA', 'Spatially Oriented Format For Acoustics',
            'Audio', '3D Audio', 'Binaural', 'Transaural', 'Acoustics'],
  package_data={
    # Include database file
    '': ['*.db'],
    },
  install_requires=[
          'netCDF4',
          'numpy',
          'pandas',
      ],
  classifiers=[
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
  ],
)
