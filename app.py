"""
Team: 7B
Date: 2023/5/9 ~ 2023/5/12
function: 메인페이지
Stack: Python, MongoDB, ...

Used lib: 가상환경 venv 만들고 pip install해야 할 것들!!
pip install flask requests dnspython pymongo
"""

"""
                  상의성
할거:
1. GET 구현 -> 메인페이지 음식 데이터 가져오기
    - 몽고DB 연결 (Done)
    - get method API 구현 (Done)
    - index.html 가져오고 결과보기 (Done)
2. 파일 업로드 기능 확장
    - 확장자 제한
        Allow: jpg,png,jpeg
            -> 일단은 하나의 모든 이미지 확장자만 허용하는 식 (Done)
                -> 파일 사이즈 제한도 해볼 예정(js 사용할듯? 다른 방법도 있나 찾아보기!)
    - 데스크탑에서 파일 업로드(POST 요청) -> 몽고DB -> 사진 불러오기 (Get 요청)
        * flask 이미지 업로드 방식
            1. static에 집어넣기 ()
            2. gridfs 사용 (이거 사용 예정)
            3. DB에 URL만 저장하며 img 서버를 따로 만들어 두어 DB에서 받아온 URL을 통해 접속 (많이 사용되는 방식이지만, 현재 프로젝트에 부적합)
3. 미정
"""

from flask import Flask, render_template, request, jsonify
from datetime import datetime
app = Flask(__name__)

from pymongo import MongoClient
import certifi
ca=certifi.where()

# 상의성: mongodb+srv://sparta:test@cluster0.fzjk15v.mongodb.net/?retryWrites=true&w=majority
# 조우진 : mongodb+srv://sparta:test@cluster0.89nsamy.mongodb.net/?retryWrites=true&w=majority
client = MongoClient('mongodb+srv://sparta:test@cluster0.89nsamy.mongodb.net/?retryWrites=true&w=majority', tlsCAFile=ca)
db = client.dbsparta

import base64
import gridfs
fs = gridfs.GridFS(db)
# 메인 페이지
@app.route('/')
def home():
   return render_template('index.html')

# 등록된 식당의 수를 가져오는 함수
def get_restaurant_count():
    count = db.yamukja.count_documents({})
    return count

# Post 요청 API: 식당 저장
@app.route('/restaurant', methods=["POST"])
def restaurant_post():
    placeName_receive = request.form['placeName_give']
    address_receive = request.form['address_give']
    picture_receive = request.files['picture_give']
    star_receive = request.form['star_give']
    review_receive = request.form['review_give']

    nickName_receive = request.form['nickname_give'] # 닉네임
    password_receive = request.form['password_give']
    # 등록된 식당 수 가져오기
    restaurant_count = get_restaurant_count()


   # 새로운 식당 번호 생성
    restaurantNum = restaurant_count + 1

    # GridFs를 통해 파일을 분할하여 DB에 저장
    file_img_id = fs.put(picture_receive)
     # DB에 저장 
    doc = {
        'number': restaurantNum,
        'name': placeName_receive,
        'address': address_receive,
        'picture': file_img_id,
        'star': star_receive,
        'review': review_receive,
        'nickname': nickName_receive,
        'password': password_receive
        }
    db.yamukja.insert_one(doc)

    return  jsonify({'result': 'success', 'msg': '저장완료'})

# GET 요청 API: 모든 식당 읽기
@app.route("/restaurant", methods=["GET"])
def restaurant_get():
    # 데이터 모두 가져오기
    all_restaurants = list(db.yamukja.find({}, {'_id': False}))
    # 이미지 데이터 검색 및 인코딩
    for restaurant in all_restaurants:
        picture_id = restaurant['picture']  # ObjectId
        if picture_id:
            try:
                # ObjectId를 사용하여 이미지 데이터 검색
                image_data = fs.get(picture_id).read()
                # 이미지 데이터를 base64로 인코딩
                base64_img = base64.b64encode(image_data).decode('utf-8')
                # 'picture' 필드 업데이트

                restaurant['picture'] = base64_img
            except gridfs.errors.NoFile as e:
                # 이미지 데이터를 가져오지 못한 경우 예외처리
                print("요구하신 파일이 존재하지 않습니다")

    return jsonify({'result': all_restaurants})

# POST 요청 API: 식당 수정
@app.route('/update_restaurant', methods=['GET','POST'])
def restaurant_update():
    # 수정할 식당 페이지에서 가져오기
    if(request.method == "POST"):
        # 각 데이터의 고유의 값 가져오기 -> _id
        restaurantNum = request.form['restaurantNum_give']
        #restaurantNum = request.args.get('restaurantNum_give')
            
        # 사용자가 타입한 비밀번호
        target_password_receive= request.form['target_password_give']

        target = db.restaurant.find_one( { 'number': restaurantNum }) # 고유 id로 찾기
        # print(target['password'])
        if target['password'] != target_password_receive:
            return jsonify({'result' : 'fail', 'msg' : '비밀번호가 틀립니다'})    
        else:
            edited_nickname_receive = request.form['edited_nickname_give']
            edited_restaurantName_receive = request.form['edited_restaurantName_give']
            edited_address_receive = request.form['edited_address_give']
            edited_star_receive = request.form['edited_star_give']
            edited_review_receive = request.form['edited_review_give']

            doc = {
                    'nickname': edited_nickname_receive,
                    'name': edited_restaurantName_receive,
                    'address': edited_address_receive,
                    'star': edited_star_receive,
                    'review': edited_review_receive
                    }

            # DB에 수정
            db.restaurant.update_one(doc)

            return jsonify({'result' : 'success', 'msg' : '수정이 완료되었습니다'})

