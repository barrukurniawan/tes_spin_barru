from flask import Flask, request
from pymongo import MongoClient
from bson import json_util
from bson.objectid import ObjectId
import requests
import pytz
import json
import uuid
import time
import datetime
import hashlib
import random

app = Flask(__name__)

client = MongoClient("mongodb+srv://barrukurniawan:SMAN60jakarta@cluster0.zvbeg.mongodb.net/provetic?retryWrites=true&w=majority")
db = client.get_database('db_spin_test')
user_records = db.table_users
auth_records = db.table_auth
balance_records = db.table_balance
payment_records = db.table_payments
topup_records = db.table_topup
transfer_records = db.table_transfer

def secret_key(key, unique_key):
    key_value = '{}{}'.format(str(key), str(unique_key))
    secret_key = hashlib.sha256(key_value.encode()).hexdigest()
    return secret_key

def auth_token(user_id):
    timenow = int(time.time() * 1000)

    auth_expire_in = datetime.datetime.now(pytz.timezone('Asia/Jakarta')) + datetime.timedelta(hours=2)
    refresh_expire_in = datetime.datetime.now(pytz.timezone('Asia/Jakarta')) + datetime.timedelta(days=3)
    auth_expire = int(auth_expire_in.timestamp() * 1000)
    refresh_expire = int(refresh_expire_in.timestamp() * 1000)

    auth = auth_records.insert({
        "user_id": user_id,
        "auth_token": secret_key(key=user_id, unique_key=str(random.randint(1000,9999))),
        "refresh_token": secret_key(key=user_id, unique_key=str(random.randint(1000,9999))),
        "expire_auth": auth_expire,
        "expire_refresh": refresh_expire,
        "created_date": timenow
    })

    check_token  = auth_records.find_one({
        "_id" : ObjectId(auth)
    })

    response_data = dict(
        access_token=check_token.get('auth_token'),
        refresh_token=check_token.get('refresh_token'),
    )

    response = dict(
        message="SUCCESS",
        result=response_data
    )

    return response

def validate_token(auth_token):
    timenow = int(time.time() * 1000)
    response_data = ""
    response = ""

    check_token  = auth_records.find_one({
        "auth_token" : auth_token
    })

    if check_token is not None:
        if timenow > check_token.get('expire_auth'):
            response = dict(
                message="Unauthenticated"
            )
            return response
        elif timenow < check_token.get('expire_auth'):
            response_data = dict(
                user_id=check_token.get('user_id'),
                access_token=check_token.get('auth_token'),
                refresh_token=check_token.get('refresh_token'),
            )

            response = dict(
                message="SUCCESS",
                result=response_data
            )
            return response
    else:
        response = dict(
            message="Unauthenticated"
        )
        return response

@app.route('/register', methods=['POST'])
def register():
    params = request.json
    response_data = dict()
    timenow = int(time.time() * 1000)

    check_user  = user_records.find({
        "phone_number" : params.get('phone_number')
    }).count()
    
    if check_user > 0 :
        response = dict(
            message="Phone number already existed"
        )
        return response
    
    hash_pin = secret_key(key=str(params.get('pin')), unique_key='BARRUTAMPAN')

    hash_id = str(uuid.uuid4().hex)
    balance_id = str(uuid.uuid4().hex) + "blnce"

    register_user  = user_records.insert({
        "user_id": hash_id,
        "first_name": params.get('first_name'),
        "last_name": params.get('last_name'),
        "phone_number": params.get('phone_number'),
        "address": params.get('address'),
        "pin": hash_pin,
        "rec_timestamp": timenow
    })

    balance_user  = balance_records.insert({
        "balance_id": balance_id,
        "user_id": hash_id,
        "amount": 0,
        "rec_timestamp": timenow
    })

    check_register_user  = user_records.find_one({
        "_id" : ObjectId(register_user)
    })

    if check_register_user is not None:
        response_data = dict(
            user_id=check_register_user.get('user_id'),
            first_name=check_register_user.get('first_name'),
            last_name=check_register_user.get('last_name'),
            phone_number=check_register_user.get('phone_number'),
            address=check_register_user.get('address'),
            pin=check_register_user.get('pin'),
            created_date=datetime.datetime.fromtimestamp(check_register_user.get('rec_timestamp')/1000).strftime('%Y-%m-%d %H:%M:%S')
        )

    response = dict(
        message="SUCCESS",
        result=response_data
    )

    return response

