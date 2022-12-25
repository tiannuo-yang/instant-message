import json

def get_user_info():
    with open(r'user_info.json', 'r') as f:
        user_info_2 = json.load(f)
    return user_info_2

def get_logger():
    with open(r'logger.json', 'r') as f:
        logger_2 = json.load(f)
    return logger_2

def set_user_info(r,c,t): 
    with open(r'user_info.json', 'r') as f:
        user_info_2 = json.load(f)
    user_info_2[r][c] = t
    with open(r'user_info.json', 'w') as f:
        json.dump(user_info_2,f)

def add_logger(time, text): 
    with open(r'logger.json', 'r') as f:
        logger_2 = json.load(f)
    logger_2.append([time,text])
    with open(r'logger.json', 'w') as f:
        json.dump(logger_2,f)

def delete_user(r):
    with open(r'user_info.json', 'r') as f:
        user_info_2 = json.load(f)
    del user_info_2[r]
    with open(r'user_info.json', 'w') as f:
        json.dump(user_info_2,f)

