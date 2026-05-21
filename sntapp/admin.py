from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Debt, News, Document
from .models import StaticPage, ManagementMember, ContactInfo

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'full_name', 'lot_number', 'phone', 'is_moderator', 'is_staff']
    list_filter = ['is_moderator', 'is_staff', 'is_active']
    search_fields = ['username', 'full_name', 'lot_number', 'phone']
    fieldsets = UserAdmin.fieldsets + (
        ('Информация СНТ', {'fields': ('full_name', 'lot_number', 'phone', 'is_moderator')}),
    )

@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    list_display = ['user', 'fee_type', 'amount', 'period', 'updated_at']
    list_filter = ['fee_type', 'period']
    search_fields = ['user__full_name', 'user__lot_number']
    raw_id_fields = ['user']

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at', 'author', 'is_published']
    list_filter = ['is_published', 'created_at']
    search_fields = ['title', 'content']
    date_hierarchy = 'created_at'

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'uploaded_at', 'uploaded_by']
    list_filter = ['document_type', 'is_visible']
    search_fields = ['title']

@admin.register(StaticPage)
class StaticPageAdmin(admin.ModelAdmin):
    list_display = ['page_type', 'title', 'is_active', 'updated_at']
    list_filter = ['page_type', 'is_active']
    search_fields = ['title', 'content']
    fieldsets = (
        ('Основная информация', {
            'fields': ('page_type', 'title', 'content', 'image')
        }),
        ('SEO настройки', {
            'fields': ('seo_title', 'seo_description'),
            'classes': ('collapse',)
        }),
        ('Настройки отображения', {
            'fields': ('order', 'is_active')
        }),
    )

@admin.register(ManagementMember)
class ManagementMemberAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'position', 'phone', 'email', 'order', 'is_active']
    list_filter = ['position', 'is_active']
    search_fields = ['full_name', 'phone', 'email']
    list_editable = ['order', 'is_active']

@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ['contact_type', 'value', 'order', 'is_active']
    list_filter = ['contact_type', 'is_active']
    search_fields = ['value']
    list_editable = ['order', 'is_active']