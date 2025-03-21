from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Category, Transaction
from .serializers import CategorySerializer, TransactionSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from datetime import datetime

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def filter_transactions(self, request):
        transactions = self.get_queryset()

        # Фильтрация по дате
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        if date_from:
            transactions = transactions.filter(date__gte=datetime.strptime(date_from, '%Y-%m-%d'))
        if date_to:
            transactions = transactions.filter(date__lte=datetime.strptime(date_to, '%Y-%m-%d'))

        # Фильтрация по категории
        category_id = request.query_params.get('category', None)
        if category_id:
            transactions = transactions.filter(category_id=category_id)

        # Фильтрация по сумме
        amount_min = request.query_params.get('amount_min', None)
        amount_max = request.query_params.get('amount_max', None)
        if amount_min:
            transactions = transactions.filter(amount__gte=amount_min)
        if amount_max:
            transactions = transactions.filter(amount__lte=amount_max)

        # Суммирование по категориям
        total = transactions.aggregate(Sum('amount'))['amount__sum']

        return Response({'transactions': TransactionSerializer(transactions, many=True).data, 'total': total})



import pandas as pd
from django.http import HttpResponse

@action(detail=False, methods=['get'])
def export_csv(self, request):
    transactions = self.get_queryset()
    data = TransactionSerializer(transactions, many=True).data
    df = pd.DataFrame(data)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    df.to_csv(path_or_buffer=response, index=False)
    return response



from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import HttpResponse

@action(detail=False, methods=['get'])
def export_pdf(self, request):
    transactions = self.get_queryset()
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="transactions.pdf"'
    p = canvas.Canvas(response, pagesize=letter)
    p.drawString(100, 800, "Transactions")
    y_position = 780
    for transaction in transactions:
        p.drawString(100, y_position, f"{transaction.date} - {transaction.category.name} - {transaction.amount}")
        y_position -= 20
    p.showPage()
    p.save()
    return response
