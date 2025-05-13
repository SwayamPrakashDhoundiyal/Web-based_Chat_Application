from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from user import User

client = MongoClient("mongodb+srv://adminUser0:RFD7GDjJbZiQDb4Y@cappuccino.h3cwt8u.mongodb.net/") #connection of the database

chat_db = client.get_database("ChatDB") #name of the database
users_collection = chat_db.get_collection("users") #module of the database to store userdata
user_code_collection = chat_db.get_collection("user_codes") #module of the database to store user's codes
user_message_collection = chat_db.get_collection("messages")
user_request_collection = chat_db.get_collection("requests")

def user_save(username,email,password,personalCode):
    """Save all the data of the user in the database.

    Args:
        username (str): Username
        email (str): E-mail of the user
        password (str): saved in hash form
        personalCode (str): code generated for the user's personal room.
    """
    password_hash = generate_password_hash(password)
    users_collection.insert_one({'_id':username,'email':email,'password':password_hash,'_perCode':personalCode})
    
def get_user(email):
    """Getting email and password hash from the database.

    Args:
        email (str): email of the user

    Returns:
        Class User: data of the user
    """
    user_data = users_collection.find_one({'email': email})
    return User(user_data['_id'],user_data['email'],user_data['password']) if user_data else None

def check_username_email(username,email):
    """Check in the database if the username and email exists or not.

    Args:
        username (str): username to check
    return:
        dict(boolean): structure -> username: boolean,email:boolean.        
    """
    user_email = users_collection.find_one({'email':email})
    user_username = users_collection.find_one({'_id':username})
    email_exist = False
    username_exists = False
    if user_email is not None:
        email_exist = True
    if user_username is not None:
        username_exists = True
    
    return {'username':username_exists,'email':email_exist}

def put_code(username,conn_name,conn_code):
    """To insert a code for a Connection(conn_name) for a given User(username).

    Args:
        username (String): For whom the code is to be stored (User).
        conn_name (String): For whom the code is generated (connection name).
        conn_code (String): The code that is generated.
    """
    user_data = user_code_collection.find_one({'_id':username})
    if user_data is not None:
        code_dict_old = user_data['code']
        code_dict_new = user_data['code']
        code_dict_new[conn_name] = conn_code
        user_code_collection.update_one({'_id':username}, {'$set': {'code': code_dict_new}})
    else:
        code_dict = {conn_name:conn_code}
        user_code_collection.insert_one({'_id': username,'code':code_dict})

def check_code_generated_for(username:str,code:str,conn_name="default"):
    """To check if the given username has already generated a code for the given connection name, 
       it returns a boolean value depending on if the code is generated or not.

    Args:
        username (string): User who is checking.
        conn_name (string): Connection name that's code is to be checked.

    Returns:
        boolean: true if there is a code for the given connection name, false if there
        is none.
    """
    if conn_name != "default":
        user_data = user_code_collection.find_one({'_id':username})
        code_dict = user_data['code']
        
        if code in code_dict:
            return True
        else:
            return False
    else:
        user_data = users_collection.find_one({'_perCode':code})
        if user_data is not None:
            return True
        else:
            return False

def get_code(username,conn_name):
    """To get the connection code between the given User and the connection.

    Args:
        username (String): User
        conn_name (String): Connection

    Returns:
        dict: task-> true if the task is done else false, code-> required code, Error-> error message if the task is not performed
    """
    user_data = user_code_collection.find_one({'_id':username})
    if user_data is not None:
        code_dict = user_data['code']
        if code_dict[conn_name] is not None:
            required_code = code_dict[conn_name]
            return {'task':True,'code':required_code,'Error':None}
        return {'task':False,'code':None,'Error':"There were no connection found"}
        
    else:
        return {'task':False,'code':None,'Error':"Data not found for the user"}
    
def get_user_code(username:str):
    """Get the user code from the database and then return it to the function.

    Args:
        username (str): User

    Returns:
        str: Personal code of the user
    """
    user_data = users_collection.find_one({'_id':username})
    code = user_data['_perCode']
    return code

def get_connect_code_list(username:str):
    """Get's the whole list of contact from the database.

    Args:
        username (str): username for which the contact list is to be fetched

    Returns:
        object: the whole list it's in dict form.
    """
    user_code_data = user_code_collection.find_one({"_id":username})
    if user_code_data is not None:
        contact_connect = user_code_data['code']
    else:
        contact_connect = "default"
    return contact_connect

def put_message_data(connection_code,username,message,time):
    """Makes a message dictionary in which sender->username,message, and time of the message are given.

    Args:
        connection_code (str): basically the name of the connection it is storing to
        username (str): the person that sent it.
        message (str): The actual message.
        time (str): The time mark it was sent in.
    """
    user_message_collection.insert_one({'connection':connection_code,'message':message,'sender':username,'time':time})

def get_message_data(connection_code):
    """retrives the message dictionary for the room which stores all the messagess in the chronological order.

    Args:
        connection_code (str): The contact code or the room code.

    Returns:
        dictionary: Message dictionary that stores all the messages of the room.
    """
    messages = user_message_collection.find({'connection':connection_code})
    list_message = list(messages)
    lenght = len(list_message)
    message_dict = {}
    for i in range(lenght):
        message_dict[i] = {'sender':list_message[i]['sender'],'message':list_message[i]['message'],'time':list_message[i]['time']}
    return message_dict

def get_username(entry,from_code):
    """Makes a list of all the username

    Args:
        entry (str): the username to check for

    Returns:
        dict: all the potential ids
    """
    list_ids = users_collection.distinct("_id")
    result_id = []
    for id in list_ids:
        temp_id = id.lower()
        entry = entry.lower()
        if entry in temp_id:
            result_id.append(id)
    result_dict = {}
    result_code = []
    for id in result_id:
        id_code = get_user_code(id)
        result_code.append(id_code)
    length = len(result_id)
    for i in range(length):
        request = user_request_collection.find_one({'from_code':from_code})
        if request is not None:
            result_dict[i] = {'id':result_id[i],'id_code':result_code[i],'action':False}
        else:
            result_dict[i] = {'id':result_id[i],'id_code':result_code[i],'action':True}
    return result_dict

def request_store(to_code,from_code,from_name):
    """Stores the request data in the database under the user_request_collection.

    Args:
        to_code (str): The code of the one receiving.
        from_code (str): The code of the one sending.
        from_name (str): The one that sent the request.
    """
    request = user_request_collection.find_one({'from_code':from_code})
    if request is not None:
        return "re-request."
    else:
        user_request_collection.insert_one({'username':from_name,'from_code':from_code,'to_code':to_code})
        return "done"

def request_retrieve(for_code):
    """retrieving the request for connection from the server.

    Args:
        for_code (str): The code of the user whom we are retrieving the requests for

    Returns:
        dictionary: dictionary with the username that sent and their code
    """
    request = user_request_collection.find({'to_code':for_code})
    list_of_requests = list(request)
    length = len(list_of_requests)
    request_dict = {}
    for i in range(length):
        request_dict[i] = {'sender':list_of_requests[i]['username'],'code':list_of_requests[i]['from_code']}
    return request_dict

def request_remove(from_code,to_code):
    """Removes the request from the database

    Args:
        from_code (str): the code of the user that had sent the request.
        to_code (str): the code of the user the request was sent to.
    """
    user_request_collection.find_one_and_delete({'to_code':to_code,'from_code':from_code})
