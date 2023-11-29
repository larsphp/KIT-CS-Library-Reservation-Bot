from datetime import date, timedelta
import requests, re

def format_line(string):
    return string.strip().replace('= ', '=').split('=')[1]

USER_AGENT = {'User-agent': 'Mozilla/5.0'}
BASE_URL = 'https://bib-buchung.informatik.kit.edu'
ADMIN_URL = f'{BASE_URL}/admin.php'
ENTRY_URL = f'{BASE_URL}/edit_entry.php'
ENTRY_HANDLER_URL = f'{BASE_URL}/edit_entry_handler.php'

COLOR_ABBREVIATIONS = {
    'aqua': 'a',
    'blue': 'b',
    'fuchsia': 'f',
    'gray': 'G',
    'green': 'g',
    'lime': 'l',
    'olive': 'O',
    'orange': 'o',
    'purple': 'p',
    'red': 'r',
    'silver': 's',
    'teal': 't',
    'wheat': 'w',
    'yellow': 'y'
}

#get csrf token
try:
    r = requests.get(ADMIN_URL)
    pattern = r'"csrf_token" value="([^"]+)"'
    matches = re.findall(pattern, r.text)
    csrf_token = matches[0]
    cookie = r.cookies['MRBS_SESSID']
except:
    print('Error: Connection failed. Check your VPN connection.')
    exit()

#read data from file
with open('settings.txt', 'r') as f:
    username = format_line(f.readline())
    password = format_line(f.readline())
    room = format_line(f.readline())
    days = int(format_line(f.readline()))
    time = format_line(f.readline())
    duration = format_line(f.readline())
    name = format_line(f.readline())
    desc = format_line(f.readline())
    color = format_line(f.readline())

#get hour and minute
hour = time.split(':')[0]
minute = time.split(':')[1]
minute = ('0' if minute != '30' else '30')

#get color
if color in COLOR_ABBREVIATIONS:
    color = COLOR_ABBREVIATIONS[color]
else:
    color = 'g'

#set room number
if room not in ['1.5', '1.6', '1.7']:
    room = '1.7'
room_num = int(room.split('.')[1]) - 4

#check if days is between 0 and 14
if days < 0 or days > 14:
    days = 14

#check if duration is between 0 and 3
if duration not in ['0.5', '1', '1.5', '2', '2.5', '3']:
    duration = '1'

#check if name is set
if name == '':
    name = 'Buchung'

#check if hour is valid
if int(hour) <= 8 or int(hour) > 16:
    hour = '12'

#login
payload = {
    'csrf_token': csrf_token,
    'username': username,
    'password': password,
    'action': 'SetName',
    'returl': '', 
    'target_url': 'index.php'
}
cookies = {'MRBS_SESSID': cookie}

r = requests.post(ADMIN_URL, data=payload, headers=USER_AGENT,
                  cookies=cookies, allow_redirects=False)

#get cookie
cookie = r.cookies['MRBS_SESSID']

#calculate the date in n days
dateIn3Days = date.today() + timedelta(days=days)
dateIn3Days = dateIn3Days.strftime("%Y-%m-%d")
dayIn3Days = dateIn3Days.split('-')[2]
monthIn3Days = dateIn3Days.split('-')[1]
yearIn3Days = dateIn3Days.split('-')[0]

#calculate start and end seconds
start_seconds = int(hour) * 3600 + int(minute) * 60
end_seconds = start_seconds + int(float(duration) * 3600)

#get csrf token
cookies = {'MRBS_SESSID': cookie}   
r = requests.get(f'{ENTRY_URL}?view=day&year={yearIn3Days}&month={monthIn3Days}&day={dayIn3Days}&area=1&room={room}&hour={hour}&minute={minute}',
                 cookies=cookies, headers=USER_AGENT, allow_redirects=False)
pattern = r'"csrf_token" value="([^"]+)"'
matches = re.findall(pattern, r.text)
csrf_token = matches[0]

#book
payload = {
    'csrf_token': csrf_token,
    'create_by': username, 
    'start_date': dateIn3Days,
    'start_seconds': start_seconds,
    'end_seconds': end_seconds,
    'name': name,
    'description': desc,
    'returl': '',
    'rep_id': '0',
    'rooms[]': room_num,
    'type': color,
    'edit_type': 'series'
}
r = requests.post(ENTRY_HANDLER_URL, headers=USER_AGENT,
                  cookies=cookies, data=payload, allow_redirects=False)

#check if booking was successful
if 'Konflikt' in r.text:
    print('Konflikt')
else:
    print('Buchung erfolgreich am ' + dateIn3Days + ' um ' + time + ' Uhr für '
          + duration + ' Stunden in Raum ' + room + ' mit dem Namen '
          + name + ' und der Beschreibung '
          + desc + ' und der Farbe ' + color + '.')
