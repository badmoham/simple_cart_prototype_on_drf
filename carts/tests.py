from django.test import TestCase
from rest_framework.exceptions import ValidationError

from carts.models import Cart, CartItem
from products.models import Product
from django.contrib.auth import get_user_model
from carts.exceptions import LowStockQuantityException
from carts.serializers import CartSerializer

UserModel = get_user_model()


class CartTest(TestCase):
    def get_auth_header(self, username, password):
        tokens_data = self.client.post(self.access_token_api_url, data={'username': username, 'password': password})
        access = tokens_data.json()['access']
        return {"Authorization": f"Bearer {access}"}

    def setUp(self):
        self.user_1_login_data = {
            'username': 'user_1',
            'password': 'pass',
        }

        self.user_1 = UserModel.objects.create_user(
            **self.user_1_login_data,
            # password_=self.user_1_login_data['password']
        )

        self.user_2_login_data = {
            'username': 'user_2',
            'password': 'pass',
        }

        self.user_2 = UserModel.objects.create_user(
            **self.user_2_login_data,
            # password2=self.user_2_login_data['password']
        )
        self.access_token_api_url = '/auth/api/token/'
        self.add_cart_item_url = '/cart/cart/'

    def test_add_cart_item_to_cart(self):
        headers = self.get_auth_header(**self.user_1_login_data)

        invalid_payload = {
            "items_car": [
                {
                    "products": 1,
                    "quantity": 4
                }
            ]
        }

        payload = {
            "items_cart": [
                {
                    "products": 1,
                    "quantity": 4
                }
            ]
        }

        response = self.client.post(self.add_cart_item_url, data=payload)
        assert response.status_code == 401

        with self.assertRaises(ValidationError):
            srz_obj = CartSerializer(data=invalid_payload)
            srz_obj.is_valid(raise_exception=True)

        with self.assertRaises(ValidationError):
            srz_obj = CartSerializer(data=payload)
            srz_obj.is_valid(raise_exception=True)
            srz_obj.create(validated_data={**srz_obj.validated_data, 'user': self.user_1})

        product = Product.objects.create(name='shalgham', stock_quantity=3, price=10)

        with self.assertRaises(ValidationError):
            srz_obj = CartSerializer(data=payload)
            srz_obj.is_valid(raise_exception=True)
            srz_obj.create(validated_data={**srz_obj.validated_data, 'user': self.user_1})

        product.stock_quantity = 7
        product.save()

        cart = Cart.objects.create(user=self.user_1)
        cart_updated_before_api_call = cart.updated

        response = self.client.post(self.add_cart_item_url, content_type='application/json', headers=headers, data=payload)
        assert response.status_code == 201

        user_1_cart_qs = Cart.objects.filter(user=self.user_1)

        assert user_1_cart_qs.count() == 1
        items = list(CartItem.objects.filter(cart=user_1_cart_qs.get()))

        assert len(items) == 1

        item = items[0]
        item: CartItem

        assert item.quantity == 4
        assert item.products_id == 1
        assert item.cart_id == 1

        product.refresh_from_db()
        assert product.stock_quantity == 7 - 4

        cart.refresh_from_db()
        assert cart.updated != cart_updated_before_api_call
        assert cart.is_dead is False

        cart.kill()
        cart.refresh_from_db()

        assert cart.is_dead is True

        item.refresh_from_db()
        assert item.quantity == 4

        product.refresh_from_db()
        assert product.stock_quantity == 7

        payload = {
            "items_cart": [
                {
                    "products": 1,
                    "quantity": 2
                }
            ]
        }

        response = self.client.post(self.add_cart_item_url, content_type='application/json', headers=headers, data=payload)
        assert response.status_code == 201

        cart.refresh_from_db()
        product.refresh_from_db()
        item.refresh_from_db()

        assert cart.is_dead is False
        assert item.quantity == 2
        self.assertEqual(product.stock_quantity, 7 - 2)
        assert product.stock_quantity == 7 - 2

    def test_get_cart_api(self):
        headers = self.get_auth_header(**self.user_1_login_data)

        sosis = Product.objects.create(name='sossssis', stock_quantity=10, price=50)
        kalbas = Product.objects.create(name='kalbas', stock_quantity=7, price=100)

        cart = Cart.objects.create(user=self.user_1)
        CartItem.objects.create(cart=cart, products=sosis, quantity=4)
        CartItem.objects.create(cart=cart, products=kalbas, quantity=3)

        expect_response = [
            {
                "id": cart.id,
                "user": self.user_1.id,
                "updated": cart.updated.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),  # 2024-10-11T00:04:33.319
                "is_dead": False,
                "items_cart": [
                    {
                        "id": 1,
                        "products": 1,
                        "quantity": 4
                    },
                    {
                        "id": 2,
                        "products": 2,
                        "quantity": 3
                    }
                ]
            }
        ]

        response = self.client.get(self.add_cart_item_url, content_type='application/json', headers=headers)
        assert response.status_code == 200
        self.assertEqual(response.json(), expect_response)