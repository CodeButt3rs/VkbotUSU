import vk_api
import psycopg2
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
load_dotenv()
def main(group):
    import requests as req
    resp = req.get(f"http://timetable.ugrasu.ru/index.php/timetable/show_timetable/group/{group}")
    resp.encoding = 'UTF-8'
    soup = BeautifulSoup(resp.text, 'lxml')
    timetable = soup.find('table', id = 'timetable')
    final = timetable.find_all(['tbody', 'thead'])
    sublist = []
    counter = 0
    json = {}

    while counter <= 10:
        sublist.append(final[counter:counter +2])
        counter += 2

    for n, i in enumerate(sublist, start=1):
        dayOfWeek = " ".join(i[0].tr.td.div.getText().split())
        json[dayOfWeek] = []
        for j in i[1]:
            if len(j) == 1:
                continue
            try:
                k = j.find_all('td')
                timeOfSubject = f'⌚Время: {" - ".join(k[1].getText().split())}'
                subject = f'🛠️Предмет: {" ".join(k[2].getText().split())}'
                teacher = f'👨‍🏫Препод👩‍🏫: {" ".join(k[3].getText().split())}'
                potok = f'➡️Поток: {" ".join(k[4].getText().split())}'
                room = f'🏠Кабинет: {" ".join(k[5].getText().split())}'
                para = {
                    'name': subject,
                    'time': timeOfSubject,
                    'teacher': teacher,
                    'parallel': potok,
                    'room': room
                }
                json[dayOfWeek].append(para)
            except:
                para = {'name': 'Занятий нет...'}
                json[dayOfWeek].append(para)
    return json

def MsgMaker(group):
    msgString = '🗺️Расписание\n'
    json = main(group)
    for i in json:
        msgString += f'---------\n🎇{i}\n'
        for j in json[i]:
            msgString += '\n'
            for k in j:
                msgString += f'{j[k]}\n'
    return(msgString)

vk_session = vk_api.VkApi(token=os.environ.get('TOKEN'))

con = psycopg2.connect(
    database = os.environ.get('DBNAME'),
    user = os.environ.get('DBUSER'),
    password = os.environ.get('DBPWD'),
    host = os.environ.get('DBHOST')
)

cur = con.cursor()

longpoll = VkBotLongPoll(vk_session, os.environ.get('GROUPID'))
vkbot = vk_session.get_api()

print('Online')
for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        if event.from_chat:
            if '!группа' in str(event):
                print(event.message.text)
                l = event.message.text.split()
                print(l)
                if len(l) == 2:
                    if l[1].isdigit():
                        cur.execute(f'SELECT chat_id FROM vkbot WHERE chat_id = {event.chat_id}')
                        fetch = lambda f: None if f is None else f[0]
                        id = fetch(cur.fetchone())
                        print(id)
                        if id == None:
                            cur.execute(f'INSERT INTO vkbot(chat_id) VALUES({event.chat_id})')
                            con.commit()
                        cur.execute(f'UPDATE vkbot SET group_number = {int(l[1])} WHERE chat_id = {event.chat_id}')
                        con.commit()
                        vkbot.messages.send( 
                        chat_id=event.chat_id,
                        message=f'Номер группы успешно занесён в базу данных!',
                        random_id = get_random_id())
                    else:
                        vkbot.messages.send( 
                        chat_id=event.chat_id,
                        message='Требуется число!',
                        random_id = get_random_id()
                        )
                else:
                    vkbot.messages.send( 
                        chat_id=event.chat_id,
                        message='Напиши номер группы согласно ссылке в расписании группы!\nКак его узнать -> https://vk.cc/c5Al4P \nКак узнаешь, пиши - !группа #Номергруппы',
                        random_id = get_random_id()
                    )
            if '!расписание' in str(event):
                cur.execute(f'SELECT group_number FROM vkbot WHERE chat_id = {event.chat_id}')
                fetch = lambda f: None if f is None else f[0]
                id = fetch(cur.fetchone())
                if id is None:
                    vkbot.messages.send( 
                    chat_id=event.chat_id,
                    message='Нужно ввести номер вашей группы! Напиши !группа для подробностей',
                    random_id = get_random_id()
                    )
                else:
                    print(event.chat_id)
                    vkbot.messages.send( 
                        chat_id=event.chat_id,
                        message=MsgMaker(id),
                        random_id = get_random_id()
                    )