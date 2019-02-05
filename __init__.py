"""Automatically increments semantic version number according to changes in the API.

   How to use:
        # if versionhelper is installed
        python -m versionhelper [api_file] ...

        # otherwise
        python versionhelper.py [api_file] ..."""
import sys

# disables the pride Alert_Handler from displaying when --help is used
sys.argv.insert(1, "--site_config")
sys.argv.insert(2, "Alert_Handler.defaults={\'parse_args\':False}")

if __name__ == "__main__": # so you can run python -m versionhelper ...
    import main            # instead of python -m versionhelper.main ...
    main.main()
