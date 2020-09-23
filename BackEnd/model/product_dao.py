import pymysql
from flask import jsonify
from connection import get_connection

class DAOInsertFailError(Exception):
    def __init__(self, message):
        super().__init__(message)


# 작성자: 김태수
# 수정일: 2020.09.21.월
# Product와 연결된 Class
class ProductDao:

    # 작성자: 김태수
    # 작성일: 2020.09.21.월
    # 원산지 데이터를 데이터베이스에서 가져오는 함수
    def get_country_of_origin(self, country_id):
        try:
            db     = get_connection(self.db)
            cursor = db.cursor(pymysql.cursors.DictCursor)

            sql = """
            SELECT id, name
            FROM tests
            WHERE id = %s;
            """

            cursor.execute(sql, country_id)
            result = cursor.fetchone()
        except:
            db.rollback()
            raise
        else:
            db.commit()
            return result if result else None
        finally:
            cursor.close()
            db.close()

    def find_first_categories_by_seller_property_id(self, conn, seller_property_id):
        QUERY = """
            SELECT
	            t2.id, t2.name 
            FROM 
	            first_category_seller_properties AS t1 
            LEFT JOIN 
	            first_categories AS t2 
            ON       
	            t1.first_category_id = t2.id 
            WHERE 
	            seller_property_id = %s;
            """

        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute(QUERY, (seller_property_id,))
        results = cursor.fetchall()

        cursor.close()

        return results if results else None

    def find_second_categories_by_first_category_id(self, conn, first_category_id):
        QUERY = """
            SELECT
                t2.id, t2.name 
            FROM 
                first_category_second_categories AS t1 
            LEFT JOIN 
                second_categories AS t2 
            ON 
                t1.second_category_id = t2.id 
            WHERE 
                first_category_id = %s;
            """

        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute(QUERY, (first_category_id,))
        results = cursor.fetchall()

        cursor.close()

        return results if results else None

    # def create_product(self, product_dict):
    #     QUERY = """
    #         INSERT INTO products (
    #             seller_id,
    #             code
    #         ) VALUES (
    #             %(seller_id)s,
    #             %(code)s
    #         );
    #     """

    #     try:
    #         db     = get_connection(self.db)
    #         cursor = db.cursor()
    #         result = cursor.execute(QUERY, product_dict)
    #         if result <= 0:
    #             raise DAOInsertFailError("COULD_NOT_CREATE_PRODUCT")

    #     except (pymysql.IntegrityError, DAOInsertFailError) as e:
    #         db.rollback()
    #         raise e
    #     else:
    #         db.commit()
    #         product_id = cursor.lastrowid
    #     finally:
    #         cursor.close()
    #         db.close()

    #     return product_id