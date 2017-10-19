#!/usr/bin/env python3.5
#-*- coding: utf-8 -*-

import telepot
import time
import logging
import json
import pprint
import urllib
import sys
from _ctypes import Array
import datetime
import re
import socket


#reload(sys)
#sys.setdefaultencoding('utf-8')

class SlaveBot(telepot.Bot):
    token=''
    admin_id=[]
    public_room=[]
    menu = {}
    url = ""
    apiKey = ""
    redmine = ""
    sended = {}
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path =  '/var/run/slavebot.pid'
        self.pidfile_timeout = 5
        super(SlaveBot, self).__init__(self.token)
        self._answerer = telepot.helper.Answerer(self)

    def run(self):
        self.redmine = Redmine()
        try:
            self.message_loop(self.handle)
            log.debug('Listening ...')
            self.sended['news']=0
            self.sended['weeklyreport']=0
            while 1:
                today = datetime.datetime.now().strftime('%m/%d')
                nowtime = datetime.datetime.now().strftime('%H:%M')
                sendkey = datetime.datetime.now().strftime('%m%d%H%M')
                weekday = datetime.datetime.now().isoweekday()
                print("weekday : %d" % weekday)
                if nowtime == "08:30" and self.sended['news'] == 0: # 아침 08:30이고 공지한 적이 없으면                    data = self.redmine.search("news") #뉴스를 가져와서
                    for item in data: #하나씩 돌려보면서

                        if item['title'][:5] == today: #같은 날짜가 있으면
                            if self.sended['news'] == 0:
                                # 공지한적 없으면 제목을 띄움
                                log.debug('오늘 뉴스 자동 공지')
                                self.sendMessage(self.public_room,"<< %s 삼팟 늬우스>>\n" % today)
                            self.sended['news'] = 1
                            str = item['title'] + item['description']
                            #self.sendMessage(152313050,"<< %s 삼팟 늬우스>>\n%s " % (today, str)) # 테스트방 (내꺼)
                            cleanr = re.compile('<.*?>')
                            cleantext = re.sub(cleanr, '', str)
                            self.sendMessage(self.public_room, cleantext)
                            print(today,cleantext)
                elif nowtime=="00:00": # 알람 초기화
                    self.sended['news']=0
                    self.sended['weeklyreport']=0
                elif weekday == 4 and nowtime == "15:00" and self.sended['weeklyreport'] == 0:
                    self.sended['weeklyreport'] = 1
                    self.sendMessage(self.public_room, "주간보고 작성!! http://goo.gl/eMKiw6")

                time.sleep(10)

        except Exception as e:
            log.exception("Main loop error")

    def handle(self, msg):
        flavor = 'normal'
        # normal message
        if flavor == 'normal':
            content_type, chat_type, chat_id = telepot.glance(msg)
            log.info('Normal Message:%s %s %s', content_type, chat_type, chat_id)
            log.debug(json.dumps(msg, ensure_ascii=False))
            command = msg['text']
            from_id = msg['from']['id']
            chat_id = msg['chat']['id']
            log.debug(command)

            if not command.startswith('/'): # 명령커맨드일 경우
                return

            keyword = command[1:].split(' ')

            if not from_id in self.admin_id:
                log.debug(" 권한 없는 사용자(%d)가 봇을 호출" % from_id)
                if keyword[0] != "nslookup":
                    self.sendMessage(chat_id,"저는 주인님의 명령만 듣습니다. 본인의 봇을 소환하세요. ")
                    return
                else:
                    exit

            if keyword[0] == "셧다운":
                log.debug(" 셧다운 시작 - %d" % from_id)
                self.sendMessage(chat_id,"모든 서버를 셧다운 합니다.")

            elif keyword[0] == "하이":
                self.sendMessage(chat_id,"반갑구만 반가워요")

            elif keyword[0] == "nslookup":
                self.sendMessage(chat_id,keyword[1] + " : " + socket.gethostbyname(keyword[1]))


            elif keyword[0] == "정보":
                self.sendMessage(chat_id,"chat_id:%s\nfrom_id:%s"%(chat_id, from_id))

            elif keyword[0] == "뉴스":
                today = datetime.datetime.now().strftime('%m/%d')
                data = self.redmine.search("news")
                for item in data: #하나씩 돌려보면서
                    if item['title'][:5] == today: #같은 날짜가 있으면
                        # 공지한적 없으면 제목을 띄움
                        log.debug('오늘 뉴스 수동 공지')
                        self.sendMessage(self.public_room,"<< 금일 늬우스>>\n")
                        str = item['title'] + item['description']
                        #self.sendMessage(152313050,"<< %s 삼팟 늬우스>>\n%s " % (today, str)) # 테스트방 (내꺼)
                        cleanr = re.compile('<.*?>')
                        cleantext = re.sub(cleanr, '', str)
                        self.sendMessage(self.public_room, cleantext)
                        print(today,cleantext)

            elif keyword[0] == "검색": # 토렌트 검색해야지
                if chat_id in self.public_room: # 채팅방이 공방이면
                    self.sendMessage(chat_id, "공개방입니다.\n 봇을 따로 소환해 검색하세요")
                    return

                result = self.get_search_list(' '.join(keyword[1:]))
                self.set_menu(chat_id, from_id,result)

            elif keyword[0] == "스샷":
                from selenium import webdriver
                today = datetime.datetime.now().strftime('%Y%m%d')
                imageName = "./images/%s_%s.png" % (today, chat_id)

                driver = webdriver.PhantomJS()
                driver.set_window_size(1024, 768)
                log.debug(keyword[1] + " => " + imageName)
                driver.get(keyword[1])  # this works fine
                driver.save_screenshot(imageName)
                driver.quit()

                fp = open(imageName, 'rb')
                self.sendPhoto(chat_id,fp)


            else:
                str = {"/셧다운- 모든 서버를 셧다운합니다.",
                        "/검색 - 유범용님의 약점을 검색합니다."}
                str = "\n".join(str)
                self.sendMessage(chat_id,str)

        # inline query - need `/setinline`
        elif flavor == 'inline_query':
            query_id, from_id, query_string = telepot.glance(msg, flavor=flavor)
            print('Inline Query:', query_id, from_id, query_string)

            def compute_answer():
                # Compose your own answers
                articles = [{'type': 'article',
                                'id': 'abc', 'title': query_string, 'message_text': query_string}]

                return articles

            self._answerer.answer(msg, compute_answer)

        # chosen inline result - need `/setinlinefeedback`
        elif flavor == 'chosen_inline_result':
            result_id, from_id, query_string = telepot.glance(msg, flavor=flavor)
            print('Chosen Inline Result:', result_id, from_id, query_string)