@app.route('/login', methods=['POST'])
def login():
    params = request.json
    response_data = dict()

    hash_pin = secret_key(key=str(params.get('pin')), unique_key='BARRUTAMPAN')

    check_login_user  = user_records.find_one({
        "phone_number" : params.get('phone_number'),
        "pin" : hash_pin
    })

    if check_login_user is None :
        response = dict(
            message="Phone number and pin doesn’t match."
        )
        return response

    if check_login_user is not None:
        response = auth_token(check_login_user.get('user_id'))

    return response

@app.route('/update-profile', methods=['PUT'])
def update_profile():
    response_data = dict()
    params = request.json
    headers = request.headers

    bearer_token = headers.get('Authorization')
    bearer_token = bearer_token.strip().split(' ')
    validation = validate_token(bearer_token[1])

    if validation is not None:
        if validation.get('result') is None:
            return validation

    check_login_user  = user_records.find_one({
        "user_id" : validation["result"]["user_id"]
    })

    if check_login_user is None :
        response = dict(
            message="User's not found"
        )
        return response

    if check_login_user is not None:
        update_profile  = user_records.update(
                {'user_id': validation["result"]["user_id"]},
                {'$set': {
                    "first_name": params.get('first_name'),
                    "last_name": params.get('last_name'),
                    "phone_number": params.get('phone_number'),
                    "address": params.get('address')
                }}
        )

        check_profile_updated  = user_records.find_one({
            "user_id" : validation["result"]["user_id"]
        })
        
        response_data = dict(
            user_id=check_profile_updated.get('user_id'),
            first_name=check_profile_updated.get('first_name'),
            last_name=check_profile_updated.get('last_name'),
            address=check_profile_updated.get('address'),
            phone_number=check_profile_updated.get('phone_number'),
            updated_date=datetime.datetime.fromtimestamp(check_profile_updated.get('rec_timestamp')/1000).strftime('%Y-%m-%d %H:%M:%S')
        )

    response = dict(
        message="SUCCESS",
        result=response_data
    )

    return response

@app.route('/topup', methods=['POST'])
def topup():
    params = request.json
    response_data = dict()
    balance_user = ""
    top_up_user = ""
    amount_now = 0
    amount_before = 0
    amount_after = 0
    timenow = int(time.time() * 1000)
    headers = request.headers

    bearer_token = headers.get('Authorization')
    bearer_token = bearer_token.strip().split(' ')
    validation = validate_token(bearer_token[1])

    if validation is not None:
        if validation.get('result') is None:
            return validation

    check_balance  = balance_records.find_one({
        "user_id" : validation["result"]["user_id"]
    })

    if check_balance is None:
        top_up_user  = topup_records.insert({
            "top_up_id": str(uuid.uuid4().hex),
            "user_id": validation["result"]["user_id"],
            "amount": int(params.get('amount')),
            "amount_before": 0,
            "amount_after": 0,
            "rec_timestamp": timenow
        })

        balance_user  = balance_records.insert({
            "balance_id": str(uuid.uuid4().hex) + "blnce",
            "user_id": validation["result"]["user_id"],
            "amount": int(params.get('amount')),
            "rec_timestamp": timenow
        })
    else:
        amount_now = int(check_balance.get('amount'))
        amount_before = amount_now
        amount_after = amount_now + int(params.get('amount'))

        update_topup  = balance_records.update(
                    {'user_id': check_balance.get('user_id')},
                    {'$set': {
                        "amount": amount_after
                    }}
        )

        top_up_user  = topup_records.insert({
            "top_up_id": str(uuid.uuid4().hex),
            "user_id": validation["result"]["user_id"],
            "amount": int(params.get('amount')),
            "balance_before": amount_before,
            "balance_after": amount_after,
            "rec_timestamp": timenow
        })

    check_top_up_user  = topup_records.find_one({
        "_id" : ObjectId(top_up_user)
    })

    if check_top_up_user is not None:
        response_data = dict(
            user_id=check_top_up_user.get('user_id'),
            amount_top_up=int(params.get('amount')),
            balance_before=int(check_balance.get('amount')),
            balance_after=int(check_balance.get('amount')) + int(params.get('amount')),
            created_date=datetime.datetime.fromtimestamp(check_top_up_user.get('rec_timestamp')/1000).strftime('%Y-%m-%d %H:%M:%S')
        )

    response = dict(
        message="SUCCESS",
        result=response_data
    )

    return response

