import sys
import os
import inspect
import imp
import importlib
import threading

import libvh

import pride.functions.utilities


class Local_Importer(object):

    def __init__(self, source_dir):
        self.source_dir = source_dir
        self.source = dict()

    def find_module(self, module, path):
        try:
            _file, filepath, _ = imp.find_module(module, [self.source_dir])
        except ImportError:
            pass
        else:
            self.source[module] = _file.read(), filepath
            _file.close()
            return self

    def load_module(self, module_name):
        thread_count = threading.active_count()
        if thread_count != 1 :
            while imp.lock_held():
                pass
            imp.acquire_lock()

        module = sys.modules.setdefault(module_name, imp.new_module(module_name))

        if thread_count != 1:
            imp.release_lock() # not sure when to release; the following doesn't use shared resources (e.g. sys.modules) other than the module itself
            
        source, filepath = self.source.pop(module_name)
        module_code = compile(source, module_name, "exec")
        is_package = True if len(module_name.split('.')) > 1 else False # not sure, but seems accurate
        module.__file__ = filepath
        module.__loader__ = self
        if is_package:
            module.__path__ = []
            module.__package__ = module_name
        else:
            module.__package__ = module_name.split('.', 1)[0]
        exec module_code in module.__dict__
        #imp.release_lock() # it might be more correct to release the lock here instead of above.
        return module


def check_api_item(function_name, values, source_dir):
    importer = Local_Importer(source_dir)
    try: # works if it is installed
        assert importer not in sys.meta_path
        function = pride.functions.utilities.resolve_string(function_name)
    except (AttributeError, ValueError): # look in source_dir instead
        sys.meta_path.insert(0, importer)
        segments = function_name.split('.')
        for index in range(1, len(segments) + 1):
            module_name = '.'.join(segments[:-index])
            try:
                module = importlib.import_module(module_name)
            except ImportError:
                continue
            else:
                function = getattr(module, '.'.join(segments[index:]))
                sys.meta_path.remove(importer)
                break
        else:
            sys.meta_path.remove(importer)
            raise libvh.Missing_Api_Functionality("Unable to locate {}".format(function_name))
    assert importer not in sys.meta_path
    determine_consistency(function_name, values, function)

def determine_consistency(function_name, values, function):
    api_arguments = values.get("arguments", None) or tuple()
    arg_spec = inspect.getargspec(function)
    try:
        spec_keywords = dict((key, value) for key, value in zip(arg_spec.args[::-1],
                                                                arg_spec.defaults[::-1]))
    except TypeError: # arg_spec.defaults can be None
        spec_keywords = dict()
    if arg_spec.keywords: # kwargs will not be present in spec_keywords as defined above
        spec_keywords["**" + arg_spec.keywords] = ''

    keyword_count = len(spec_keywords)
    spec_positionals = arg_spec.args[:len(arg_spec.args) - keyword_count]
    if arg_spec.varargs:
        spec_positionals.append("*" + arg_spec.varargs)

    api_keywords = values.get("keywords", None) or dict()
    undocumented_keys = []
    for key in spec_keywords.keys():
        if key not in api_keywords:
            if key[0] == '_': # prune _private key word arguments
                del spec_keywords[key]
            else:
                undocumented_keys.append("'{}'".format(key))
    if undocumented_keys:
        message = "\nUndeclared keyword argument(s) found for '{}':".format(function_name)
        message += "\nKeyword(s): " + ', '.join(undocumented_keys)
        message += "\nNot found in API specification"
        raise libvh.Mismatched_Api_Argument(message)

    nonexistant_keys = [key for key in api_keywords.keys() if key not in spec_keywords]
    if nonexistant_keys:
        message = "\nKeyword argument(s) declared in API not found in code for '{}':".format(function_name)
        message += "\nKeyword(s): " + ', '.join(nonexistant_keys)
        message += "\nNot found in code"
        raise libvh.Mismatched_Api_Argument(message)

    if len(spec_positionals) != len(api_arguments):
        message = "\nMismatched positional arguments for '{}'.\n{} argument(s) declared in API, {} argument(s) found in function specifcation"
        message = message.format(function_name, len(api_arguments), len(spec_positionals))
        raise libvh.Mismatched_Api_Argument(message)
