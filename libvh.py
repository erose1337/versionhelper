import StringIO
import os
import importlib
import hashlib
import types
import string

from _database import API_Database
from _serialization import serialize, deserialize
import _checker
import pychecker

class Missing_Api_Functionality(Exception):
    """ Raised when a checker cannot locate an item listed in the API. """

class Mismatched_Api_Argument(Exception):
    """ Raised when a checker determines that a functions signature differs from what was declared in the API. """

class Unspecified_Source_Types(Exception):
    """ Raised when no source types are specified and they cannot be introspected. """

SOURCE_TYPE = {"python" : ("py", ), "c" : ("c", )}
ASCII_ALPHANUMERICS = set(string.ascii_letters + string.digits)
DATABASE = os.path.join(os.path.split(__file__)[0], "api.db")

def version_helper(api_filename, directory='', version='', prerelease='', build_metadata='',
                   db='', checker='', source_types=tuple(), no_invariant_check=False,
                   dry_run=False, silent=False):
    """Usage: version_helper(api_filename, directory='', version='', prerelease='',
                             build_metadata='', db='', checker='', source_types=tuple(),
                             no_invariant_check=False, dry_run=False,
                             silent=False) => None
       Inspect api file indicated by api_filename and relevant source code, and increment semantic version number in api file as necessary.

       # Arguments
       ------------
       api_filename is the filename string of the api file.
       directory is a file path string indicating the directory that the source code resides in.
       version is a semantic version formatted string.
       prerelease is a string of a prerelease information to be attached to the version number.
       build_metadata is a string of build metadata to be attached to the version number.
       db is a filename for the database file to be used. If the file does not exist, it will be created.
       checker is the file path for an invariance checker module.
       source_types is an iterable of file extensions indicating what type of source files to track
       no_invariant_check is a boolean flag indicating whether or not to run the invariant checker
       dry_run is a boolean flag indicating whether or not to perform a dry run (don't write to DB or API file)
       silent is a boolean flag indicating whether or not to silence output to stdout

       # All arguments except for api_filename are optional.
       ------------
       If directory is not specified, then the source code is assumed to reside in the same directory as the api file.
       If version is not specified, then new version number will be determined automatically.
       If prerelease is not specified, then no prerelease information will be appended to the version number.
       If build_metadata is not specified, then no build metadata will be appended to the version number.
       If db is not specified, then the default "api.db" file will be used.
       If checker is not specified, then the LANGUAGE attribute of the api file will be used to see if an available invariance checker is built-in. If no checker can be found, no checker will be run.
       If source_types is not specified, then the LANGUAGE attribute of the api file will be used to determine what file extensions to check
       If no_invariant_check is not specified, then the invariant checker will be run if available
       If dry_run is not specified, then the run *will* write to the DB and API
       If silent is not specified, then information will be printed to stdout

       # Side Effects
       -----------
       The VERSION attribute of the indicated api file may be modified.
       The database may be modified (insert and/or update_table)."""
    if version and len(version.split('.', 2)) != 3:
        raise ValueError("Invalid version string '{}'".format(version))
    if dry_run and not silent:
        print("Performing a dry run; Changes will not be written to DB or API file")

    api_info = _load_module_from_filename(api_filename, "api")
    directory = directory if directory else (os.path.split(api_filename)[0] or os.curdir)

    _run_invariant_checker(api_info, no_invariant_check, silent, checker, directory)

    if not source_types:
        source_types = _determine_source_types(api_info)
    serialized_api = serialize(api_info.API)
    digest = _obtain_package_digest(directory, serialized_api, source_types)

    project_name = api_info.PROJECT
    db = API_Database(database_name=db or DATABASE)
    old_digest, old_api, db_entry = _obtain_old_api_info(db, project_name, dry_run, api_info, digest, serialized_api)

    if dry_run:
        _file = StringIO.StringIO()
        _update_version(digest, old_digest, version, prerelease, build_metadata,
                        db, silent, api_info, old_api, dry_run, serialized_api,
                        db_entry, _file)
    else:
        with open("apichangelog.txt", 'w') as _file:
            _update_version(digest, old_digest, version, prerelease, build_metadata,
                            db, silent, api_info, old_api, dry_run, serialized_api,
                            db_entry, _file)


