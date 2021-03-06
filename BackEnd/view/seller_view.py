from flask          import jsonify, request, send_file
from flask.views    import MethodView

from connection     import get_connection
from pymysql        import err

from flask_request_validator import (
    GET,
    PATH,
    FORM,
    Param,
    Pattern,
    JSON,
    validate_params
)

from utils.validation import (
    Validation_seller_account,
    Validation_password,
    Validation_phone_number,
    Validation_korean_name,
    Validation_english_name,
    Validation_cs_phone,
    Validation_seller_property,
    Validation_order,
    Validation_managers_name,
    Validation_managers_email,
    Validation_bank_name,
    Validation_account_number,
    Validation_account_name,
    Validation_shipping_information,
    Validation_exchange_refund_information,
    Validation_model_height,
    Validation_model_top_size,
    Validation_model_bottom_size,
    Validation_model_feet_size,
    Validation_shopping_feedtext
)

from utils.decorator import (
    login_decorator,
    catch_exception
)

import config,connection
import traceback, os, datetime

class ProductSellerSearchView(MethodView):
    def __init__(self, service):
        self.service = service

    @login_decorator
    def get(self):
        """
        상품 등록을 위해 셀러를 검색한다.

        Args:

        Returns:
            200: 
                셀러 정보 딕셔너리 리스트를 JSON으로 리턴
            400: 
                CHECK_QUERY_PARAMS: 쿼리 스트링의 값이 올바르지 않음
            500:
                OperationalError: 데이터베이스 조작 에러
                InternalError   : 데이터베이스 내부 에러

        Author:
            이충희(choonghee.dev@gmail.com)

        History:
            2020-09-20(이충희): 초기 생성
        """
        try: 
            conn        = get_connection()
        
            search_term = request.args.get('q')
            limit       = request.args.get('limit', '10')
    
            if not search_term or not limit or not limit.isnumeric():
                message = {"message": "CHECK_QUERY_PARAMS"} 
                return jsonify(message), 400

            limit = int(limit)
            if limit > 10:
                limit = 10
            
            results     = self.service.search_sellers(conn, search_term, limit)
        except (err.OperationalError, err.InternalError) as e:
            message = {"errno": e.args[0], "errval": e.args[1]}
            return jsonify(message), 500
        else:
            return jsonify(results), 200
        finally:
            conn.close()

