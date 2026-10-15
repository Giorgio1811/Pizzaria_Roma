import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from pedidos.models import Categoria, Produto, Pedido, ItemPedido


# Preços de pizza grande (8 fatias) em pizzarias de bairro, 2026
SABORES = [
    ('Pizzas Salgadas', 'Mussarela', 'Molho de tomate, mussarela e orégano', '47.90'),
    ('Pizzas Salgadas', 'Calabresa', 'Molho de tomate, mussarela, calabresa fatiada e cebola', '49.90'),
    ('Pizzas Salgadas', 'Margherita', 'Molho de tomate, mussarela de búfala, tomate e manjericão', '54.90'),
    ('Pizzas Salgadas', 'Napolitana', 'Molho de tomate, mussarela, tomate, parmesão e alho', '52.90'),
    ('Pizzas Salgadas', 'Portuguesa', 'Mussarela, presunto, ovo, cebola, ervilha e azeitona', '56.90'),
    ('Pizzas Salgadas', 'Toscana', 'Mussarela, linguiça toscana moída e cebola', '57.90'),
    ('Pizzas Salgadas', 'Frango com Catupiry', 'Frango desfiado temperado e Catupiry original', '58.90'),
    ('Pizzas Salgadas', 'Palmito', 'Mussarela, palmito, tomate e azeitona', '58.90'),
    ('Pizzas Salgadas', 'Atum', 'Mussarela, atum sólido e cebola roxa', '59.90'),
    ('Pizzas Salgadas', 'Bacon', 'Mussarela, bacon crocante e milho', '59.90'),
    ('Pizzas Salgadas', 'Lombo com Catupiry', 'Lombo canadense defumado e Catupiry', '61.90'),
    ('Pizzas Salgadas', 'Quatro Queijos', 'Mussarela, provolone, parmesão e gorgonzola', '62.90'),
    ('Pizzas Salgadas', 'Pepperoni', 'Mussarela e pepperoni fatiado', '64.90'),
    ('Pizzas Doces', 'Brigadeiro', 'Chocolate ao leite e granulado', '52.90'),
    ('Pizzas Doces', 'Romeu e Julieta', 'Mussarela e goiabada cascão', '54.90'),
]

NOMES = [
    'Ana', 'Bruno', 'Carla', 'Diego', 'Eduarda', 'Felipe', 'Gabriela', 'Henrique',
    'Isabela', 'João', 'Larissa', 'Marcos', 'Natália', 'Otávio', 'Paula', 'Rafael',
    'Sabrina', 'Thiago', 'Vanessa', 'Lucas', 'Juliana', 'Pedro', 'Camila', 'Gustavo',
]
SOBRENOMES = [
    'Silva', 'Souza', 'Oliveira', 'Santos', 'Lima', 'Pereira', 'Costa', 'Almeida',
    'Ferreira', 'Rodrigues', 'Carvalho', 'Gomes', 'Martins', 'Ribeiro', 'Barbosa',
]
ENDERECOS = [
    'SQN {q} Bloco {b} Apto {a}, Asa Norte',
    'SQS {q} Bloco {b} Apto {a}, Asa Sul',
    'QI {n} Conjunto {b} Casa {a}, Lago Sul',
    'Rua {n} Lote {a}, Águas Claras',
    'QNM {n} Conjunto {b} Casa {a}, Ceilândia',
    'QS {n} Conjunto {b} Casa {a}, Taguatinga',
]


class Command(BaseCommand):
    help = 'Cadastra 15 sabores de pizza e 60 pedidos de clientes fictícios.'

    def add_arguments(self, parser):
        parser.add_argument('--clientes', type=int, default=60)

    @transaction.atomic
    def handle(self, *args, **options):
        rnd = random.Random(42)

        produtos = []
        for nome_categoria, nome, descricao, preco in SABORES:
            categoria, _ = Categoria.objects.get_or_create(nome=nome_categoria)
            produto, _ = Produto.objects.update_or_create(
                nome=nome,
                defaults={
                    'categoria': categoria,
                    'descricao': descricao,
                    'preco': Decimal(preco),
                    'disponivel': True,
                },
            )
            produtos.append(produto)
        self.stdout.write(f'{len(produtos)} sabores cadastrados/atualizados.')

        combinacoes = [(n, s) for n in NOMES for s in SOBRENOMES]
        rnd.shuffle(combinacoes)
        status = [codigo for codigo, _ in Pedido.STATUS_CHOICES]
        agora = timezone.now()

        pedidos = []
        itens_por_pedido = []
        for nome, sobrenome in combinacoes[:options['clientes']]:
            escolhidos = rnd.sample(produtos, rnd.randint(1, 3))
            itens = [(p, rnd.randint(1, 2)) for p in escolhidos]
            total = sum(p.preco * qtd for p, qtd in itens)
            endereco = rnd.choice(ENDERECOS).format(
                q=rnd.choice([104, 108, 112, 202, 210, 308, 410]),
                n=rnd.randint(1, 30),
                b=rnd.choice('ABCDEFGHIJK'),
                a=rnd.randint(101, 612),
            )
            pedidos.append(Pedido(
                nome_cliente=f'{nome} {sobrenome}',
                telefone_cliente=f'(61) 9{rnd.randint(8000, 9999)}-{rnd.randint(1000, 9999)}',
                endereco_entrega=endereco,
                status=rnd.choice(status),
                valor_total=total,
            ))
            itens_por_pedido.append(itens)

        pedidos = Pedido.objects.bulk_create(pedidos)

        ItemPedido.objects.bulk_create([
            ItemPedido(pedido=pedido, produto=p, quantidade=qtd, preco_unitario=p.preco)
            for pedido, itens in zip(pedidos, itens_por_pedido)
            for p, qtd in itens
        ])

        # Espalha as datas dos pedidos pelos últimos 30 dias
        for pedido in pedidos:
            pedido.data_criacao = agora - timedelta(minutes=rnd.randint(0, 30 * 24 * 60))
        Pedido.objects.bulk_update(pedidos, ['data_criacao'])

        self.stdout.write(self.style.SUCCESS(
            f'{len(pedidos)} pedidos criados (#{pedidos[0].id} a #{pedidos[-1].id}).'
        ))
