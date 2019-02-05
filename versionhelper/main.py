import argparse
import sys

import libvh

PARSER = argparse.ArgumentParser()
PARSER.add_argument("api", help="The api file to work on")
PARSER.add_argument("-v", "--version", help="Explicitly sets version to the specified version number.")
PARSER.add_argument("-d", "--directory", help="Specify a directory where the source code lives, if different from the location of the api file")
PARSER.add_argument("-p", "--prerelease", help="Specify a pre-release string to be included after the patch number")
PARSER.add_argument("-b", "--build_metadata", help="Specify build metadata string to be included after the patch number")
PARSER.add_argument("-db", "--database", help="Specify the database file that stores the prior API version")
PARSER.add_argument("-c", "--checker", help="Specify (comma separated) file(s) that should provide the `check_api_item` functionality")
PARSER.add_argument("-x", "--extensions", help="Specify the file extensions of possible source files")
PARSER.add_argument("-nic", "--no_invariant_check", help="Specify that the invariant checker should not be run", action="store_true")
PARSER.add_argument("-dry", "--dry_run", help="Perform a dry run; Does not write to DB or API file", action="store_true")
PARSER.add_argument("-s", "--silent", help="Do not display any information to stdout", action="store_true")

def main():
    if "--site_config" in sys.argv:
        sys.argv.remove("--site_config")
        sys.argv.remove("Alert_Handler.defaults={\'parse_args\':False}")
    args = PARSER.parse_args()
    libvh.version_helper(args.api, args.directory, args.version,
                         args.prerelease, args.build_metadata,
                         args.database, args.checker, args.extensions,
                         args.no_invariant_check, args.dry_run, args.silent)

if __name__ == "__main__":
    if "-m" in sys.argv:
        sys.argv.remote("-m")
    # disables the pride Alert_Handler from displaying when --help is used
    #if "--site_config" not in sys.argv:
    sys.argv.insert(1, "--site_config")
    sys.argv.insert(2, "Alert_Handler.defaults={\'parse_args\':False}")
    main()