# 회원가입 endpoint
class SellerSignUpView(MethodView): 

    def __init__(self, service):
        self.service = service #(app->init->view)
    
    @catch_exception
    @validate_params(
        #들어온 파라미터들을 유효성 검사한다.
        Param('seller_account',JSON,str,required=True),
        Param('password',JSON,str,required=True),
        Param('phone_number',JSON,str,required=True),
        Param('korean_name',JSON,str,required=True),
        Param('english_name',JSON,str,required=True),
        Param('cs_phone',JSON,str,required=True),
        Param('seller_property',JSON,str,required=True)
    )
    def post(self, *args):
        """
        새로운 셀러를 생성합니다.

            Args:
                    seller_account     : 셀러 아이디 ,
                    english_name       : 영문 셀러명,
                    korean_name        : 셀러명,
                    cs_phone           : 고객센터 전화번호 ,
                    seller_property_id : 셀러 속성 PK(쇼핑몰 마켓  로드샵  디자이너브랜드  제너럴브랜드  내셔널브랜드  뷰티),
                    password           : 패스워드,
                    phone_number       : 담당자 전화번호,
                    seller_id          : 셀러 FK
            Retruns:
                200, {'message': 'SUCCESS'} : 회원가입 성공

                400, {'message': 'UNSUCCESS'} : 회원가입 실패, 유효성 검사 오류

                400, {"errno": e.args[0], "errval": e.args[1]} : DB와 관련된 오류

                (  
                    IntegrityError : 데이터베이스의 관계형 무결성에서 발생하는 예외 (외래키 검사 실패, 중복키, 기타)
                    DataError : 0으로 나누기, 범위를 벗어난 숫자 값,기타
                    NotSupportedError : 메서드 또는 데이터베이스 API를 사용한 경우 예외 발생 데이터베이스에서 지원하지 않는 경우( 트랜잭션을 지원하지 않는 연결의 .rollback () 또는 거래가 해제)
                    OperationalError : 데이터베이스와 관련된 오류에 대해 예외, 예기치 않은 연결 해제가 발생하면 데이터 소스 이름이 발견, 트랜잭션을 처리 할 수 ​​없음, 메모리 할당 처리 중 오류
                    InternalError : 데이터베이스가 내부 오류, 예를 들어 커서가 더 이상 유효하지 않습니다. 트랜잭션이 동기화되지 않음 등
                )

            Authors:
                wldus9503@gmail.com(이지연)
            
            History:
                2020.09.22(이지연) : 초기 생성
                2020.09.23(이지연) : 수정
                                -> view에서 db commit하도록 변경, 에러 처리 추가
                2020.09.25(이지연)  : validation(유효성) 검사 추가
                2020.09.28(이지연)  : validation(유효성) 검사 삭제 -> ui쪽에서 처리하기로
                2020.10.02(이지연)  : 모델링 변경 -> 하나의 셀러 테이블을 sellers와 seller_informations으로 나누고 로직 변경
                2020.10.07(이지연)  : 회원가입할 시 셀러 계정아이디, 셀러 cs_phone, manager_phone unique처리 추가
                2020-10.08(이지연)  : 피드백 반영 팀원들과 형식 맞춰 수정

        """
        try:
            conn          = connection.get_connection()   
            seller_info   = {
                'seller_account'    :   args[0],
                'password'          :   args[1],
                'phone_number'      :   args[2],
                'korean_name'       :   args[3],
                'english_name'      :   args[4],
                'cs_phone'          :   args[5],
                'seller_property'   :   args[6]
            }
            sign_up       = self.service.sign_up(seller_info, conn)
        #DB와 관련된 오류
        except (err.IntegrityError,err.DataError, err.NotSupportedError, err.OperationalError,err.InternalError) as e:
            traceback.print_exc
            conn.rollback()
            message = {"errno": e.args[0], "errval": e.args[1]}
            return jsonify(message), 400
        #그 외 모든 에러들
        except Exception as e:
            traceback.print_exc()
            conn.rollback()
            return jsonify({'message': 'UNSUCCESS'}), 400
        else:
            conn.commit()    
            return jsonify({'message':'SUCCESS'}), 200 
        finally:
            conn.close()  
            
# 로그인 endpoint
class SellerSignInView(MethodView):

    def __init__(self, service):
        self.service = service 

    @catch_exception
    @validate_params(
        Param('seller_account',JSON,str,required=True),
        Param('password',JSON,str,required=True)
    )
    def post(self, *args):
        """
        기본 로그인 API

        Args:
            seller_info{
                seller_account : 셀러 아이디
                password       : 패스워드
            }

        Retruns:
            200, {'access_token':access_token}

            400, {'message': 'UNSUCCESS'}

            400, {"errno": e.args[0], "errval": e.args[1]} : DB와 관련된 오류

            (   
                #IntegrityError : 데이터베이스의 관계형 무결성에서 발생하는 예외 (외래키 검사 실패, 중복키, 기타)
                #DataError : 0으로 나누기, 범위를 벗어난 숫자 값,기타
                #NotSupportedError : 메서드 또는 데이터베이스 API를 사용한 경우 예외 발생 데이터베이스에서 지원하지 않는 경우( 트랜잭션을 지원하지 않는 연결의 .rollback () 또는 거래가 해제)
                #OperationalError : 데이터베이스와 관련된 오류에 대해 예외, 예기치 않은 연결 해제가 발생하면 데이터 소스 이름이 발견, 트랜잭션을 처리 할 수 ​​없음, 메모리 할당 처리 중 오류
                #InternalError : 데이터베이스가 내부 오류, 예를 들어 커서가 더 이상 유효하지 않습니다. 트랜잭션이 동기화되지 않음 등
            )

        Authors:
            wldus9503@gmail.com(이지연)
        
        History:(
            2020.09.23(이지연) : 초기 생성
            2020.09.24(이지연) : 수정
                                -> view에서 db commit하도록 변경, 에러 처리 추가
            2020.09.25(이지연)  : 유효성 검사 추가
            2020.09.28(이지연)  : 유효성 검사 customexception -> validationexception 변경
            2020.10.02(이지연)  : 모델링 변경 -> 하나의 셀러 테이블을 sellers와 seller_informations으로 나누고 로직 변경
            2020.10.08(이지연)  : 피드백 반영 팀원들과 형식 맞춰 수정
    """ 
       
        try:
            conn          = connection.get_connection()
            seller_info   = {
                'seller_account'    :   args[0],
                'password'          :   args[1]
            }
            
            # 로그인 성공 시 access_token 생성 메소드 실행 -> 성공 x : INVALID_USER, INVALID_TOKEN
            access_token  = self.service.sign_in(seller_info,conn)

        #DB 오류
        except (err.IntegrityError,err.DataError, err.NotSupportedError, err.OperationalError,err.InternalError) as e:
            traceback.print_exc()
            message = {"errno": e.args[0], "errval": e.args[1]}
            # (1054, "Unknown column 'seller_accounts' in 'field list'")
            return jsonify(message), 400
        #그 외 오류(컬럼명 오타 등)
        except Exception as e:
            traceback.print_exc()
            return jsonify({'message': 'UNSUCCESS'}),400
        else:
            return jsonify({'access_token':access_token}),200
        finally:
            conn.close() 