# @app.route("/restaurant", method=["DELETE"])
# def restaurant_delete():
#     db.yamukja.delete_one({'name':placeName},{'_id':False})

########################################################
#상세 페이지
@app.route('/detail')
def getDetail():
   global placeName # placeName을 global 변수로 선언
   placeName = request.args.get('placeName',"")
   return render_template('detail.html')

@app.route('/desc', methods=['GET'])
def desc_get():
    #상세페이지의 선택 식당 전체 내용 가져오기
   global placeName # 이미 선언되어있는 전역 변수를 사용
   desc_restaurant = db.yamukja.find_one({'name':placeName},{'_id':False})
   picture_id = desc_restaurant['picture']
   if picture_id:
        try:
            # ObjectId를 사용하여 이미지 데이터 검색
            image_data = fs.get(picture_id).read()
            # 이미지 데이터를 base64로 인코딩
            base64_img = base64.b64encode(image_data).decode('utf-8')
            # 'picture' 필드 업데이트
            #print(base64_img)
            desc_restaurant['picture'] = base64_img
        except gridfs.errors.NoFile as e:
            # 이미지 데이터를 가져오지 못한 경우 예외처리
            print("요구하신 파일이 존재하지 않습니다")

   return jsonify({'result':desc_restaurant})

@app.route('/desc_reply', methods=['GET'])
def reply_get():
    #상세페이지의 선택 식당 댓글 가져오기
   global placeName
   print("댓글가져오기:"+placeName)
   all_replies = list(db.restaurant_reply.find({'name':placeName},{'_id':False}))
   return jsonify({'result':all_replies})

@app.route('/save_reply', methods=['POST'])
def reply_post():
    #상세페이지 선택 식당 댓글 저장하기
   name_receive = request.form['name_give']
   reply_receive = request.form['reply_give']
   nickname_receive = request.form['nickname_give']
   password_receive = request.form['password_give']
   current_time = datetime.now()
   doc = {'name' : name_receive,
          'reply' : reply_receive,
          'nickname' : nickname_receive,
          'password' : password_receive,
          'datetime':current_time}
   db.restaurant_reply.insert_one(doc)
   return jsonify({'result':'success', 'msg': '댓글 저장이 완료되었습니다.'})

@app.route('/update_reply', methods=['GET','POST'])
def reply_update():
    #상세페이지 선택 식당 댓글 저장하기
    if request.method == "POST": #수정할 댓글을 페이지에서 가져오기
        targetname_receive = request.form['targetname_give']
        targetnickname_receive = request.form['targetnickname_give']
        targetpassword_receive = request.form['targetpassword_give']
        targetreply_receive = request.form['targetreply_give']

        target = db.restaurant_reply.find_one({'name':targetname_receive,
                                               'nickname':targetnickname_receive,
                                               'reply':targetreply_receive}) #댓글 테이블에 아이디와 댓글이 있는지 확인
        if target['password'] != targetpassword_receive: #입력한 비밀번호가 다를 때
            return jsonify({'result':'fail', 'msg': '비밀번호가 틀립니다.'})
        else: # 입력한 비밀번호가 맞을 때
            global before_reply
            before_reply = target
            return jsonify({'result':'success', 'msg': '수정할 내용을 작성하세요.'})

@app.route('/done_reply', methods=['POST'])
def reply_done():
    #상세페이지 선택 식당 댓글 수정 완료하기
    global before_reply
    afterreply_receive = request.form['afterreply_give']
    db.restaurant_reply.update_one(before_reply,{'$set':{'reply':afterreply_receive}})
    return jsonify({'result':'success', 'msg': '댓글 수정이 완료되었습니다.'})

@app.route('/delete_reply', methods=['POST'])
def reply_delete():
    #상세페이지 선택 식당 댓글 삭제하기
    targetname_receive = request.form['targetname_give']
    targetnickname_receive = request.form['targetnickname_give']
    targetpassword_receive = request.form['targetpassword_give']
    targetreply_receive = request.form['targetreply_give']
    print(targetname_receive)
    print(targetnickname_receive)
    print(targetpassword_receive)
    print(targetreply_receive)

    target = db.restaurant_reply.find_one({'name':targetname_receive,
                                           'nickname':targetnickname_receive,
                                           'reply':targetreply_receive}) #댓글 테이블에 아이디와 댓글이 있는지 확인
    if target['password'] != targetpassword_receive: #입력한 비밀번호가 다를 때
        return jsonify({'result':'fail', 'msg': '비밀번호가 틀립니다.'})
    else: # 입력한 비밀번호가 맞을 때
        db.restaurant_reply.delete_one(target)
        return jsonify({'result':'success', 'msg': '댓글이 삭제되었습니다.'})



if __name__ == '__main__':  
   app.run('0.0.0.0',port=5005,debug=True) # Port 문제시 포트번호 변경 (ex 5004)