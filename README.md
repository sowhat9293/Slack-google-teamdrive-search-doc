Slack-google-teamdrive-search-doc
=
```
Google Teamdrive에 공유되어 있는 Document 파일들을 검색하여 사용자가 입력한 Keyword가 존재하는 문단 내용과 URL 출력
```  
# Step1. Install
```
pip install slackclient
pip insatll slacker
pip install --upgrade google-api-python-client
```  
  
# Step2. Get Slack BOT ID
```
1. Create Slack Bot

$ curl https://DOMAIN.slack.com/api/auth.test?token=API_TOKEN
## Json Response 중 user_id 이후에 나오는 값이 Slack BOT ID
```

# Step3. Get client_secret.json (Google)
```
1. Create Project
2. 사용자 등록 -> oauth2 -> 기타 -> client_secret.json Download
```

# Step4. Export Env
```
$ export SLACK_BOT_TOKEN="{SLACK_BOT_TOKEN}"
$ export BOT_ID="{BOT_ID}"
```
