import libvh

def check_api_items(api, source_dir, checkers):
    for item, values in api.items():
        for checker in checkers:
            try:
                checker.check_api_item(item, values, source_dir)
            except (libvh.Missing_Api_Functionality, libvh.Mismatched_Api_Argument):
                continue
            else:
                break
        else:
            raise