# 검색 기능 endpoint
class  SellerSearchView(MethodView):
    def __init__(self, service):
        self.service = service

    @login_decorator
    @catch_exception
    @validate_params(
        Param('id', GET, str, required=False, default=None),
        Param('seller_account', GET, str, required=False, default=None),
        Param('korean_name', GET, str, required=False, default=None),
        Param('english_name', GET, str, required=False, default=None),
        Param('seller_status', GET, str, required=False, default=None),
        Param('seller_property',GET, str, required=False, default=None),
        Param('manager_name', GET, str, required=False, default=None),
        Param('manager_phone', GET, str, required=False, default=None),
        Param('manager_email', GET, str, required=False,default=None),
        Param('start_date', GET, str, required=False, default=None),
        Param('end_date',GET, str, required=False, default=None),
        Param('page',GET, int, required=False, default=1), #현재 페이지
        Param('per_page',GET, int, required=False, default=10),
        Param('order',GET, str, required=False, default='DESC',rules=[Validation_order()]) # DAO에서 sql 정렬방식 
    )
    #프론트에서 페이지 번호, 페이지 당 개수
    def get(self, *args):
        """
        셀러 계정 관리 검색 API

        Args:
            search_info :   검색 데이터를 담을 리스트

        Retruns:
            200, results : 해당 검색에 대한 결과
            400, {'message': 'UNSUCCESS'} : 검색실패시

        Authors:
            wldus9503@gmail.com(이지연)
        
        History:(
            2020.09.27(이지연) : 셀러 리스트 초기 생성   
            2002.09.28(이지연) : 수정
                             ->  유효성 검사 함수를 DAO로 이동
            2020.09.29(이지연) : 셀러 검색 추가, 페이지 네이션 추가 
            2020.10.02(이지연) : 모델링 변경으로 인한 수정
                             -> 하나의 셀러 테이블을 sellers와 seller_informations으로 나누고 로직 변경
            2020.10.08(이지연)  : 피드백 반영 팀원들과 형식 맞춰 수정

        """

        try:
            conn = connection.get_connection()
            search_info = {
                'id'                        :   args[0],
                'seller_account'            :   args[1],
                'korean_name'               :   args[2],
                'english_name'              :   args[3],
                'seller_status'             :   args[4],
                'seller_property'           :   args[5],
                'manager_name'              :   args[6],
                'manager_phone'             :   args[7],
                'manager_email'             :   args[8],
                'start_date'                :   args[9],
                'end_date'                  :   args[10],
                'page'                      :   args[11],
                'per_page'                  :   args[12],
                'order'                     :   args[13]
            }

            results = self.service.search_seller_list(conn, search_info)
        except:
            traceback.print_exc()
            return jsonify({'message': 'UNSUCCESS'}), 400
        else:
            return jsonify(results), 200
        finally:
            conn.close()

