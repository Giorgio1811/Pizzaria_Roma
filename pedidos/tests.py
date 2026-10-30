from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Categoria, ItemPedido, Pedido, Produto


class PedidoFlowTests(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nome='Pizzas')
        self.produto = Produto.objects.create(
            categoria=self.categoria,
            nome='Margherita',
            descricao='Tomate e manjericao',
            preco=Decimal('40.00'),
        )

    def test_cart_uses_current_product_data(self):
        self.client.post(
            reverse('adicionar_ao_carrinho', args=[self.produto.id])
        )
        self.produto.nome = 'Margherita especial'
        self.produto.preco = Decimal('45.00')
        self.produto.save()

        response = self.client.get(reverse('ver_carrinho'))
        self.assertContains(response, 'Margherita especial')
        self.assertContains(response, '45,00')

    def test_checkout_persists_current_price_atomically(self):
        self.client.post(
            reverse('adicionar_ao_carrinho', args=[self.produto.id])
        )
        response = self.client.post(
            reverse('finalizar_pedido'),
            {
                'nome_cliente': 'Cliente Teste',
                'telefone_cliente': '(61) 99999-9999',
                'endereco_entrega': 'Rua Teste, 1',
            },
        )
        pedido = Pedido.objects.get()
        item = ItemPedido.objects.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(pedido.valor_total, self.produto.preco)
        self.assertEqual(item.preco_unitario, self.produto.preco)
        self.assertFalse(self.client.session.get('carrinho'))

    def test_checkout_rejects_unavailable_products(self):
        self.client.post(
            reverse('adicionar_ao_carrinho', args=[self.produto.id])
        )
        self.produto.disponivel = False
        self.produto.save()

        response = self.client.post(
            reverse('finalizar_pedido'),
            {
                'nome_cliente': 'Cliente Teste',
                'telefone_cliente': '(61) 99999-9999',
                'endereco_entrega': 'Rua Teste, 1',
            },
        )
        self.assertRedirects(response, reverse('ver_carrinho'))
        self.assertFalse(Pedido.objects.exists())

    def test_tracking_requires_matching_phone(self):
        pedido = Pedido.objects.create(
            nome_cliente='Cliente Teste',
            telefone_cliente='(61) 99999-9999',
            endereco_entrega='Rua Teste, 1',
            valor_total=Decimal('40.00'),
        )
        response = self.client.post(
            reverse('acompanhar_pedido'),
            {'pedido_id': pedido.id, 'telefone_cliente': '(61) 00000-0000'},
        )
        self.assertNotContains(response, 'badge-recebido')

        response = self.client.post(
            reverse('acompanhar_pedido'),
            {'pedido_id': pedido.id, 'telefone_cliente': pedido.telefone_cliente},
        )
        self.assertContains(response, 'badge-recebido')
        self.assertNotContains(response, 'Cliente Teste')
