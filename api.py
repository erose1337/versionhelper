VERSION = "1.0.0-beta.11"
LANGUAGE = "python"
PROJECT = "versionhelper"

_p = "versionhelper.libvh."
API = {_p + "version_helper" : {"arguments" : ("filename str", ),
                                "keywords" : {"directory" : "directory str",
                                              "version" : "str",
                                              "prerelease" : "str",
                                              "build_metadata" : "str",
                                              "db" : "filename str",
                                              "checker" : "filename str",
                                              "source_types" : "iterable of str",
                                              "no_invariant_check" : "bool",
                                              "dry_run" : "bool",
                                              "silent" : "bool"},
                                 "returns" : None,
                                 "exceptions" : ("ValueError", "Missing_Api_Function",
                                                 "Mismatched_Api_Argument",
                                                 "Missing_Api_Info"),
                                 "side_effects" : ("Modifies api VERSION",
                                                   "Modifies database",
                                                   "Overwrites apichangelog.txt")},
        _p + "parse_version" : {"arguments" : ("version str", ),
                                 "returns" : ("str", "str", "str", "str", "str")}
       }