class Redmine():
    url = ""
    apiKey = ""

    def __init__(self):
        print("halo")

    def search(self,keyword):
        from bs4 import BeautifulSoup
        import urllib.request
        url = self.url+"news.xml?key=%s" % self.apiKey
        print(url)
        req = urllib.request.Request(url)
        handle = urllib.request.urlopen(req)
        data = handle.read()
        soup = BeautifulSoup(data,"lxml")
        count = 0
        data = soup.find("news")
        arrData = []
        for item in data:
            if (count>5):
                break
            str = item.find("title").text

            log.debug("%d 제목 : %s" % (count,str))
            d = {
                'title': item.find("title").text,
                'description': item.find("description").text,
               }
            arrData.append(d)
            count = count + 1

        return arrData

def loadConf():
    fp = open(conf_file,'r')
    conf = json.loads(fp.read())
    fp.close()

    SlaveBot.token = conf['telegram']['token']
    SlaveBot.admin_id = conf['telegram']['admin_id']
    SlaveBot.public_room = conf['telegram']['public_room']
    Redmine.url = conf['redmine']['url']
    Redmine.apiKey = conf['redmine']['api-key']


import time
from daemon import runner # python-daemon2
import logging.handlers
#load configuration
conf_file = 'slavebot-settings.json'
loadConf()

bot = SlaveBot()

log = logging.getLogger("SlaveBot")
log.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(name)s:%(levelname)s %(message)s (%(filename)s:%(lineno)s)",
                            datefmt='%Y-%m-%d %H:%M:%S')
handler = logging.handlers.RotatingFileHandler("SlaveBot.log", maxBytes=10240, backupCount=1)
handler.setFormatter(formatter)
handler2 = logging.StreamHandler()
handler2.setFormatter(formatter)
log.addHandler(handler)
log.addHandler(handler2)

if (len(sys.argv)>1 and sys.argv[1] == "foreground"):
    log.info("Foreground mode start")
    log.setLevel(logging.DEBUG)
    log.debug("Debug mode setted.")
    bot.run()
    exit()

daemon_runner = runner.DaemonRunner(bot)
daemon_runner.daemon_context.files_preserve=[handler.stream]
daemon_runner.do_action()