from datetime import datetime, timedelta

def isDateCorrect(date):
    try:
        input_date = datetime.strptime(date, '%d.%m.%y %H:%M')
        if input_date > datetime.now() - timedelta(hours=2):
            return True
        else:
            return False
    except ValueError:
        return False
    


print(datetime.strptime("16.35.2024 15:35", "%Y-%m-%d %H:%M"))