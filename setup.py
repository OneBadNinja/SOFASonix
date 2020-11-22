import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
  name="SOFASonix",
  version="1.0.7",
  author='Ioseb Laghidze',
  author_email='developer@artisan-one.com',
  description="A Lightweight Python API for the AES69-2015 Spatially Oriented Format for Acoustics (SOFA) File Format",
  long_description=long_description,
  long_description_content_type="text/markdown",
  url='https://github.com/OneBadNinja/SOFASonix/',
  packages=setuptools.find_packages(),
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
  python_requires='>=2.7',
  license='BSD 3-Clause',
  keywords=['SOFA', 'Spatially Oriented Format For Acoustics',
            'Audio', '3D Audio', 'Binaural', 'Transaural', 'Acoustics'],
  package_data={
    # Include database file
    'SOFASonix': ['*.db'],
  },
  install_requires=[
          'netCDF4',
          'numpy',
          'pandas',
  ]
)
