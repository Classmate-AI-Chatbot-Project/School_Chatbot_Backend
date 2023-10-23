from django.views import View
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from django.core.files.base import ContentFile
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated
from .models import User
from account.models import User
from chat.models import ConsultResult
from teacher.serializers import ResultSerializer
import requests, jwt
from backend_django.settings  import SECRET_KEY
from django.contrib.auth import authenticate, login, logout
from django.core.files import File
from PIL import Image
from django.http import JsonResponse
from PIL import Image
from io import BytesIO
import base64
import os

# Create your views here.

#kakao 로그인 하면 email, nickname, photo정보로 임시가입
class kakao_login(APIView):    
    def post(self, request):
        try:
            code = request.data.get("code") # 프론트에서 보내준 code로 token을 구해와야한다 !! 

            data = {
                "grant_type"    :"authorization_code",
                "client_id"     :"2d9ed17578b0549eedac781a79515516",
                "redirect_uri": "http://schoollog.kro.kr/account/kakao/callback",
                "code": code
            }

            kakao_token_api = "https://kauth.kakao.com/oauth/token"
            token_headers = {
            'Content-type': 'application/x-www-form-urlencoded;charset=utf-8'
        }
            access_token = requests.post(kakao_token_api, data=data, headers=token_headers).json()["access_token"]

            # 성공 ! 이 token으로 kakao api와 대화 가능
            # 밑에는 기본적인 user data
            user_data = requests.get(
                "https://kapi.kakao.com/v2/user/me",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
                },
            )

            # email, nickname, photo 가져옴
            user_data = user_data.json()
            email = user_data['kakao_account']['email']
            nickname = user_data['properties']['nickname']
            photo = user_data['properties']['profile_image']
            token = jwt.encode({"email": email}, SECRET_KEY) #카톡 token을 자체 jwt token으로 변경해줌

            user = authenticate(request, email=email, password=token)
            if user is None:
                new_user = User.objects.create_user(email=email, username=nickname, password=token)
                user = authenticate(request, email=email, password=token)
                print(user)
                if photo:
                    response = requests.get(photo)
                    if response.status_code == 200:
                        file_name = photo.split('/')[-1]
                        new_user.profile_photo.save(file_name, ContentFile(response.content), save=True)
                new_user.save()
                print("회원 없어서 생성/ 학교, 직업 생성해야 함.")

            return Response(token)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
#google 로그인 하면 email, nickname, photo정보로 임시가입
class google_login(APIView):    
    def post(self, request):
        try:
            code = request.data.get("code") # 프론트에서 보내준 code로 token을 구해와야한다 !! 
            print("code:", code)

            client_id = '793203864825-bgnnqpfmg3oseutieg9onr478j3hcroj.apps.googleusercontent.com'
            client_secret = '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'
            redirect_uri = "http://schoollog.kro.kr/account/google/callback"
            state = "random_string"

            # 액세스 토큰 교환
            response = requests.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'code': code,
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'redirect_uri': redirect_uri,
                    'grant_type': 'authorization_code',
                }
            )
            data = response.json()
            access_token = data['access_token']

            # 성공 ! 이 token으로 google api에서 사용자 정보 불러옴
            user_info_response = requests.get(
                f'https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}'
            )
            user_data = user_info_response.json()

            # email, nickname, photo 가져옴
            email = user_data['email']
            nickname = user_data['name']
            photo = user_data['picture']
            token = jwt.encode({"email": email}, SECRET_KEY) #카톡 token을 자체 jwt token으로 변경해줌

            user = authenticate(request, email=email, password=token)
            if user is None:
                new_user = User.objects.create_user(email=email, username=nickname, password=token)
                user = authenticate(request, email=email, password=token)
                print(user)
                if photo:
                    response = requests.get(photo)
                    if response.status_code == 200:
                        file_name = photo.split('/')[-1]
                        new_user.profile_photo.save(file_name, ContentFile(response.content), save=True)
                new_user.save()
                print("회원없어서 생성/ 학교, 직업 생성해야함.")

            return Response(token)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