@app.route('/pay', methods=['POST'])
def payment():
    params = request.json
    response_data = dict()
    balance_user = ""
    payment_user = ""
    amount_now = 0
    amount_before = 0
    amount_after = 0
    timenow = int(time.time() * 1000)
    headers = request.headers

    bearer_token = headers.get('Authorization')
    bearer_token = bearer_token.strip().split(' ')
    validation = validate_token(bearer_token[1])

    if validation is not None:
        if validation.get('result') is None:
            return validation

    check_balance = balance_records.find_one({
        "user_id" : validation["result"]["user_id"]
    })

    if check_balance is None:
        balance_user = balance_records.insert({
            "balance_id": str(uuid.uuid4().hex),
            "user_id": validation["result"]["user_id"],
            "amount": 0,
            "rec_timestamp": timenow
        })

        response = dict(
            message="Balance Not Enough"
        )
        return response
    else:
        if int(check_balance.get('amount')) < int(params.get('amount')):
            response = dict(
                message="Balance Not Enough"
            )
            return response
        elif int(check_balance.get('amount')) >= int(params.get('amount')):
            amount_before = int(check_balance.get('amount'))
            amount_after = int(check_balance.get('amount')) - int(params.get('amount'))

            update_topup = balance_records.update(
                        {'user_id': check_balance.get('user_id')},
                        {'$set': {
                            "amount": amount_after
                        }}
            )

            payment_user = payment_records.insert({
                "payment_id": str(uuid.uuid4().hex),
                "user_id": validation["result"]["user_id"],
                "remarks": params.get('remarks'),
                "amount": int(params.get('amount')),
                "balance_before": amount_before,
                "balance_after": amount_after,
                "rec_timestamp": timenow
            })

            check_balance = balance_records.find_one({
                "user_id" : validation["result"]["user_id"]
            })

    check_payment  = payment_records.find_one({
        "_id" : ObjectId(payment_user)
    })

    if check_payment is not None:
        response_data = dict(
            payment_id=check_payment.get('payment_id'),
            remarks=check_payment.get('remarks'),
            amount=int(check_payment.get('amount')),
            balance_before=check_payment.get('balance_before'),
            balance_after=check_payment.get('balance_after'),
            created_date=datetime.datetime.fromtimestamp(check_payment.get('rec_timestamp')/1000).strftime('%Y-%m-%d %H:%M:%S')
        )

    response = dict(
        message="SUCCESS",
        result=response_data
    )

    return response

