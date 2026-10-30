from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Categoria, ItemPedido, Pedido, Produto


def _carrinho_valido(request):
    """Return sanitized session cart data with only product IDs and quantities."""
    carrinho = request.session.get('carrinho', {})
    if not isinstance(carrinho, dict):
        request.session['carrinho'] = {}
        return {}

    valido = {}
    alterado = False
    for produto_id, dados in carrinho.items():
        try:
            quantidade = int(dados.get('quantidade', 0))
            produto_id = int(produto_id)
        except (AttributeError, TypeError, ValueError):
            alterado = True
            continue
        if quantidade < 1:
            alterado = True
            continue
        quantidade_limitada = min(quantidade, 99)
        alterado = alterado or quantidade != quantidade_limitada
        valido[str(produto_id)] = {'quantidade': quantidade_limitada}

    if alterado:
        request.session['carrinho'] = valido
    return valido


def cardapio(request):
    categorias = Categoria.objects.prefetch_related('produtos').all()
    return render(request, 'pedidos/cardapio.html', {'categorias': categorias})


@require_POST
def adicionar_ao_carrinho(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id, disponivel=True)
    carrinho = _carrinho_valido(request)
    chave = str(produto_id)
    quantidade = carrinho.get(chave, {}).get('quantidade', 0)

    if quantidade >= 99:
        messages.warning(request, 'Limite de 99 unidades por produto.')
        return redirect('cardapio')

    carrinho[chave] = {'quantidade': quantidade + 1}
    request.session['carrinho'] = carrinho
    messages.success(request, f'{produto.nome} adicionado ao carrinho.')
    return redirect('cardapio')


def ver_carrinho(request):
    carrinho = _carrinho_valido(request)
    produtos = Produto.objects.filter(
        id__in=carrinho.keys(), disponivel=True
    )
    produtos_por_id = {str(produto.id): produto for produto in produtos}
    itens = []
    total = Decimal('0.00')

    for produto_id, dados in carrinho.items():
        produto = produtos_por_id.get(produto_id)
        if produto is None:
            continue
        preco = produto.preco
        subtotal = preco * dados['quantidade']
        total += subtotal
        itens.append({
            'produto_id': produto_id,
            'nome': produto.nome,
            'preco': preco,
            'quantidade': dados['quantidade'],
            'subtotal': subtotal,
        })

    return render(
        request,
        'pedidos/carrinho.html',
        {'itens': itens, 'total': total},
    )


@require_POST
def remover_do_carrinho(request, produto_id):
    carrinho = _carrinho_valido(request)
    carrinho.pop(str(produto_id), None)
    request.session['carrinho'] = carrinho
    return redirect('ver_carrinho')


def finalizar_pedido(request):
    carrinho = _carrinho_valido(request)
    if not carrinho:
        messages.warning(request, 'Seu carrinho está vazio.')
        return redirect('cardapio')

    if request.method != 'POST':
        return redirect('ver_carrinho')

    nome = request.POST.get('nome_cliente', '').strip()
    telefone = request.POST.get('telefone_cliente', '').strip()
    endereco = request.POST.get('endereco_entrega', '').strip()
    if not (nome and telefone and endereco):
        messages.warning(request, 'Preencha nome, telefone e endereço.')
        return redirect('ver_carrinho')
    if len(nome) > 100 or len(telefone) > 20 or len(endereco) > 200:
        messages.warning(request, 'Algum campo passou do tamanho máximo.')
        return redirect('ver_carrinho')

    with transaction.atomic():
        produtos = Produto.objects.select_for_update().filter(
            id__in=carrinho.keys(), disponivel=True
        )
        produtos_por_id = {str(produto.id): produto for produto in produtos}
        indisponiveis = set(carrinho) - set(produtos_por_id)
        if indisponiveis:
            request.session['carrinho'] = {
                produto_id: carrinho[produto_id]
                for produto_id in carrinho
                if produto_id not in indisponiveis
            }
            messages.warning(
                request,
                'Um ou mais produtos não estão mais disponíveis. '
                'Revise seu carrinho.',
            )
            return redirect('ver_carrinho')

        total = sum(
            (
                produto.preco * carrinho[str(produto.id)]['quantidade']
                for produto in produtos_por_id.values()
            ),
            Decimal('0.00'),
        )
        pedido = Pedido.objects.create(
            nome_cliente=nome,
            telefone_cliente=telefone,
            endereco_entrega=endereco,
            valor_total=total,
        )
        for produto_id, dados in carrinho.items():
            produto = produtos_por_id[produto_id]
            ItemPedido.objects.create(
                pedido=pedido,
                produto=produto,
                quantidade=dados['quantidade'],
                preco_unitario=produto.preco,
            )

    request.session['carrinho'] = {}
    return render(
        request,
        'pedidos/pedido_confirmado.html',
        {'pedido': pedido},
    )


def acompanhar_pedido(request):
    pedido = None
    if request.method == 'POST':
        pedido_id = request.POST.get('pedido_id', '').strip()
        telefone = request.POST.get('telefone_cliente', '').strip()
        if pedido_id.isdigit() and telefone:
            pedido = Pedido.objects.filter(
                id=pedido_id, telefone_cliente=telefone
            ).first()
        if not pedido:
            messages.error(
                request, 'Pedido não encontrado ou dados de acesso inválidos.'
            )

    return render(request, 'pedidos/acompanhar.html', {'pedido': pedido})
