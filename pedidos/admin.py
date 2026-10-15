from django.contrib import admin
from .models import Categoria, Produto, Pedido, ItemPedido


# Register your models here.
class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome',)


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'preco', 'disponivel')
    list_filter = ('categoria', 'disponivel')
    search_fields = ('nome',)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'nome_cliente',
        'status',
        'valor_total',
        'data_criacao',
    )
    list_filter = ('status',)
    inlines = [ItemPedidoInline]
