# my_settings.py 개인 로컬 MySQL DB 설정 (.gitignore로 관리)

DATABASES = {
    'default' : {
        'ENGINE': 'django.db.backends.mysql',    
        'NAME': 'schoollog_db',     # 연동할 DB 이름 (로컬 설정)         
        'USER': 'root',                          
        'PASSWORD': '1234',      # 개인 로컬이니 다른 비번 설정 가능      
        'HOST': '127.0.0.1',     # localhost (서버 IP 주소)              
        'PORT': '3306',
    }
}

# SECRET_KEY = ''
