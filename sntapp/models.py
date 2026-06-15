from django.utils import timezone

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
import os

class User(AbstractUser):
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Номер телефона должен быть в формате: +999999999. До 15 цифр."
    )
    
    full_name = models.CharField('ФИО', max_length=200, blank=True)
    lot_number = models.CharField(
        'Номер участка', 
        max_length=10, 
        unique=True, 
        blank=True, 
        null=True,
        help_text="Номер участка в СНТ (используется как логин)"
    )
    phone = models.CharField(
        'Телефон', 
        validators=[phone_regex], 
        max_length=17, 
        blank=True
    )
    is_moderator = models.BooleanField(
        'Модератор',
        default=False,
        help_text="Может управлять новостями и документами"
    )
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['lot_number']
    
    def __str__(self):
        if self.full_name:
            return f"{self.full_name} (уч. {self.lot_number or 'не указан'})"
        return self.username

class Debt(models.Model):
    
    MEMBERSHIP_FEE = 'membership' 
    TARGET_FEE = 'target'  
    OTHER_FEE = 'other' 
    
    FEE_TYPES = [
        (MEMBERSHIP_FEE, 'Членский взнос'),
        (TARGET_FEE, 'Целевой взнос'),
        (OTHER_FEE, 'Прочие взносы'),
    ]
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='debts',
        verbose_name='Пользователь'
    )
    fee_type = models.CharField(
        'Тип взноса', 
        max_length=20, 
        choices=FEE_TYPES
    )
    amount = models.DecimalField(
        'Сумма долга', 
        max_digits=10, 
        decimal_places=2, 
        default=0
    )
    period = models.CharField('Период', max_length=20, help_text="Например: 2024-01")
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Долг'
        verbose_name_plural = 'Долги'
        unique_together = ['user', 'fee_type', 'period']
        ordering = ['user', '-period']
    
    def __str__(self):
        return f"{self.user.full_name} - {self.get_fee_type_display()}: {self.amount} руб."

class News(models.Model):
    
    title = models.CharField('Заголовок', max_length=200)
    content = models.TextField('Текст новости')
    image = models.ImageField(
        'Изображение', 
        upload_to='news_images/%Y/%m/%d/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    author = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='news',
        verbose_name='Автор'
    )
    is_published = models.BooleanField('Опубликовано', default=True)
    
    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class Document(models.Model):
    DOCUMENT_TYPES = [
        ('charter', 'Устав СНТ'),
        ('protocol', 'Протокол собрания'),
        ('report', 'Отчет правления'),
        ('financial', 'Финансовые документы'),
        ('regulations', 'Положения и регламенты'),
        ('contract', 'Договоры'),
        ('other', 'Прочее'),
    ]
    
    title = models.CharField('Название документа', max_length=200)
    description = models.TextField('Описание', blank=True, help_text="Краткое описание документа")
    document_type = models.CharField('Тип документа', max_length=20, choices=DOCUMENT_TYPES, default='other')
    file = models.FileField('Файл', upload_to='documents/%Y/%m/%d/')
    preview = models.ImageField(
        'Превью', 
        upload_to='document_previews/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text="Миниатюра для предпросмотра документа (опционально)"
    )
    file_size = models.IntegerField('Размер файла (байт)', editable=False, default=0)
    downloads_count = models.IntegerField('Количество скачиваний', default=0)
    uploaded_at = models.DateTimeField('Дата загрузки', auto_now_add=True)
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='uploaded_documents',
        verbose_name='Загрузил'
    )
    is_visible = models.BooleanField('Видим для всех', default=True)
    is_important = models.BooleanField('Важный документ', default=False, help_text="Помечает документ как важный")
    
    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'
        ordering = ['-is_important', '-uploaded_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    def get_file_extension(self):
        return os.path.splitext(self.file.name)[1].lower()
    
    def get_file_icon(self):
        ext = self.get_file_extension()
        icons = {
            '.pdf': 'fa-file-pdf',
            '.doc': 'fa-file-word',
            '.docx': 'fa-file-word',
            '.xls': 'fa-file-excel',
            '.xlsx': 'fa-file-excel',
            '.jpg': 'fa-file-image',
            '.jpeg': 'fa-file-image',
            '.png': 'fa-file-image',
            '.zip': 'fa-file-archive',
            '.rar': 'fa-file-archive',
        }
        return icons.get(ext, 'fa-file-alt')
    
class StaticPage(models.Model):
    PAGE_TYPES = [
        ('about', 'О нас'),
        ('management', 'Правление'),
        ('info', 'Информация'),
        ('contacts', 'Контакты'),
    ]
    
    page_type = models.CharField(
        'Тип страницы', 
        max_length=20, 
        choices=PAGE_TYPES, 
        unique=True,
        help_text="Выберите тип страницы"
    )
    title = models.CharField('Заголовок', max_length=200)
    content = models.TextField('Содержание', help_text="HTML-разметка поддерживается")
    image = models.ImageField(
        'Изображение страницы', 
        upload_to='pages/%Y/%m/%d/',
        blank=True,
        null=True
    )
    seo_title = models.CharField('SEO заголовок', max_length=200, blank=True, help_text="Для поисковых систем")
    seo_description = models.CharField('SEO описание', max_length=500, blank=True)
    order = models.IntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активна', default=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='updated_pages'
    )
    
    class Meta:
        verbose_name = 'Статическая страница'
        verbose_name_plural = 'Статические страницы'
        ordering = ['order', 'page_type']
    
    def __str__(self):
        return self.get_page_type_display()
    
    def get_absolute_url(self):
        from django.urls import reverse
        url_map = {
            'about': 'about',
            'management': 'management',
            'info': 'info',
            'contacts': 'contacts',
        }
        return reverse(url_map.get(self.page_type, 'home'))