@app.route('/transfer', methods=['POST'])
def transfer():
    params = request.json
    response_data = dict()
    balance_user = ""
    payment_user = ""
    amount_now = 0
    amount_before = 0
    amount_after = 0
    timenow = int(time.time() * 1000)
    headers = request.headers

    bearer_token = headers.get('Authorization')
    bearer_token = bearer_token.strip().split(' ')
    validation = validate_token(bearer_token[1])

    if validation is not None:
        if validation.get('result') is None:
            return validation

    check_balance = balance_records.find_one({
        "user_id" : validation["result"]["user_id"]
    })

    if check_balance is None:
        balance_user = balance_records.insert({
            "balance_id": str(uuid.uuid4().hex),
            "user_id": validation["result"]["user_id"],
            "amount": 0,
            "rec_timestamp": timenow
        })

        response = dict(
            message="Balance Not Enough"
        )
        return response
    else:
        if int(check_balance.get('amount')) < int(params.get('amount')):
            response = dict(
                message="Balance Not Enough"
            )
            return response
        elif int(check_balance.get('amount')) >= int(params.get('amount')):
            amount_before = int(check_balance.get('amount'))
            amount_after = int(check_balance.get('amount')) - int(params.get('amount'))

            update_topup = balance_records.update(
                        {'user_id': check_balance.get('user_id')},
                        {'$set': {
                            "amount": amount_after
                        }}
            )

            check_target = balance_records.find_one({
                "user_id" : params.get('target_user')
            })

            target_topup = balance_records.update(
                        {'user_id': check_target.get('user_id')},
                        {'$set': {
                            "amount": int(check_target.get('amount')) + int(params.get('amount'))
                        }}
            )

            payment_user = transfer_records.insert({
                "transfer_id": str(uuid.uuid4().hex),
                "user_id": validation["result"]["user_id"],
                "remarks": params.get('remarks'),
                "amount": int(params.get('amount')),
                "balance_before": amount_before,
                "balance_after": amount_after,
                "rec_timestamp": timenow
            })

            check_balance = balance_records.find_one({
                "user_id" : validation["result"]["user_id"]
            })

    check_transfer  = transfer_records.find_one({
        "_id" : ObjectId(payment_user)
    })

    if check_transfer is not None:
        response_data = dict(
            transfer_id=check_transfer.get('transfer_id'),
            remarks=check_transfer.get('remarks'),
            amount=int(check_transfer.get('amount')),
            balance_before=check_transfer.get('balance_before'),
            balance_after=check_transfer.get('balance_after'),
            created_date=datetime.datetime.fromtimestamp(check_transfer.get('rec_timestamp')/1000).strftime('%Y-%m-%d %H:%M:%S')
        )

    response = dict(
        message="SUCCESS",
        result=response_data
    )

    return response

def formatter_payment(payment_data, transfer_data, topup_data):
    list_payment = list()
    for item in payment_data:
        serialized_data = dict(
            payment_id=item.get('payment_id', ''),
            created_date=datetime.datetime.fromtimestamp(item.get('rec_timestamp') / 1000).strftime('%Y-%m-%d %H:%M:%S'),
            amount=item.get('amount'),
            balance_before=item.get('balance_before'),
            balance_after=item.get('balance_after'),
            remarks=item.get('remarks')
        )
        list_payment.append(serialized_data)

    for item_tf in transfer_data:
        data_tf = dict(
            transfer_id=item_tf.get('transfer_id', ''),
            created_date=datetime.datetime.fromtimestamp(item_tf.get('rec_timestamp') / 1000).strftime('%Y-%m-%d %H:%M:%S'),
            amount=item_tf.get('amount'),
            balance_before=item_tf.get('balance_before'),
            balance_after=item_tf.get('balance_after'),
            remarks=item_tf.get('remarks')
        )
        list_payment.append(data_tf)

    for item_tp in topup_data:
        data_tp = dict(
            top_up_id=item_tp.get('top_up_id', ''),
            created_date=datetime.datetime.fromtimestamp(item_tp.get('rec_timestamp') / 1000).strftime('%Y-%m-%d %H:%M:%S'),
            amount=item_tp.get('amount'),
            balance_before=item_tp.get('balance_before'),
            balance_after=item_tp.get('balance_after')
        )
        list_payment.append(data_tp)

    return list_payment

@app.route('/transactions')
def transactions():
    params = request.json
    headers = request.headers

    bearer_token = headers.get('Authorization')
    bearer_token = bearer_token.strip().split(' ')
    validation = validate_token(bearer_token[1])

    if validation is not None:
        if validation.get('result') is None:
            return validation

    query_payment = dict(
        user_id=validation["result"]["user_id"]
    )

    data_payment = payment_records.find(query_payment)

    query_transfer = dict(
        user_id=validation["result"]["user_id"]
    )

    data_transfer = transfer_records.find(query_transfer)

    query_topup = dict(
        user_id=validation["result"]["user_id"]
    )

    data_topup = topup_records.find(query_topup)

    serialized_data = formatter_payment(data_payment, data_transfer, data_topup)
    
    response = dict(
        message="SUCCESS",
        result=serialized_data
    )
    return response

if __name__ == '__main__':
    app.run()
