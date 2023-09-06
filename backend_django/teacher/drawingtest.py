import os
from collections import defaultdict
from google.cloud import automl_v1beta1
from PIL import Image, ImageDraw
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'C:\tree-392720-f06af2faa92c.json'

# 'content' is base-64-encoded image data.
def get_prediction(content, project_id, model_id):
    prediction_client = automl_v1beta1.PredictionServiceClient()

    name = 'projects/{}/locations/us-central1/models/{}'.format(project_id, model_id)
    payload = {'image': {'image_bytes': content}}
    params = {}

    request = prediction_client.predict(name=name, payload=payload, params=params)
    return request  # waits till request is returned


def visualize_detection_results(detection_results, image_path):
    # 이미지 열기
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    dic = defaultdict(str)

    dic["branch"] = ""
    dic["flower"] = ""
    dic["fruit"] = ""
    dic["leaf"] = ""
    dic["root"] = ""


    # 객체 이름과 해당 객체에 대한 문구 매핑
    object_to_sentence = {
        "branch": "그림을 통해 당신의 자아 정체감이 높다는 것을 알 수 있어요. 당신은 자신의 정체성을 확립하고 있으며, 타인에게 자신을 잘 표현할 수 있는 사람이네요.",
        "flower": "당신은 삶에 대한 긍정적인 태도를 가지고 있으며, 행복한 마음을 가지고 있네요!",
        "fruit": "혹시 스트레스를 많이 받고 있지는 않나요? 스트레스 해소를 위한 방법을 찾아보는 건 어떨까요? 혼자 찾기 힘들다면 당신을 도와줄 수 있어요!",
        "leaf": "당신은 감수성이 풍부하군요. 세상의 넓게 관찰하고 아름답게 보는 눈을 가지고 있네요. 다만, 그러한 장점이 때때로 당신을 힘들게 하기도 하네요. 요즘 학업으로 인해 스트레스를 받고 있지 않나요? 혼자 해결하기 힘들다면 상담을 통해 해결해 보는 것은 어때요?",
        "root": "결정되지 않은 일들과 과거에 대한 후회가 당신을 힘들게 할 때가 있네요. 당신은 종종 친구들이나 가족 등 주변 사람들에게 의존하고 싶은 경향을 보이기도 해요.\n",
        }
           
    # 객체 탐지 결과 확인
    detected_objects = set()
    for result in detection_results.payload:
        display_name = result.display_name
        score = result.image_object_detection.score

        # 점수가 일정 이상인 객체만 출력하고 객체 이름 기록, 중복 객체 방지
        if score > 0.5 and display_name in object_to_sentence and display_name not in detected_objects:
            sentence = object_to_sentence[display_name]
            print(sentence)
            dic[display_name] = sentence
            detected_objects.add(display_name)

    # 객체가 탐지되지 않은 경우에 대한 문구 출력
    for object_name in object_to_sentence:
        if object_name not in detected_objects:
            no_object_sentence = {
                "branch": "그림 속 가지를 확인해보니 당신은 아직 자아 정체감이 발달하지 않았을 수 있어요. 아직 자신의 정체감에 대한 혼란을 겪고 있으며, 타인에게 자신을 잘 표현하는 데 어려움을 겪고 있기도 하네요. 챗봇과의 대화는 자신에 대해 알아가고 자아 정체감을 형성할 기회가 될 거예요!",
                "flower": "요즘 마음이 힘들지는 않나요? 때때로 삶이 부정적으로 느껴지고 우울한 마음이 생길 수도 있어요. 챗봇과 대화를 통해 자신의 감정을 표현하고, 스트레스를 해소하는 건 어때요?",
                "fruit": "스트레스를 잘 관리하는 것 같아요. 당신만의 스트레스를 해소법이 법이 궁금해요!",
                "leaf": "요즘 마음속 공허함이 들지는 않나요? 도움이 필요하다면 상담을 통해 해결해 보는 것은 어떨까요? ",
                "root": "본인의 능력에 대해 객관적으로 판단하고 신뢰하고 있군요. 스스로의 믿음은 어려움을 헤쳐갈 수 있는 큰 원동력이 될 거에요.",
            }
            sentence = no_object_sentence[object_name]
            print(sentence)
            dic[object_name] = sentence
    
        
    # 마무리 멘트

    data = {
        'branch' : dic["branch"],
        'flower' : dic["flower"],
        'leaf' : dic["leaf"],
        'root' : dic["root"],
        'fruit' : dic["fruit"]
    }

    return data