# 셀러 수정 기능
class SellerUpdateView(MethodView):

    def __init__(self, service):
        self.service = service
    
    @login_decorator
    @catch_exception
    @validate_params(
        Param('seller_id', PATH, int, required=True, default=None),
        Param('seller_status', FORM , str, required=True, default=None),
        Param('seller_property', FORM, str, required=True, default=None),
        Param('seller_account', FORM, str, required=True, default=None),
        Param('simple_description', FORM, str, required=False, default=None),
        Param('detail_description', FORM, str, required=False, default=None),
        Param('cs_phone', FORM, str, required=True, default=None),
        Param('zip_code', FORM, str, required=False, default=None),
        Param('address', FORM, str, required=False, default=None),
        Param('detail_address', FORM, str, required=False, default=None),
        Param('open_time', FORM, str, required=False, default=None),
        Param('close_time', FORM, str, required=False, default=None),
        Param('bank', FORM, str, required=False, default=None),
        Param('account_number', FORM, str, required=False, default=None),
        Param('account_name', FORM, str, required=False, default=None),
        Param('shipping_information', FORM, str, required=False, default=None),
        Param('exchange_refund_information', FORM, str, required=False, default=None),
        Param('model_height', FORM, str, required=False, default=None),
        Param('model_top_size', FORM, str, required=False, default=None),
        Param('model_bottom_size', FORM, str, required=False, default=None),
        Param('model_feet_size', FORM, str, required=False, default=None),
        Param('shopping_feedtext', FORM, str, required=False, default=None),
        Param('password', FORM, str, required=False, default=None),
        Param('korean_name', FORM, str, required=False, default=None),
        Param('english_name', FORM, str, required=False, default=None),
        Param('manager_info[0]', FORM, dict, required=True, default=None),
        Param('manager_info[1]', FORM, dict, required=False, default=None),
        Param('manager_info[2]', FORM, dict, required=False, default=None)
    )
    #Form으로 한 이유: 이미지 파일과 json데이터를 한꺼번에 요청하기 위해서
    
    #셀러 정보 수정
    def put(self,*args):

        """
        셀러 정보 수정페이지 API

        Args:
            update_info   = :  수정 정보를 담을 리스트 

        Retruns:
            200, results : 해당 검색에 대한 결과
            400, {'message': 'UNSUCCESS'} : 셀러 정보 수정 실패

        Authors:
            wldus9503@gmail.com(이지연)
        
        History:(
            2020.10.02(이지연) : 모델링 변경으로 인한 수정
                             -> 하나의 셀러 테이블을 sellers와 seller_informations으로 나누고 로직 변경
            2020.10.04(이지연) : 데코레이터를 적용
            2020.10.08(이지연) : 피드백 반영 팀원들과 형식 맞춰 수정
            
        """

        try:
            conn = connection.get_connection()

            update_info   = {
                'seller_id'                   : args[0],
                'seller_status'               : args[1],
                'seller_property'             : args[2],
                'seller_account'              : args[3],
                'simple_description'          : args[4],
                'detail_description'          : args[5],
                'cs_phone'                    : args[6],
                'zip_code'                    : args[7],
                'address'                     : args[8],
                'detail_address'              : args[9],
                'open_time'                   : args[10],
                'close_time'                  : args[11],
                'bank'                        : args[12],
                'account_number'              : args[13],
                'account_name'                : args[14],
                'shipping_information'        : args[15],
                'exchange_refund_information' : args[16],
                'model_height'                : args[17],
                'model_top_size'              : args[18],
                'model_bottom_size'           : args[19],
                'model_feet_size'             : args[20],
                'shopping_feedtext'           : args[21],
                'password'                    : args[22],
                'korean_name'                 : args[23],
                'english_name'                : args[24],
                'manager_infos'               : None
            }

            #매니저정보 1개 이상 최대 3개를 받음.
            manager_infos = []

            #None이 아닌 매니저 정보는 리스트에 담는다(args-23,24,25까지)
            for i in range(25,28):
                if args[i] != None:
                    manager_infos.append(args[i])
            #update_info에 리스트를 담는다.
            update_info['manager_infos'] = manager_infos

            #데코레이터로 부터 저장한 요청자의 id값 = 수정자의 id
            modifier_user = request.user
            #print(modifier_user)
            #프로필 이미지 및 배경화면 이미지 값 받아오기
            profile_image = request.files.get('profile_image', None)
            background_image = request.files.get('background_image', None)
            
            results = self.service.update_seller(conn, update_info,profile_image,background_image,modifier_user)
        except Exception as e:
            traceback.print_exc()
            conn.rollback()
            return jsonify({'message': 'UNSUCCESS'}),400
        else:
            conn.commit()
            return jsonify(results), 200
        finally:
            conn.close()

    @catch_exception
    @validate_params(
        Param('seller_id', PATH, str, required=True, default=None)
    )
    #셀러 상세정보 조회
    def get(self,*args):

        """
        셀러 상세 정보 조회 페이지 
            - 이전에 입력된 데이터를 보여준다.

        Args:
            seller_id : 셀러 고유 아이디
        Retruns:
            200, results : 해당 검색에 대한 결과
            400, {'message': 'UNSUCCESS'} : 셀러 정보 수정 실패

        Authors:
            wldus9503@gmail.com(이지연)
        
        History:(
            2020.10.04(이지연) : 초기 생성
            2020-10.08(이지연) : 피드백 반영 팀원들과 형식 맞춰 수정
            2020.10.09(이지연) : 모델링 param을 적용해 sql로직 수정

        """

        try: 
            #db연결
            conn            = get_connection()
            #seller_id를 인자로 갖고온다.
            seller_id       = args[0]
            #service에서 넘겨준 값을 results변수에 담는다.
            results          = self.service.detail_seller(conn, seller_id)
        
        #예외처리
        except Exception as e:
            traceback.print_exc()
            return jsonify({'message':'UNSUCCESS'}), 400
        else:
            return jsonify(results), 200
        finally:
            conn.close()

