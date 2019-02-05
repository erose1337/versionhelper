VERSION = "0.12.0"
LANGUAGE = "python"
PROJECT = "versionhelper"

API = {"libvh.version_helper" : {"arguments" : ("filename str", ),
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
                                                 "Mismatched_Api_Argument"),
                                 "side_effects" : ("Modifies api VERSION",
                                                   "Modifies database",
                                                   "Overwrites apichangelog.txt")},
        "libvh.parse_version" : {"arguments" : ("version str", ),
                                 "returns" : ("str", "str", "str", "str", "str")}
       }