def _update_version(digest, old_digest, version, prerelease, build_metadata, db,
                    silent, api_info, old_api, dry_run, serialized_api, db_entry,
                    _file):
    if digest != old_digest or version or prerelease or build_metadata:
        if version: # explicitly set a version number
            new_version = _attach_metadata(version, prerelease, build_metadata)
            message = "Set version to {} (from {})".format(new_version, api_info.VERSION)
            _file.write(message + "\n")
            if not silent:
                print(message)
        elif not db_entry: # first run, don't increment version
            new_version = _attach_metadata(api_info.VERSION, prerelease, build_metadata)
            message = "First run, version is set to {}".format(api_info.version)
            _file.write(message + "\n")
            if not silent:
                print(message)
        elif digest != old_digest: # changes have happened, update version accordingly
            new_version = _determine_new_version(api_info, old_api, silent, _file)
            new_version = _attach_metadata(new_version, prerelease, build_metadata)
            message = "Changed version from {} to {}".format(api_info.VERSION, new_version)
            _file.write(message + "\n")
            if not silent:
                print(message)
        else: # only handle prerelease/build_metadata
            version = api_info.VERSION
            new_version = _attach_metadata(version, prerelease, build_metadata)
            format_info = []
            if prerelease:
                format_info.append("prerelease")
            if build_metadata:
                format_info.append("build_metadata")
            formatted = " and ".join(format_info)
            message = "Added {} to version: {} -> {}".format(formatted, version, new_version)
            _file.write(message + "\n")
            if not silent:
                print(message)
        if not dry_run:
            _write_version(api_info.__file__, api_info.VERSION, new_version)
            db.update_table("Api_Info", where={"project" : api_info.PROJECT},
                            arguments={"digest" : digest, "api" : serialized_api})
    else:
        if db_entry:
            message = "No changes. Version number: {}".format(api_info.VERSION)
            _file.write(message + "\n")
            if not silent:
                print(message)
        else:
            message = "First run, version is set to {}".format(api_info.VERSION)
            _file.write(message + "\n")
            if not silent:
                print(message)

def _obtain_old_api_info(db, project_name, dry_run, api_info, digest, serialized_api):
    db_entry = db.query("Api_Info", retrieve_fields=("digest", "api"),
                                    where={"project" : project_name})
    if not db_entry:
        if not dry_run:
            db.insert_into("Api_Info", (project_name, digest, serialized_api))
        old_digest = digest
        old_api = api_info.API
    else:
        old_digest, old_api = db_entry
        old_api = deserialize(old_api)
    return old_digest, old_api, db_entry

def _determine_source_types(api_info):
    language = getattr(api_info, "LANGUAGE", '')
    try:
        source_types = SOURCE_TYPE[language]
    except KeyError:
        error_message = "Source types not explicitly specified; Unable to determine source file types"
        if language:
            error_message += " for language '{}'".format(language)
        else:
            error_message += "; api.LANGUAGE not specified"
        raise Unspecified_Source_Types(error_message)
    else:
        return source_types

def _run_invariant_checker(api_info, no_invariant_check, silent, checker, directory):
    if no_invariant_check:
        if not silent:
            print("Skipping invariant checker")
    else:
        languages = getattr(api_info, "LANGUAGE", '')
        checkers = []
        if not checker:
            if not languages:
                if not silent:
                    print("No language or invariant checker specified. Unable to run invariant checker")
            else:
                if isinstance(languages, str):
                    languages = [languages]
                for language in languages:
                    if language == "python":
                        checkers.append(pychecker)
                    else:
                        if not silent:
                            print("Checker module for language '{}' not built-in. Unable to check {} files".format(language, language))
        else: # custom checker(s)
            for checker_file in checker.split(','):
                checkers.append(_load_module_from_filename(checker_file.strip(), "checker"))

        _checker.check_api_items(api_info.API, directory, checkers)

