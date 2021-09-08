import unittest, random, string, requests
from random import randrange
from app import *

class TestPayments(unittest.TestCase):

    def test_secret_key(self):
        params = {
            "pin": "323770"
        }

        hash_pin = secret_key(key=str(params.get('pin')), unique_key='BARRUTAMPAN')

        self.assertEqual(64, len(hash_pin))

    def test_success_register(self):
        letters = string.ascii_lowercase

        params_regis = {
            "first_name":''.join(random.choice(letters) for i in range(7)),
            "last_name":''.join(random.choice(letters) for i in range(10)),
            "phone_number":"0881" + str(random.randint(3333333,9888888)),
            "address":''.join(random.choice(letters) for i in range(20)),
            "pin":str(randrange(222222,777777))
        }

        response = requests.post('http://127.0.0.1:5000/register', json=params_regis)
        hasil = response.json()

        self.assertEqual("SUCCESS", hasil.get('message'))

    def test_failed_register_phone_exists(self):

        params_regis ={
            "first_name":"jason",
            "last_name":"ui",
            "phone_number":"088813338800",
            "address":"jalan jauh lewat jagarasa",
            "pin":"323770"
        }

        response = requests.post('http://127.0.0.1:5000/register', json=params_regis)
        hasil = response.json()
        
        self.assertEqual("Phone number already existed", hasil.get('message'))

    def test_success_login(self):

        params_login = {
            "phone_number":"088813338800",
            "pin":"323770"
        }

        response = requests.post('http://127.0.0.1:5000/login', json=params_login)
        hasil = response.json()
        
        self.assertEqual("SUCCESS", hasil.get('message'))

    def test_failed_login(self):

        params_login = {
            "phone_number":"08000000000",
            "pin":"111111"
        }

        response = requests.post('http://127.0.0.1:5000/login', json=params_login)
        hasil = response.json()
        
        self.assertEqual("Phone number and pin doesn’t match.", hasil.get('message'))

    def test_success_update_profile(self):
        letters = string.ascii_lowercase
        auth_token='87a634dadc83480421e5166236515a988b729695c9a89a754212a752300f2e5a'
        hed = {'Authorization': 'Bearer ' + auth_token}

        params_update ={
            "first_name":''.join(random.choice(letters) for i in range(7)),
            "last_name":''.join(random.choice(letters) for i in range(12)),
            "phone_number":"088888999911",
            "address":"jalan jauh lewat jagarasa",
        }

        response = requests.put('http://127.0.0.1:5000/update-profile', json=params_update, headers=hed)
        hasil = response.json()
        
        self.assertEqual("Unauthenticated", hasil.get('message'))

if __name__ == '__main__':
    unittest.main()