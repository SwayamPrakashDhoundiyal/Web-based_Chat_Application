from werkzeug.security import check_password_hash
class User:
    def __init__(self,username,email,password):
        self.username = username
        self.email = email
        self.password = password
    @staticmethod
    def is_authencticated(self):
        return True
    
    @staticmethod
    def is_active(self):
        return True
    
    @staticmethod
    def is_anonymus(self):
        return False
    
    def get_id(self):
        return self.username
    
    def check_password(self, password_input):
        return check_password_hash(self.password, password_input)