def _load_module_from_filename(filename, module_name):
    with open(filename, 'r') as _file:
        source = _file.read()
    module_code = compile(source, module_name, "exec")
    module = types.ModuleType("api")
    exec module_code in module.__dict__
    module.__file__ = filename
    return module

def _attach_metadata(new_version, prerelease, build_metadata):
    if prerelease:
        for segment in prerelease.split('.'):
            if segment == '': # segment was just a .
                raise ValueError("Invalid prerelease string '{}' contains non-separator period".format(prerelease))
            elif segment[0] == '0' and len(segment) > 1:
                raise ValueError("Invalid prerelease string '{}' contains leading zeros".format(prerelease))
            elif set(segment).difference(ASCII_ALPHANUMERICS):
                raise ValueError("Invalid prerelease string '{}' contains non-alphanumeric ASCII".format(prerelease))
        try:
            new_version, old_prerelease = new_version.split('-', 1)
        except ValueError:
            pass
        new_version += "-" + prerelease
    if build_metadata:
        for segment in build_metadata.split('.'):
            if segment == '':
                raise ValueError("Invalid build metadata string '{}' contains non-separator period".format(build_metadata))
            elif set(segment).difference(ASCII_ALPHANUMERICS):
                raise ValueError("Invalid built metadata string '{}' contains non-alphanumeric ASCII".format(build_metadata))
        try:
            new_version, old_build_metadata = new_version.split('+', 1)
        except ValueError:
            pass
        new_version += "+" + build_metadata
    return new_version

def _determine_new_version(api_info, old_api, silent, _file):
    change_type = _determine_change_type(api_info.API, old_api, silent, _file)
    return _increment_version(change_type, api_info.VERSION, silent, _file)

def _increment_version(change_type, current_version, silent, _file):
    major, minor, patch, prerelease, build_metadata = parse_version(current_version)
    message = "Change type: {}".format(change_type)
    _file.write(message + "\n")
    if not silent:
        print(message)
    if prerelease:
        checked = []
        values = prerelease.split('.')
        for item in values:
            try:
                int(item)
            except ValueError:
                checked.append(item)
            else:
                checked.append(str(int(item) + 1))
                break
        else:
            checked.append('0')
        prerelease = '.'.join(checked)
    elif change_type == "major":
        if major != '0':
            major = str(int(major) + 1)
            minor = patch = '0'
        else:
            minor = str(int(minor) + 1)
            patch = '0'
    elif change_type == "minor":
        minor = str(int(minor) + 1)
        patch = '0'
    else:
        patch = str(int(patch) + 1)
    new_version = '.'.join((major, minor, patch))
    if prerelease:
        new_version = '-'.join((new_version, prerelease))
    if build_metadata:
        new_version = '+'.join((new_version, build_metadata))
    return new_version

def parse_version(version):
    major, minor, patch = version.split('.', 2)
    try:
        patch, prerelease = patch.split('-', 1)
    except ValueError:
        prerelease = ''
        try:
            patch, build_metadata = patch.split('+', 1)
        except ValueError:
            build_metadata = ''
    else:
        try:
            prerelease, build_metadata = prerelease.split('+', 1)
        except ValueError:
            build_metadata = ''
    return major, minor, patch, prerelease, build_metadata

def _write_version(api_file, current_version, new_version):
    with open(api_file, "r+") as _file:
        assert _file.tell() == 0
        source = _file.read().replace("VERSION = \"{}\"".format(current_version),
                                      "VERSION = \"{}\"".format(new_version), 1)
        _file.truncate(0)
        _file.seek(0)
        assert _file.tell() == 0
        _file.write(source)

def _obtain_package_digest(package_dir, serialized_api, source_types):
    """Returns a hash representing the state of the source files in package_dir."""
    hash_output = hashlib.sha256()
    for root, _, files in os.walk(package_dir):
        for filename in files:
            extension = os.path.splitext(filename)[1][1:] # slice off '.'
            if extension and extension in source_types:
                name = os.path.splitext(os.path.split(filename)[1])[0]
                if name != "api":
                    with open(os.path.join(root, filename), 'r') as _file:
                        hash_output.update(_file.read())
    hash_output.update(serialized_api + "api")
    return hash_output.hexdigest()

