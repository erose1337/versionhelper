Semantic Versioning
-----

Before you begin, you will want to familiarize yourself with [*Semantic Versioning*]((https://semver.org).


Getting started
-----

First, you will need to create a file named "api" at the root of your source code directory. This file provides details about your API.

An API file should contain the following information:

- Version number
- Language
- Project name
- A description of the interface
    - Includes method names, and as applicable: argument types, keyword arguments, return types, raised exceptions, deprecation warnings, and any side effects.

Demo api file
-----
Create a `apidemo` folder, and in it create an `lib.py` file. Place the following code into `lib.py`:

    _STORAGE1 = []
    _STORAGE2 = dict()

    def add_numbers(x, y):
        return x + y

    def manipulate_filenames(filenames):
        for index in range(len(filenames)):
            if filenames[index] == "api":
                raise ValueError()
            filenames[index] += str(index)

    def update_storage(*args, **kwargs):
        _STORAGE1.extend(args)
        _STORAGE2.update(kwargs)

    def _private_function():
        pass

    def cached_function(x, y, _cache=dict()):
        try:
            return _cache[(x, y)]
        except KeyError:
            output = _cache[(x, y)] = add_numbers(x, y)
            return output


And next create a `setup.py` file:

    from setuptools import setup
    import apidemo.api

    options = {"name" : "apidemo",
               "version" : apidemo.api.VERSION,
               "description" : "versionhelper demonstration",
               "packages" : ["apidemo"]}

    if __name__ == "__main__":
        setup(**options)

And run `python setup.py develop` to install the apidemo package in development mode.

The API file
----
Now we will make an API file that describes this code and maintains a version number.

Create a file named `"api.py"`, and enter the following:


    VERSION = "0.1.0"
    LANGUAGE = "python"
    PROJECT = "apidemo"

    API = {"apidemo.lib.add_numbers" : {"arguments" : ("int", "int"),
                                        "returns" : ("int", )},
           "apidemo.lib.manipulate_filenames" : {"arguments" : ("list of filename str", ),
                                                 "returns" : None,
                                                 "exceptions" : ("ValueError", )},
           "apidemo.lib.update_storage" : {"arguments" : ("*args", ),
                                           "keywords" : {"**kwargs" : ''},
                                           "side_effects" : ("extends _STORAGE1", "updates _STORAGE2")},
           "apidemo.lib.cached_function" : {"arguments" : ("int", "int"),
                                            "returns" : ("int", )}
          }


The `.py` file extension is optional in general, but we are importing the api file from the setup script to have access to the version number, so for this instance it needs to be a `.py` file.

A description of the contents:

- `VERSION` is a [semantic version number](https://semver.org)
- `LANGUAGE` is the language the project is written in
- `PROJECT` is the name of the project.

So far, it should be pretty self explanatory; The only detail you need to remember is to put quotes around the values that you define for these.

Next up is the important part: Documentation for the API.

If you're familiar with python, you'll recognize the entry for the API as a python dictionary. Each key (e.g. `"apidemo.lib.add_ints"`) names a function that the "apidemo" project exposes for users of the project. The format of the key may vary between different project languages - with python, there is a nice representation using the package_name.module_name.class_name.function_name format, with some segments being optional or with multiple layers. Other languages, such as C, might specify items differently, e.g. `apidemo/lib:add_ints`. The invariant checker (which has not yet been discussed) will likely depend on a particular format, but built-in invariant checkers are not yet available for languages other than python, so the format for entries is still open.

Each value in the dictionary is another dictionary that contains the information that describes how to use that part of the API. The relevant information can include: argument types, keyword arguments, return types, raised exceptions, side effects, and deprecation warnings.

We can see that the `apidemo.lib.add_ints` is a function that takes 2 positional arguments and no keyword arguments. It indicates that it takes an int for the first argument, and an int for the second argument.

Note that these types are placed in quotes, as are all of the rest of the information that are not None.

Another important note is that, with the exception of the `"keywords"` entry, **any entry which is not None is placed in a tuple, even if there is only one entry**. (This small amount of rigidity ensures that there is no ambiguity in the specification.)

This requirement is observable in the `arguments` entry for the `manipulate_filenames` function: The function takes one argument, yet the API entry holds that one argument in a tuple. The exceptions entry is similar.

We can see that non-applicable entries can simply be labeled None, or they can be omitted completely.

Another feature can be seen in the arguments for `manipulate_filenames`: Argument types can be descriptive, and are not limited to only strict literal types. Instead of saying `"list"`, or even `"list of str"`, it specifies that it takes a `"list of filename str"`, which indicates what the entries of the list are actually expected to be. 

The third entry, `"apidemo.lib.update_storage"` indicates that it takes an arbitrary number of arguments and keyword arguments. It also lists side effects that calling the function has; If a function manipulates state that other code may access, these are referred to as "side effects", and it is best to document them.

The `_private_function` is not listed in the API specification. This means it may be used by the project internally somewhere, but is not exposed for public use. Any external code that tries to use it will receive no guarantees of compatibility: It can be changed or even removed at any release, and the library is under no obligation to attempt to ensure that external code that uses it does not break. Modifying or removing a private function will not alter the major or minor version number of a project.

The `cached_function` is a public function declared in the API, yet it lists no keyword arguments in the specification despite the function declaring one. Note that the keyword argument in the code is prefixed with an underscore: `_cache`. This indicates that it is a private variable. Similar to the previous private function example, private variables may be used by the project internally, but are not exposed publicly as part of the interface. External code should not use the projects internal private variables, as no guarantees of compatibility are provided. In this example, the `_cache` variable could be removed and the major/minor version would not have to be modified.

Running the version helper
----
Next, try running `python -m versionhelper api`

It should say mention that this is the first run, and that it has not modified the version number (since no changes have been made yet).

A hash digest that stores the state of the source code and API has been saved to the database. Any time the code or the API is modified and `versionhelper` is run, changes will be detected and the version number incremented as appropriate.

Modifying the API
----

There are three types of changes that can happen to the code and the API:

- Major changes are any changes that are not backwards compatible
- Minor changes add new functionality without breaking backwards compatibility
- Patch changes modify code in a way that does not add or break functionality (e.g. bug fixes)

Examples of major changes include:

- removing items from the API
- removing, re-arranging, or modifying positional arguments
- removing or modifying a keyword arguments
- removing, modifying, or adding return types
- removing,modifying, or adding exceptions
- removing side effects

Examples of minor changes include:

- adding items to the API
- adding arguments to a function
- adding keyword arguments to a function
- adding side effects
- adding deprecation warnings to items in the API

Examples of patch changes include:

- re-naming positional arguments (*not* keyword arguments)
- applying bug fixes
- removing exceptions

There are a few exceptions to the above - Sometimes you may, for example, add or replace an exception that is a sub-class of an already listed exception, and so code that catches the super class exception will also catch the newly added sub-class exception. In these cases, you can make use of the `-v` or `--version` arguments to manually specify a new version number that only increments the minor or patch number. Similarly, you might remove an exception; Code that tries to catch it will not be taken. Whether or not this will cause undesirable behavior in the program is a matter of context, so versionhelper must assume that it is a major change.

The default behavior is to assume that any changes that could break compatibility do so.

One final note is that: If the major version is `0`, then this indicates that the API is not yet stable. Any major changes will only increment the minor version number until the major version number is set to `> 1`.

Modifying code and the API
----

In our current example, the version number is `0.1.0`. The major version is `0`, indicating that the api is not yet stable. If we remove functions from the API, then the minor version will be incremented.

Remove the `cached_function` from `lib.py` and run the version checker.

It should raise `libvh.Missing_Api_Function` and say that it's unable to find `apidemo.lib.cached_function`.

This happened because we did not remove the function from our API listing. This is one perk of using `versionhelper` - it helps to maintain the invariant between the declared API and the code. This functionality is optional, and its availability depends on the existence of an invariant checker for the language being used.

Now remove the `cached_function` entry from the API file and run versionhelper again.

It will list any changes, the type of those changes, the overall type of change as a result of these changes, and the new version number.

Note that the change type was a major change because we removed functionality from the API. Also note that it only incremented the minor version number, because we are using the unstable major version `0`.

Suppose the code was ready to be upgraded to version `1.0.0`, but that we'd like to indicate that the release is an alpha release. To do this, run the following command:

    python -m versionhelper api.py -v 1.0.0 -p alpha

The `-v` argument indicates that we are passing an explicit version number for it to set. The `-p` argument indicates that we want to use a prerelease string.

When a prerelease string is used, any changes to the version number will be applied to the prerelease segment, rather than the major/minor/patch segments.

Let's change our mind about removing the `cached_function` and re-add it into the code and the API. Do so, then run the version helper again.

It will state that we added functionality, which is a minor change, and attempts to increment the minor version number for us. Note that the increment is re-directed to the prerelease segment, rather than the minor segment of the version.

Other options
-----

By this point you should have a good idea of how to build an API file and how to use `versionhelper` to accomplish basic tasks.

There are other arguments that are available for when the situation arises:

- `-d` or `--directory` allows you to specify a directory where the source code resides, in case you do not want to keep the API file at the top level of your source tree
- `-b` or `--build_metadata` allows you to specify a build metadata string to go after the version-prerelease information
- `-db` or `--database` allows you to specify the filename of the database that tracks changes
- `-c` or `--checker` allows you to specify a file that contains a custom invariant checker. If you want to use a language that does not have an invariant checker built-in to `versionhelper`, you can specify a python file that holds one here. See "How to write an invariant checker" for more details.
- `-x` or `--extensions` allows you to specify the file extensions of source code that should be examined when determining when code has been modified. By default, `versionhelper` will look for files according to the language that was specified in the `api` file. If your project consists of multiple languages (e.g. python and C), you can specify `py,c` as file extensions this way.
