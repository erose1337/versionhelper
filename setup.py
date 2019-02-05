from setuptools import setup

import versionhelper.api

options = {"name" : "versionhelper",
           "version" : versionhelper.api.VERSION,
           "description" : "Automatically increment semantic version number according to changes in the code and API",
           #"long_description" : '',
           #"url" : "",
           #"download_url" : "",
           "author" : "Ella Rose",
           "author_email" : "python_pride@protonmail.com",
           "packages" : ["versionhelper"],
           "classifiers" : ["Development Status :: 4 - Beta",
                            "Intended Audience :: Developers",
                            "License :: OSI Approved :: MIT License",
                            "Operating System :: Microsoft :: Windows",
                            "Operating System :: POSIX :: Linux",
                            "Programming Language :: Python :: 2.7",
                            "Topic :: Software Development :: Libraries :: Python Modules"]
                            }

if __name__ == "__main__":
    setup(**options)
