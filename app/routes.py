from flask import current_app as app, jsonify, request, Flask
from app.function import generateJWT, decodeJWT
from flask_sqlalchemy import SQLAlchemy
from app.models import WalletUser
import psycopg2
from datetime import datetime
from app.db import get_conn, put_conn

@app.route('/api/v1/init', methods=['POST'])
def initialize_wallet():
    if request.form:
        form_data = request.form
        customer_xid = form_data.get('customer_xid')
        
        customer_token = generateJWT(customer_xid)
        conn = get_conn()
        try:
            cur = conn.cursor()
            cur.execute('INSERT INTO wallet_user (customer_xid, token) VALUES (%s, %s)', (customer_xid, customer_token))
            cur.execute("INSERT INTO wallet_user_info (owned_by, status, balance) VALUES (%s, %s, %s)", (customer_xid, "disabled", 0))
            conn.commit()
            cur.close()

            data = {
                "token":customer_token
            }

            return jsonify(status='success', data=data)
        except Exception as e:
            conn.rollback()
            return jsonify(error=str(e))
        finally:
            put_conn(conn)

    else:
        return jsonify(error='No form data provided in the request')

@app.route('/api/v1/wallet', methods=['POST', 'GET', 'PATCH'])
def set_wallet_status():
    auth_token = request.headers.get('Authorization')
    token  = auth_token.split()[1]
    response_token = decodeJWT(token)
    customer_xid = response_token["customer_xid"]
    conn = get_conn()
    if request.method == 'GET':
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM wallet_user_info WHERE owned_by = '" + customer_xid + "'"
            )
            customer_data = cur.fetchone()
            enabled_at = str(customer_data[3])
            dt = datetime.fromisoformat(enabled_at)
            enabled_at_iso_format = dt.isoformat()
            cur.close()
            wallet_status = customer_data[2]
            if wallet_status == "enabled":
                return jsonify(
                    status="success",
                    data={
                        "wallet": {
                        "id": customer_data[0],
                        "owned_by": customer_xid,
                        "status": wallet_status,
                        "enabled_at": enabled_at_iso_format,
                        "balance": customer_data[4]
                        }
                    }
                )
            elif wallet_status == "disabled":
                return jsonify(
                    status="fail",
                    data={
                        "error": "wallet disabled"
                    }
                )
        except Exception as e:
            conn.rollback()
            return jsonify(error=str(e))
        finally:
            put_conn(conn)    
    elif request.method == 'POST':
        try:
            cur = conn.cursor()
            cur.execute("UPDATE wallet_user_info SET status = 'enabled' WHERE owned_by = '" + customer_xid + "'")
            conn.commit()
            cur.execute(
                "SELECT * FROM wallet_user_info WHERE owned_by = '" + customer_xid + "'"
            )
            customer_data = cur.fetchone()
            enabled_at = str(customer_data[3])
            dt = datetime.fromisoformat(enabled_at)
            enabled_at_iso_format = dt.isoformat()
            cur.close()

            return jsonify(
                status="success",
                data={
                    "wallet": {
                    "id": customer_data[0],
                    "owned_by": customer_xid,
                    "status": customer_data[2],
                    "enabled_at": enabled_at_iso_format,
                    "balance": customer_data[4]
                    }
                }
            )
        except Exception as e:
            conn.rollback()
            return jsonify(error=str(e))
        finally:
            put_conn(conn) 
    elif request.method == 'PATCH':
        if request.form:
            form_data = request.form
            is_disabled = form_data.get('is_disabled').lower()
            try:
                cur = conn.cursor()
                if is_disabled == "true":
                    cur.execute("UPDATE wallet_user_info SET status = 'disabled' WHERE owned_by = '" + customer_xid + "'")
                    conn.commit()
                
                cur.execute(
                    "SELECT * FROM wallet_user_info WHERE owned_by = '" + customer_xid + "'"
                )
                customer_data = cur.fetchone()
                disabled_at = str(customer_data[3])
                dt = datetime.fromisoformat(disabled_at)
                disabled_at_iso_format = dt.isoformat()
                cur.close()

                return jsonify(
                    status="success",
                    data={
                        "wallet": {
                        "id": customer_data[0],
                        "owned_by": customer_xid,
                        "status": customer_data[2],
                        "disabled_at": disabled_at_iso_format,
                        "balance": customer_data[4]
                        }
                    }
                )
            except Exception as e:
                conn.rollback()
                return jsonify(error=str(e))
            finally:
                put_conn(conn) 


