[versionhelper](https://erose1337.github.io/versionhelper/)
==============

Automatically increment semantic version number based on changes in the api and source code

How to use:

    python -m versionhelper.main ./pathtomyproject/api.py

And the api and code will be examined for changes, and the version number in `api.py` incremented accordingly.

You will need to create an `api.py` file before you can use `versionhelper` - but it's probably a good idea to have an explicitly written api anyways! See [this file](https://github.com/erose1337/versionhelper/blob/master/versionhelper/docs/howtoapi.md) for a how-to guide to writing an api file.

`versionhelper` is not limited to python projects. But certain helpful features, such as checking the invariant between the code and api, are language dependent.


# Detect differences between your official api and what is defined in the code

When operating on a supported language, `versionhelper` will check to ensure that the code matches what the api offers (to the extent that this is reasonably possible).

For python, which is currently the only language with this feature built-in, this means that function arguments and keyword arguments are checked against the api.

If you desire this functionality but your project is not written in python, you can [write your own invariant checker](https://github.com/erose1337/versionhelper/blob/master/versionhelper/docs/how_to_write_an_invariant_checker.md). And if you want to be really helpful, you can make a pull request to have it included with `versionhelper` by default.

You can stil use `versionhelper` without an invariant checker - this functionality is optional (but helpful!)


# Isn't this an unsolvable problem?

It's version *helper*, not version *solver*. It will still require programmer intervention at certain points, but should in general be helpful.

Incrementing the patch number and maintaining the invariant between the api file and code are both tedious tasks that `versionhelper` is very useful for.

It also may help to prevent accidental modifications that break backwards compatibility.


# Dependencies

- [pride](https://github.com/erose1337/pride) (available on github; **not yet available via `pip install`**)

# Installation

- Download and install pride (the dependency linked above)
- Download the contents of the repo and run `python setup.py install` (using `sudo` if appropriate)
