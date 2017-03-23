
class JamaConfig:
    def __init__(self):
        self.username = "username"
        self.password = "password"
        self.auth = (self.username, self.password)
        self.base_url = "https://{base URL}.jamacloud.com"
        self.rest_url = self.base_url + "/rest/v1/"
        self.folder_type_id = 89030
        self.text_type_id = 89031
        self.verify_ssl = True
        self.system_gid_prefix = "GID"
