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

    def test_register(self):
        letters = string.ascii_lowercase

        params_regis = {
            "first_name":''.join(random.choice(letters) for i in range(7)),
            "last_name":''.join(random.choice(letters) for i in range(10)),
            "phone_number":"0888" + str(randrange(8)),
            "address":''.join(random.choice(letters) for i in range(20)),
            "pin":str(randrange(6))
        }

        response = requests.post('http://127.0.0.1:5000/register', json=params_regis)
        hasil = response.json()
        
        self.assertEqual("SUCCESS", hasil.get('message'))

if __name__ == '__main__':
    unittest.main()