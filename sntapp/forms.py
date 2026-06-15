from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, News, Document
from django.core.exceptions import ValidationError
from .models import ImportantAnnouncement

class UserRegistrationForm(UserCreationForm):
    username = None
    
    lot_number = forms.CharField(
        label='Номер участка',
        help_text='Ваш номер участка в СНТ "Ивушка" (будет использоваться как логин)',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 pl-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-snt-green',
            'placeholder': 'Например: 123',
            'autofocus': True
        })
    )
    
    full_name = forms.CharField(
        label='ФИО',
        required=True,
        help_text='Ваше полное имя',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 pl-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-snt-green',
            'placeholder': 'Иванов Иван Иванович'
        })
    )
    
    phone = forms.CharField(
        label='Телефон',
        required=True,
        help_text='Контактный телефон',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 pl-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-snt-green',
            'placeholder': '+7 (XXX) XXX-XX-XX'
        })
    )
    
    email = forms.EmailField(
        label='Email',
        required=True,
        help_text='Электронная почта',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 pl-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-snt-green',
            'placeholder': 'example@mail.ru'
        })
    )
    
    password1 = forms.CharField(
        label='Пароль',
        help_text='Минимум 8 символов',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 pl-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-snt-green',
            'placeholder': 'Введите пароль'
        })
    )
    
    password2 = forms.CharField(
        label='Подтверждение пароля',
        help_text='Введите тот же пароль еще раз',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 pl-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-snt-green',
            'placeholder': 'Повторите пароль'
        })
    )
    
    class Meta:
        model = User
        fields = ['lot_number', 'full_name', 'phone', 'email', 'password1', 'password2']
    
    def clean_lot_number(self):
        lot_number = self.cleaned_data.get('lot_number')
        if User.objects.filter(lot_number=lot_number).exists():
            raise ValidationError('Пользователь с таким номером участка уже зарегистрирован')
        if User.objects.filter(username=lot_number).exists():
            raise ValidationError('Пользователь с таким номером участка уже зарегистрирован')
        return lot_number
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['lot_number']
        user.lot_number = self.cleaned_data['lot_number']
        if commit:
            user.save()
        return user
    
class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['title', 'content', 'image', 'is_published']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
        }

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'description', 'document_type', 'file', 'preview', 'is_important', 'is_visible']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
            'title': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
            'document_type': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
            'file': forms.FileInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
            'preview': forms.FileInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
        }

class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(
        label='Excel файл с долгами',
        help_text='Файл должен содержать колонки: Номер участка, ФИО, Членские взносы, Целевые взносы',
        widget=forms.FileInput(attrs={'accept': '.xlsx, .xls, .csv'})
    )
    
    period = forms.CharField(
        label='Период',
        max_length=20,
        required=False,
        help_text='Например: 2024-01 (если не указано в файле)',
        widget=forms.TextInput(attrs={'placeholder': '2024-01'})
    )

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = ImportantAnnouncement
        fields = ['title', 'content', 'expire_at']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg',
                'placeholder': 'Заголовок объявления'
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg',
                'rows': 4,
                'placeholder': 'Текст объявления...'
            }),
            'expire_at': forms.DateTimeInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg',
                'type': 'datetime-local'
            }),
        }