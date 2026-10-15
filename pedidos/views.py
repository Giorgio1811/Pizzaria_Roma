from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.views.decorators.http import require_POST
from decimal import Decimal
from .models import Produto, Pedido, ItemPedido, Categoria


def cardapio(request):
    categorias = Categoria.objects.prefetch_related('produtos').all()
    return render(request, 'pedidos/cardapio.html', {'categorias': categorias})


@require_POST
def adicionar_ao_carrinho(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id, disponivel=True)
    carrinho = request.session.get('carrinho', {})
    chave = str(produto_id)

    if chave in carrinho:
        carrinho[chave]['quantidade'] += 1
    else:
        carrinho[chave] = {
            'nome': produto.nome,
            'preco': str(produto.preco),
            'quantidade': 1,
        }

    request.session['carrinho'] = carrinho
    messages.success(request, f'{produto.nome} adicionado ao carrinho.')
    return redirect('cardapio')


def ver_carrinho(request):
    carrinho = request.session.get('carrinho', {})
    itens = []
    total = Decimal('0.00')

    for produto_id, dados in carrinho.items():
        preco = Decimal(dados['preco'])
        subtotal = preco * dados['quantidade']
        total += subtotal
        itens.append({
            'produto_id': produto_id,
            'nome': dados['nome'],
            'preco': preco,
            'quantidade': dados['quantidade'],
            'subtotal': subtotal,
        })

    context = {
        'itens': itens,
        'total': total,
    }
    return render(request, 'pedidos/carrinho.html', context)


@require_POST
def remover_do_carrinho(request, produto_id):
    carrinho = request.session.get('carrinho', {})
    chave = str(produto_id)

    if chave in carrinho:
        del carrinho[chave]
        request.session['carrinho'] = carrinho

    return redirect('ver_carrinho')


def finalizar_pedido(request):
    carrinho = request.session.get('carrinho', {})

    if not carrinho:
        messages.warning(request, 'Seu carrinho está vazio.')
        return redirect('cardapio')

    if request.method == 'POST':
        nome = request.POST.get('nome_cliente', '').strip()
        telefone = request.POST.get('telefone_cliente', '').strip()
        endereco = request.POST.get('endereco_entrega', '').strip()

        if not (nome and telefone and endereco):
            messages.warning(request, 'Preencha nome, telefone e endereço.')
            return redirect('ver_carrinho')

        if len(nome) > 100 or len(telefone) > 20 or len(endereco) > 200:
            messages.warning(request, 'Algum campo passou do tamanho máximo.')
            return redirect('ver_carrinho')

        total = Decimal('0.00')
        for dados in carrinho.values():
            total += Decimal(dados['preco']) * dados['quantidade']

        # Grava pedido e itens juntos: se um produto do carrinho não existir
        # mais, nada é salvo (evita pedido sem itens no banco)
        with transaction.atomic():
            pedido = Pedido.objects.create(
                nome_cliente=nome,
                telefone_cliente=telefone,
                endereco_entrega=endereco,
                valor_total=total,
            )

            for produto_id, dados in carrinho.items():
                produto = get_object_or_404(Produto, id=produto_id)
                ItemPedido.objects.create(
                    pedido=pedido,
                    produto=produto,
                    quantidade=dados['quantidade'],
                    preco_unitario=Decimal(dados['preco']),
                )

        request.session['carrinho'] = {}
        return render(
            request,
            'pedidos/pedido_confirmado.html',
            {'pedido': pedido},
        )

    return redirect('ver_carrinho')


def acompanhar_pedido(request):
    pedido = None

    if request.method == 'POST':
        pedido_id = request.POST.get('pedido_id', '').strip()
        if pedido_id.isdigit():
            pedido = Pedido.objects.filter(id=pedido_id).first()

        if not pedido:
            messages.error(request, 'Pedido não encontrado.')

    return render(request, 'pedidos/acompanhar.html', {'pedido': pedido})
