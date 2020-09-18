import pride.components.database

class API_Database(pride.components.database.Database):

    schema = {"Api_Info" : ("project TEXT PRIMARY_KEY UNIQUE",
                            "digest BLOB", "api BLOB")}
    primary_key = {"Api_Info" : "project"}
    defaults = {"database_name" : "api.db"}
