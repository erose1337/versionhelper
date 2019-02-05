What is an invariant checker
-----

When `versionhelper` is run, it attempts to examine the source code and API, and make sure that there are no discrepancies between the two. This feature is provided by an "invariant checker".

Invariant checkers are language specific. As such, only a limited number are currently built in to `versionhelper`.

If your project uses a language that does not have access to a built-in invariant checker, you can write your own. This guide will tell you what an invariant checker should do.

How to write an invariant checker
---

An invariant checker must have a python interface.

The backend that does the processing may be in any language, as long as you can wrap that language and provide a python module.

The front end python interface must offer a function named `check_api_item` that accepts as arguments:

- a key that names API functionality (from the `API` dict in the `api.py` file)
- the values associated with that key
- and a source directory string.

So the definition of `check_api_item` should be like so:

    def check_api_item(api_entry, entry_values, source_directory):
        ...


The `check_api_item` function must attempt to find the corresponding functionality in the source files located in the source directory.

- If the functionality cannot be found, the code must raise a `libvh.Missing_Api_Functionality` exception and specify the name of the functionality that could not be found.

Once the functionality is located, the arguments must be extracted from the `api` entry and compared against the arguments in the code.

For all languages, the checker must check that both the API and code specify the same quantity of positional arguments

- If a differing number of positional arguments is detected, then the code must raise a `libvh.Mismatched_Api_Argument` exception and specify which functionality triggered this.

For languages where it is possible to do so (those that are statically typed), in addition to counting arguments, positional arguments may have their types checked against the types specified in the API.

- If a type-mismatch occurs, code may raise a `libvh.Mismatched_Api_Argument` exception
    - Note: types specified in the `api` are not required to be literal types and may be more descriptive, so a simple equality comparison of strings may result in false positives.

For languages that support keyword arguments, there are two relevant types of mismatch: Undocumented keys and Non-Existent keys.

Undocumented keys are keys that are found in the function signature but are not listed in the API.
- Private variables *are* allowed in the form of _underscore-prefixed names.
    - If private variables are found in the function signature, then they should not count as undocumented keys.
- If undocumented keys are found, then `libvh.Mismatched_Api_Argument` must be raised and specify the relevant functionality, list any undocumented keys for that functionality, and state that those keys are undocumented.

Non-existent keys are keys that are listed in the API but are not found in the function signature.
- If non-existent keys are found, then `libvh.Mismatched_Api_Argument` must be raised and specify the relevant functionality, list any non-existent keys, and state that those keys are non-existent.