def _determine_change_type(api, old_api, silent, _file):
    # major changes:
    #   functions in API removed
    #   positional arguments removed or re-ordered
    #   keyword arguments removed or renamed
    #   return types modified
    #   exceptions modified
    #       - not sure if adding return types/exceptions constitutes API breaking change
    #       - cannot assume that code that uses API will work with alternative return types or catch new exceptions, so it seems major
    # minor changes:
    #   functions added to API
    #   positional arguments added
    #   keyword arguments added
    # patch changes:
    #   anything else
    #       - includes negligible changes like comments
    change = "patch"

    function_removals = [method_name for method_name in old_api.keys() if method_name not in api]
    if function_removals:
        message = "Major: Following functions were removed:\n    {}".format('\n'.join(item for item in function_removals))
        _file.write(message + "\n")
        if not silent:
            print(message)
        change = "major"

    for method_name, old_values in old_api.items():
        try:
            api_values = api[method_name]
        except KeyError: # function was removed from api
            continue
        else:
            (arguments, old_arguments, keywords, old_keywords,
             returns, old_returns, exceptions, old_exceptions,
             side_effects, old_side_effects) = _extract_api_values(api_values, old_values)

        change, positionals_added = _detect_positional_changes(arguments, old_arguments, method_name, change, silent, _file)
        change, keywords_added = _detect_keyword_changes(keywords, old_keywords, method_name, change, silent, _file)
        change = _detect_return_changes(returns, old_returns, method_name, change, silent, _file)
        change = _detect_exception_changes(exceptions, old_exceptions, method_name, change, silent, _file)
        change, side_effects_added = _detect_side_effect_changes(side_effects, old_side_effects, method_name, change, silent, _file)

        if ((side_effects_added or positionals_added or
             keywords_added or old_values.get("deprecated", False))
            and change != "major"):
            change = "minor"

    new_functions = [method for method in api.keys() if method not in old_api]
    if new_functions:
        formatted = ", ".join(new_functions)
        message = "Minor: Following functions were added:\n    {}".format(formatted)
        _file.write(message + "\n")
        if not silent:
            print(message)
        if change != "major":
            change = "minor"
    return change

def _extract_api_values(api_values, old_values):
    arguments = api_values.get("arguments", None)
    keywords = api_values.get("keywords", None)
    returns = api_values.get("returns", None)
    exceptions = api_values.get("exceptions", None)
    old_arguments = old_values.get("arguments", None)
    old_keywords = old_values.get("keywords", None)
    old_returns = old_values.get("returns", None)
    old_exceptions = old_values.get("exceptions", None)
    side_effects = api_values.get("side_effects", None)
    old_side_effects = old_values.get("side_effects", None)
    output = [arguments or tuple(), old_arguments or tuple(),
              keywords or dict(), old_keywords or dict()]
    output += [item or tuple() for item in (returns, old_returns,
                                            exceptions, old_exceptions,
                                            side_effects, old_side_effects)]
    return output

def _detect_positional_changes(arguments, old_arguments, method_name, change, silent, _file):
    arguments = arguments
    old_arguments = old_arguments
    positionals_removed = []
    positionals_moved = []
    positionals_added = [argument for argument in arguments if
                         argument not in old_arguments]
    for i, argument in enumerate(old_arguments):
        if argument not in arguments:
            positionals_removed.append(argument)
        else:
            try:
                if arguments[i] != argument:
                    positionals_moved.append(argument)
            except IndexError:
                break

    if positionals_removed:
        formatted = ", ".join(positionals_removed)
        message = "Major: Following positional arguments for {} were removed:\n    {}".format(method_name, formatted)
        _file.write(message + "\n")
        if not silent:
            print(message)
        change = "major"
    if positionals_moved:
        formatted = "\n".join(positionals_moved)
        message = "Major: Following positional arguments for {} were moved:\n    {}".format(method_name, formatted)
        _file.write(message + "\n")
        if not silent:
            print(message)
        change = "major"
    if positionals_added:
        formatted = ", ".join(positionals_added)
        message = "Minor: Following positional arguments for {} were added:\n    {}".format(method_name, formatted)
        _file.write(message + "\n")
        if not silent:
            print(message)
        # defer assigning change to minor until after all major changes have been determined
    return change, bool(positionals_added)

