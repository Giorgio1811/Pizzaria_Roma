from django.urls import path
from . import views


urlpatterns = [
    path('', views.cardapio, name='cardapio'),
    path('carrinho/', views.ver_carrinho, name='ver_carrinho'),
    path(
        'carrinho/adicionar/<int:produto_id>/',
        views.adicionar_ao_carrinho,
        name='adicionar_ao_carrinho',
    ),
    path(
        'carrinho/remover/<int:produto_id>/',
        views.remover_do_carrinho,
        name='remover_do_carrinho',
    ),
    path('finalizar/', views.finalizar_pedido, name='finalizar_pedido'),
    path('acompanhar/', views.acompanhar_pedido, name='acompanhar_pedido'),
]