@app.route('/api/v1/wallet/deposits', methods=['POST'])
def add_virtual_money():
    auth_token = request.headers.get('Authorization')
    token  = auth_token.split()[1]
    response_token = decodeJWT(token)
    customer_xid = response_token["customer_xid"]
    if request.form:
        conn = get_conn()
        try:
            form_data = request.form
            money_amount = int(form_data.get('amount'))
            reference_id = form_data.get('reference_id')
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM wallet_user_transactions WHERE reference_id = '" + reference_id + "'"
            )
            customer_data = cur.fetchone()
            if customer_data:
                return jsonify(
                    status="fail",
                    data={
                        "error": "duplicate reference id"
                    }
                )
            else:
                cur.execute(f"""INSERT INTO wallet_user_transactions (reference_id, owned_by, status, amount, 
                            transaction_type) VALUES (%s, %s, %s, %s, %s)""", (reference_id, customer_xid, "success", money_amount, "deposit"))
                cur.execute(
                    f"""UPDATE wallet_user_info SET balance = balance + {money_amount} WHERE owned_by ='{customer_xid}'""",
                )
                conn.commit()
                cur.execute(
                    "SELECT * FROM wallet_user_transactions WHERE transaction_type = 'deposit' AND reference_id = '" + reference_id + "'  AND owned_by = '"+ customer_xid +"'"
                )
                transaction_data = cur.fetchone()
                transaction_at = str(transaction_data[4])
                dt = datetime.fromisoformat(transaction_at)
                transaction_at_iso_format = dt.isoformat()
                cur.close()

                return jsonify(              
                    status="success",
                    data={
                        "deposit": {
                            "id": transaction_data[0],
                            "deposited_by": customer_xid,
                            "status": "success",
                            "deposited_at": transaction_at_iso_format,
                            "amount": money_amount,
                            "reference_id": reference_id
                        }
                    }
                    
                )
        except Exception as e:
            conn.rollback()
            return jsonify(error=str(e))
        finally:
            put_conn(conn) 
        

@app.route('/api/v1/wallet/withdrawals', methods=['POST'])
def withdraw_virtual_money():
    auth_token = request.headers.get('Authorization')
    token  = auth_token.split()[1]
    response_token = decodeJWT(token)
    customer_xid = response_token["customer_xid"]
    if request.form:
        conn = get_conn()
        try:
            form_data = request.form
            money_amount = int(form_data.get('amount'))
            reference_id = form_data.get('reference_id')
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM wallet_user_transactions WHERE reference_id = '" + reference_id + "'"
            )
            customer_data = cur.fetchone()
            if customer_data:
                return jsonify(
                    status="fail",
                    data={
                        "error": "duplicate reference id"
                    }
                )
            else:
                cur.execute(f"""INSERT INTO wallet_user_transactions (reference_id, owned_by, status, amount, 
                            transaction_type) VALUES (%s, %s, %s, %s, %s)""", (reference_id, customer_xid, "success", money_amount, "withdrawal"))
                cur.execute(
                    f"""UPDATE wallet_user_info SET balance = balance - {money_amount} WHERE owned_by ='{customer_xid}'""",
                )
                conn.commit()
                cur.execute(
                    "SELECT * FROM wallet_user_transactions WHERE transaction_type = 'withdrawal' AND reference_id = '" + reference_id + "'  AND owned_by = '"+ customer_xid +"'"
                )
                transaction_data = cur.fetchone()
                transaction_at = str(transaction_data[4])
                dt = datetime.fromisoformat(transaction_at)
                transaction_at_iso_format = dt.isoformat()
                cur.close()

                return jsonify(              
                    status="success",
                    data={
                        "withdrawal": {
                            "id": transaction_data[0],
                            "withdrawn_by": customer_xid,
                            "status": "success",
                            "withdrawn_at": transaction_at_iso_format,
                            "amount": money_amount,
                            "reference_id": reference_id
                        }
                    }
                    
                )
        except Exception as e:
            conn.rollback()
            return jsonify(error=str(e))
        finally:
            put_conn(conn) 
       
@app.route('/api/v1/wallet/transactions', methods=['GET'])
def view_transactions():
    auth_token = request.headers.get('Authorization')
    token  = auth_token.split()[1]
    response_token = decodeJWT(token)
    customer_xid = response_token["customer_xid"]
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM wallet_user_transactions WHERE owned_by = '" + customer_xid + "' ORDER BY transaction_at DESC"
        )
        transaction_data = cur.fetchall()
        result = []
        for items in transaction_data:
            transaction_at = str(items[4])
            dt = datetime.fromisoformat(transaction_at)
            transaction_at_iso_format = dt.isoformat()
            transaction_info = {
                "transaction_date": transaction_at_iso_format,
                "amount": items[5],
                "transaction_type": items[6],
                "reference_id": items[1],
                "status": items[2],
                "transaction_by":customer_xid
            }
            result.append(transaction_info)

        return jsonify(
                status="success",
                data=result
            )
    except Exception as e:
        conn.rollback()
        return jsonify(error=str(e))
    finally:
        put_conn(conn)



if __name__ == '__main__':
    app.run(debug=True)