# 엑셀 다운로드 파일 엔드포인트
class SellerExcelDownloadView(MethodView):
    def __init__(self, service):
        self.service = service

    # @login_decorator
    @catch_exception
    @validate_params(
        Param('id', GET, str, required=False, default=None),
        Param('seller_account', GET, str, required=False, default=None),
        Param('korean_name', GET, str, required=False, default=None),
        Param('english_name', GET, str, required=False, default=None),
        Param('seller_status', GET, str, required=False, default=None),
        Param('seller_property',GET, str, required=False, default=None),
        Param('manager_name', GET, str, required=False, default=None),
        Param('manager_phone', GET, str, required=False, default=None),
        Param('manager_email', GET, str, required=False,default=None),
        Param('start_date', GET, str, required=False, default=None),
        Param('end_date',GET, str, required=False, default=None),
        Param('order',GET, str, required=False, default='DESC',rules=[Validation_order()])
    )
    def get(self, *args):
        
        """
        엑셀 다운로드 파일 엔드포인트

        Args: 
            search_info : 검색 결과 정보를 담을 리스트

        Retruns:
            400, {'message': 'UNSUCCESS'} 

        Authors:
            wldus9503@gmail.com(이지연)
        
        History:(
            2020.10.09(이지연) : 초기 설정
            2020.10.11(이지연) : user_id 중복 발생으로 인한 에러 수정
        """
        try:
            conn = connection.get_connection()

            #데이터를 dict형으로 받아준다.
            search_info = {
                'id'                        :   args[0],
                'seller_account'            :   args[1],
                'korean_name'               :   args[2],
                'english_name'              :   args[3],
                'seller_status'             :   args[4],
                'seller_property'           :   args[5],
                'manager_name'              :   args[6],
                'manager_phone'             :   args[7],
                'manager_email'             :   args[8],
                'start_date'                :   args[9],
                'end_date'                  :   args[10],
                'order'                     :   args[11]
            }

            directory, filename, filename_for_user = self.service.make_excel_file(conn, search_info)
        except:
            traceback.print_exc()
            return jsonify({'message': 'UNSUCCESS'}), 400
        else:
            now_date = datetime.datetime.now().strftime("%Y%m%d")
            #오늘 날짜 + '_' + "유저 다운로드 파일명"
            filename_for_user = now_date + "_" + filename_for_user
            #flask의 send_file 기능 -> 서버에 저장되어있는 엑셀파일을 응답에 담아서 보냄
            send_to_file = send_file(directory + filename,
                mimetype="application/vnd.ms-excel",
                as_attachment=True,
                attachment_filename=filename_for_user,
                conditional=False)
            os.remove(os.path.join('temp/', filename))
            return send_to_file
        finally:
            conn.close()