#naver 로그인 하면 email, nickname, photo정보로 임시가입
class naver_login(APIView):    
    def post(self, request):
        try:
            code = request.data.get("code") # 프론트에서 보내준 code로 token을 구해와야한다 !! 
            print("code:", code)

            client_id = 'N2pHYJkFjc2tY4jtGNRE'
            client_secret = 'KVtGsWwUmH'
            redirect_uri = "http://schoollog.kro.kr/account/naver/callback"
            naver_uri = 'https://nid.naver.com/oauth2.0/token?grant_type=authorization_code&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}&code=${code}'

            # 액세스 토큰 교환
            response = requests.post(
                'https://nid.naver.com/oauth2.0/token',
                data={
                    'code': code,
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'redirect_uri': redirect_uri,
                    'grant_type': 'authorization_code',
                }
            )
            data = response.json()

            access_token = data['access_token']

            # 성공 ! 이 token으로 naver api와 대화 가능
            # 밑에는 기본적인 user data
            user_info_response = requests.get(
                "https://openapi.naver.com/v1/nid/me",
                headers={
                    "Authorization": f"Bearer {access_token}"
                },
            )
            user_data = user_info_response.json()

            print('user:', user_data)

            # email, nickname, photo 가져옴
            email = user_data['response']['email']
            nickname = user_data['response']['name']
            photo = user_data['response']['profile_image']
            token = jwt.encode({"email": email}, SECRET_KEY) #카톡 naver 자체 jwt token으로 변경해줌

            print("email : ", email, "nickname : ", nickname, "photo :", photo)

            user = authenticate(request, email=email, password=token)
            if user is None:
                new_user = User.objects.create_user(email=email, username=nickname, password=token)
                user = authenticate(request, email=email, password=token)
                print(user)
                if photo:
                    response = requests.get(photo)
                    if response.status_code == 200:
                        file_name = photo.split('/')[-1]
                        new_user.profile_photo.save(file_name, ContentFile(response.content), save=True)
                new_user.save()
                print("회원없어서 생성/ 학교, 직업 생성해야함.")

            return Response(token)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

# 회원가입
class SignUp(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        nickname = request.data.get('nickname', None)
        school = request.data.get('school', None)
        school_code = request.data.get('school_code', None)
        print(school_code)
        job = request.data.get('job', None)

        user = request.user

        user.username = nickname
        user.school = school
        user.school_code = school_code
        user.job = job
        user.save()
        return HttpResponse(status=200)

    
# 로그인
class Login(APIView):
    def post(self, request):
        try:
            user_token = request.data.get('token')
            print(user_token)
            decode_jwt = jwt.decode(user_token, SECRET_KEY, algorithms=['HS256'])
            print(decode_jwt)
            account = User.objects.get(email=decode_jwt.get('email'))
            print(account)

            user = authenticate(request, email=account, password=user_token)
            print(user)

            if user is not None:
                login(request, user)
                print("로그인 완료", user)
                if (user.job==None or user.school==None):
                    print("회원 이미 존재/ 학교, 직업 생성해야함.")
                    return Response(status=status.HTTP_201_CREATED)
                else:
                    return Response(status=status.HTTP_202_ACCEPTED)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        

# 로그아웃
class LogOut(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logout(request)

        return Response(status=status.HTTP_200_OK)
    
# 탈퇴
class Leave(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        request.user.delete()
        logout(request)

        return Response(status=status.HTTP_200_OK)
    


# 프론트로 UserSerializer 보낼 때 사용 (유저 정보 보낼 때)
class decode(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        student_serializer = UserSerializer(user)  # User 객체를 직렬화
        student_chatResult = ConsultResult.objects.filter(member_id=user) 
        result_serializer = ResultSerializer(student_chatResult, many=True) #접근한 학생의 상담 결과를 직렬화

        print(result_serializer)

        data = {
            'student' : student_serializer.data,
            'consult_result' : result_serializer.data
        }

        return JsonResponse(data)
    

# 별명 중복확인
class exist(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print(request.data)
        username = request.data.get('nickname')
        print(username)
        if User.objects.filter(username=username).exists(): #아이디 중복 체크 
            print("이미 존재하는 계정")
            return Response(status=200)
        else:
            print("존재하지않는 별명")
            return Response(status=201)
        
        # student_serializer = UserSerializer(user)  # User 객체를 직렬화
        # student_chatResult = ConsultResult.objects.filter(member_id=user) 
        # result_serializer = ResultSerializer(student_chatResult, many=True) #접근한 학생의 상담 결과를 직렬화

        # data = {
        #     'student' : student_serializer.data,
        #     'consult_result' : result_serializer.data
        # }

class EditProfile(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            user = request.user
            new_profile_data = request.data

            user.username = new_profile_data.get('username', user.username)
            user.school = new_profile_data.get('school', user.school)
            user.job = new_profile_data.get('job', user.job)
            profile_photo = new_profile_data.get('profile_photo')  # 이미지 파일
            print(profile_photo)

            if "media" not in profile_photo:
                print("if문 안입니다.")
                _, data = profile_photo.split(',', 1)
                image_data = base64.b64decode(data)

                # 이미지를 Pillow Image 객체로 변환
                image = Image.open(BytesIO(image_data))
                
                image.save(f'media/{user.email}.png', 'PNG')
                user.profile_photo = f'{user.email}.png'

            user.save()

            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def check_nickname_availability(request):
    nickname = request.data.get('nickname')

    # 닉네임이 이미 사용 중인지 확인합니다.
    if User.objects.filter(username=nickname).exists():
        # 이미 사용 중인 경우
        return Response({'available': False}, status=status.HTTP_200_OK)
    else:
        # 사용 가능한 경우
        return Response({'available': True}, status=status.HTTP_200_OK)
