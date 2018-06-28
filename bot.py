# -*- coding: utf-8 -*-
import os
import time
import re
import html
from urllib.parse import urlencode
from urllib.request import Request,urlopen

from slackclient import SlackClient
from slacker import Slacker

from apiclient import discovery
from googleapiclient.http import *
from oauth2client import client, tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# constants
SCOPES = 'https://www.googleapis.com/auth/drive'
TEAMDRIVE_ID = '{TEAMDRIVE_ID}'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Drive API Python Quickstart'
BOT_ID = os.environ.get("BOT_ID")
AT_BOT = "<@" + BOT_ID + ">"
SEARCH_COMMAND = "DOCFIND"  # start command in slack
slack = Slacker(os.environ.get("SLACK_BOT_TOKEN"))
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
GA_URL = "https://www.google-analytics.com/collect"
GA_TID = "{GA_TID}"
DOC_NAME_SUFFIX = "_DOC"

def post_to_channel(message, channel):
    slack.chat.post_message(channel, message, as_user=True)

def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,'drive-python-quickstart.json')
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def search_paragraph_in_document(keyword, channel):
    post_to_channel('Starts the search.... Please wait a moment :)', channel)
    # GA
    details = urlencode({'v' : '1', 'tid' : GA_TID , 'cid' : '{CID}', 't' : '{T}', 'ec' : '{EC}', 'ea' : '{EA}', 'el' : keyword})
    details = details.encode('UTF-8')
    url = Request(GA_URL, details)
    url.add_header("User-Agent","Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.29 Safari/525.13")
    urlopen(url).read()
    count = 0
    result = convert_keyword_unicode(html.unescape(keyword))
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)
    results = service.files().list(corpora="teamDrive", includeTeamDriveItems=True, supportsTeamDrives=True, teamDriveId=TEAMDRIVE_ID).execute()
    items = results.get('files', [])
    if not items:
        print('No files found.')
    else:
        print('Files:')
        list = []
        for item in items:
            if item['name'].find(DOC_NAME_SUFFIX) != -1:
                item['name'] = item['name'].split(DOC_NAME_SUFFIX)[0].encode('utf-8')
                item['id'] = item['id'].encode('utf-8')
                map = {'name' : item['name'], 'id' : item['id']}
                list.append(map)

        if list :
            for item in list :
                file_id = item['id'].decode('utf-8')
                results = service.files().export(fileId=file_id,
                                                 mimeType="text/html").execute(http=http)
                results = results.decode("utf-8")  # without this line, Printing Error!!
                p = re.compile((
                    u'<h[0-9] id="(.*?)"|<span style="color:#\d+;font-weight:\d+;text-decoration:none;vertical-align:baseline;font-size:\d+pt;font-family:&quot;Malgun Gothic&quot;;font-style:normal">(.*?)<\/span>'),
                    re.UNICODE)
                findAll = p.findall(results)
                content = ''
                head_id = ''
                for i in findAll:
                    if i[0]:
                        if content and re.search(u'' + result, content):
                            count += 1
                            answer = "*•" + str(count) + " search results* // Author. _"+item['name'].decode('utf-8')+"_\n" + "```" + html.unescape(
                                content) + "\n\n" + "[Link] " + "https://docs.google.com/document/d/"+file_id+"/edit#heading=" + head_id + "```"
                            post_to_channel(answer, channel)
                        head_id = i[0]
                        content = ''
                    else:
                        content += '\n' + i[1]

    post_to_channel('A total of '+str(count)+'search results were found.', channel)

def convert_keyword_unicode(kword):
    pre = '&#'
    suf = ';'
    result = ''
    pattern = r'[가-힣]+'
    for stt in kword:
        if re.search(pattern, stt):
            result += (pre + str(ord(stt)) + suf)
        else:
            result += html.escape(stt)
    return result

def parse_slack(msg):
    output_list = msg
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and BOT_ID not in output:
                channel = output['channel']
                command = output['text']    # Get text in JSON
                answer = slack_answer(command, channel)    # Go to desk
                if answer :
                    post_to_channel(answer, channel)
    return None


def slack_answer(txt, channel):    # Have Condition
    if txt.find(SEARCH_COMMAND) != -1:
        cmd = txt[7:]
        if len(cmd) < 2 or re.search('[ㄱ-ㅎ]|[ㅏ-ㅣ]', cmd) or re.search('[`~!@#$%^&*_=+;:",./<>?]', cmd) or cmd.find('-') != -1 or cmd.find('\'') != -1 or cmd.find('[') != -1 or cmd.find(']') != -1 or cmd.find('{') != -1 or cmd.find('}') != -1 or cmd.find('(') != -1 or cmd.find(')') != -1 or cmd.find('|') != -1 or cmd.find('\\') != -1:
            post_to_channel('*Search keywords can only contain words that do not contain more than one special character.*', channel)
            return None
        search_paragraph_in_document(txt[7:], channel)
        return None
    else:
        return None

    return answer

if __name__ == "__main__":
    if slack_client.rtm_connect():
        print("Connected!")
        while True:
            parse_slack(slack_client.rtm_read())
            time.sleep(1)
    else:
        print("Connection failed.")