def _detect_keyword_changes(keyword_arguments, old_keyword_arguments, method_name, change, silent, _file):
    keywords_removed = []
    keywords_modified = []
    keywords_added = [(key, value) for key, value in keyword_arguments.items() if
                      key not in old_keyword_arguments]
    for key, value in old_keyword_arguments.items():
        if key not in keyword_arguments:
            keywords_removed.append(key)
        elif keyword_arguments[key] != value:
            keywords_modified.append((key, value, keyword_arguments[key]))

    if keywords_removed:
        formatted = ", ".join(keywords_removed)
        message = "Major: Following keyword arguments for {} were removed:\n    {}".format(method_name, formatted)
        _file.write(message + "\n")
        if not silent:
            print(message)
        change = "major"
    if keywords_modified:
        formatted = "\n".join("{}: {} -> {}".format(key, value, value2) for key, value, value2 in keywords_modified)
        message = "Major: Following keyword arguments for {} were modified:\n    {}".format(method_name, formatted)
        _file.write(message + "\n")
        if not silent:
            print(message)
        change = "major"
    if keywords_added:
        formatted = "\n".join("    {}: {}".format(key, value) for key, value in keywords_added)
        message = "Minor: Following keyword arguments for {} were added:\n{}".format(method_name, formatted)
        _file.write(message + "\n")
        if not silent:
            print(message)
        # defer assigning change to minor until after all major changes have been determined
    return change, bool(keywords_added)

def _detect_return_changes(returns, old_returns, method_name, change, silent, _file):
    returns_removed = [value for value in old_returns if value not in returns]
    returns_added = [value for value in returns if value not in old_returns]
    if returns_removed:
        formatted = ", ".join(returns_removed)
        message = "Major: Following return types for {} were removed:\n    {}".format(method_name, formatted)
        _file.write(message + "\n")
        if not silent:
            print(message)
        change = "major"
    if returns_added:
        formatted = ", ".join(returns_added)
        message = "Major: Following return types for {} were added:\n    {}".format(method_name, formatted)
        _file.write(message + "\n")
        if not silent:
            print(message)
        change = "major"
    return change

def _detect_exception_changes(exceptions, old_exceptions, method_name, change, silent, _file):
    exceptions_removed = [exception for exception in old_exceptions if exception not in exceptions]
    exceptions_added = [exception for exception in exceptions if exception not in old_exceptions]
    if exceptions_removed:
        formatted = ", ".join(exceptions_removed)
        message = "Major: Following exceptions for {} were removed:\n    {}".format(method_name, formatted)
        _file.write(message + "\n")
        if not silent:
            print(message)
        change = "major"
    if exceptions_added:
        formatted = ", ".join(exceptions_added)
        message = "Major: Following exceptions for {} were added:\n    {}".format(method_name, formatted)
        _file.write(message + "\n")
        if not silent:
            print(message)
        change = "major"
    return change

def _detect_side_effect_changes(side_effects, old_side_effects, method_name, change, silent, _file):
    side_effects_removed = [effect for effect in old_side_effects if effect not in side_effects]
    side_effects_added = [effect for effect in side_effects if effect not in old_side_effects]
    if side_effects_removed:
        formatted = ", ".join(side_effects_removed)
        message = "Major: Following side effects for {} were removed:\n    {}".format(method_name, formatted)
        _file.write(message + "\n")#
        if not silent:
            print(message)
        change = "major"
    if side_effects_added:
        formatted = ", ".join(side_effects_added)
        message = "Minor: Following side effects for {} were added:\n    {}".format(method_name, formatted)
        _file.write(message + "\n")
        if not silent:
            print(message)
        # defer assigning change until later
    return change, bool(side_effects_added)