class ManagementMember(models.Model):
    POSITION_CHOICES = [
        ('chairman', 'Председатель'),
        ('deputy', 'Заместитель председателя'),
        ('treasurer', 'Казначей'),
        ('secretary', 'Секретарь'),
        ('member', 'Член правления'),
        ('auditor', 'Ревизор'),
    ]
    
    full_name = models.CharField('ФИО', max_length=200)
    position = models.CharField('Должность', max_length=20, choices=POSITION_CHOICES)
    phone = models.CharField('Телефон', max_length=20, blank=True)
    email = models.EmailField('Email', blank=True)
    photo = models.ImageField('Фото', upload_to='management/%Y/%m/%d/', blank=True, null=True)
    description = models.TextField('Описание', blank=True, help_text="Краткая информация о члене правления")
    order = models.IntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активен', default=True)
    
    class Meta:
        verbose_name = 'Член правления'
        verbose_name_plural = 'Члены правления'
        ordering = ['order', 'position']
    
    def __str__(self):
        return f"{self.get_position_display()}: {self.full_name}"


class ContactInfo(models.Model):  
    CONTACT_TYPES = [
        ('phone', 'Телефон'),
        ('email', 'Email'),
        ('address', 'Адрес'),
        ('schedule', 'Режим работы'),
        ('social', 'Социальная сеть'),
        ('other', 'Другое'),
    ]
    
    contact_type = models.CharField('Тип контакта', max_length=20, choices=CONTACT_TYPES)
    value = models.CharField('Значение', max_length=300)
    icon = models.CharField('Иконка', max_length=50, blank=True, help_text="Font Awesome иконка (например, fas fa-phone)")
    order = models.IntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активен', default=True)
    
    class Meta:
        verbose_name = 'Контактная информация'
        verbose_name_plural = 'Контактная информация'
        ordering = ['order', 'contact_type']
    
    def __str__(self):
        return f"{self.get_contact_type_display()}: {self.value}"
    
class ImportantAnnouncement(models.Model):
    title = models.CharField('Заголовок', max_length=200, default='Важное объявление')
    content = models.TextField('Текст объявления')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    is_active = models.BooleanField('Активно', default=True)
    expire_at = models.DateTimeField('Дата и время удаления', blank=True, null=True, 
                                       help_text='После этой даты объявление скроется автоматически')
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='announcements'
    )
    
    class Meta:
        verbose_name = 'Важное объявление'
        verbose_name_plural = 'Важные объявления'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def is_expired(self):
        if self.expire_at and timezone.now() > self.expire_at:
            return True
        return False