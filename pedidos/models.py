from django.db import models


class Categoria(models.Model):
    nome = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'


class Produto(models.Model):
    categoria = models.ForeignKey(
        Categoria, on_delete=models.CASCADE, related_name='produtos'
    )
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=6, decimal_places=2)
    imagem = models.ImageField(upload_to='produtos/', blank=True, null=True)
    disponivel = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


class Pedido(models.Model):
    STATUS_CHOICES = [
        ('recebido', 'Recebido'),
        ('preparo', 'Em preparo'),
        ('entrega', 'Saiu para entrega'),
        ('finalizado', 'Entregue'),
    ]
    nome_cliente = models.CharField(max_length=100)
    telefone_cliente = models.CharField(max_length=20)
    endereco_entrega = models.CharField(max_length=200)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='recebido'
    )
    data_criacao = models.DateTimeField(auto_now_add=True)
    valor_total = models.DecimalField(
        max_digits=8, decimal_places=2, default=0
    )

    class Meta:
        ordering = ('-data_criacao',)

    def __str__(self):
        return f'Pedido #{self.id} - {self.nome_cliente}'


class ItemPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido, on_delete=models.CASCADE, related_name='itens'
    )
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=6, decimal_places=2)

    def subtotal(self):
        return self.quantidade * self.preco_unitario
