from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum
from .models import User, News, Document, Debt
from .forms import ExcelUploadForm, UserRegistrationForm, NewsForm, DocumentForm
from .utils import parse_excel_debts, get_debt_summary, get_user_total_debt
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect
from .models import ImportantAnnouncement
from .forms import AnnouncementForm

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация успешно завершена!')
            return redirect('profile')
    else:
        form = UserRegistrationForm()
    return render(request, 'sntapp/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Добро пожаловать!')
            return redirect('profile')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    return render(request, 'sntapp/login.html')

def user_logout(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('home')

def home(request):
    news_list = News.objects.filter(is_published=True)[:6]
    
    active_announcement = ImportantAnnouncement.objects.filter(
        is_active=True
    ).first()
    
    if active_announcement and active_announcement.is_expired():
        active_announcement.is_active = False
        active_announcement.save()
        active_announcement = None
    
    return render(request, 'sntapp/home.html', {
        'news_list': news_list,
        'active_announcement': active_announcement
    })

from .models import StaticPage, ManagementMember, ContactInfo

def about(request):
    page = StaticPage.objects.filter(page_type='about', is_active=True).first()
    if not page:
        page = StaticPage.objects.create(
            page_type='about',
            title='О нас',
            content='<p>СНТ "Ивушка" - это уютное садоводческое товарищество, расположенное в живописном месте Московской области. Мы гордимся нашей историей и заботимся о каждом участке.</p>'
        )
    
    return render(request, 'sntapp/about.html', {'page': page})

def management(request):
    page = StaticPage.objects.filter(page_type='management', is_active=True).first()
    if not page:
        page = StaticPage.objects.create(
            page_type='management',
            title='Правление СНТ',
            content='<p>Правление СНТ "Ивушка" работает для блага всех садоводов. Мы открыты к диалогу и всегда готовы помочь.</p>'
        )
    
    members = ManagementMember.objects.filter(is_active=True)
    
    return render(request, 'sntapp/management.html', {
        'page': page,
        'members': members
    })

def info(request):
    page = StaticPage.objects.filter(page_type='info', is_active=True).first()
    if not page:
        page = StaticPage.objects.create(
            page_type='info',
            title='Полезная информация',
            content='<p>Здесь вы найдете важную информацию о жизни в СНТ "Ивушка": правила, регламенты, полезные советы.</p>'
        )
    
    return render(request, 'sntapp/info.html', {'page': page})

def contacts(request):
    page = StaticPage.objects.filter(page_type='contacts', is_active=True).first()
    if not page:
        page = StaticPage.objects.create(
            page_type='contacts',
            title='Контакты',
            content='<p>Свяжитесь с нами любым удобным способом. Мы всегда рады ответить на ваши вопросы!</p>'
        )
    
    contacts_list = ContactInfo.objects.filter(is_active=True)
    
    contacts_by_type = {}
    for contact in contacts_list:
        if contact.contact_type not in contacts_by_type:
            contacts_by_type[contact.contact_type] = []
        contacts_by_type[contact.contact_type].append(contact)
    
    return render(request, 'sntapp/contacts.html', {
        'page': page,
        'contacts_by_type': contacts_by_type,
    })

def announcements(request):
    announcements_list = News.objects.filter(is_published=True)
    paginator = Paginator(announcements_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'sntapp/announcements.html', {'page_obj': page_obj})


@login_required
def profile(request):
    user_debts_summary = get_user_total_debt(request.user)
    all_debts = Debt.objects.filter(user=request.user).order_by('-period')
    debts_by_period = {}
    for debt in all_debts:
        if debt.period not in debts_by_period:
            debts_by_period[debt.period] = {
                'membership': 0,
                'target': 0,
                'other': 0,
                'total': 0
            }
        
        if debt.fee_type == 'membership':
            debts_by_period[debt.period]['membership'] = debt.amount
        elif debt.fee_type == 'target':
            debts_by_period[debt.period]['target'] = debt.amount
        else:
            debts_by_period[debt.period]['other'] = debt.amount
        
        debts_by_period[debt.period]['total'] += debt.amount
    
    recent_debts = all_debts[:5]
    
    debt_stats = {
        'total_periods': len(debts_by_period),
        'oldest_debt': all_debts.last(),
        'newest_debt': all_debts.first(),
    }
    
    return render(request, 'sntapp/profile.html', {
        'user_debts_summary': user_debts_summary,
        'all_debts': all_debts,
        'debts_by_period': debts_by_period,
        'recent_debts': recent_debts,
        'debt_stats': debt_stats,
    })

@login_required
def edit_profile(request):
    if request.method == 'POST':
        request.user.full_name = request.POST.get('full_name')
        request.user.phone = request.POST.get('phone')
        request.user.email = request.POST.get('email')
        request.user.save()
        messages.success(request, 'Профиль обновлен')
        return redirect('profile')
    return render(request, 'sntapp/edit_profile.html')


@login_required
def news_manage(request):
    if not (request.user.is_staff or request.user.is_moderator):
        messages.error(request, 'У вас нет прав для доступа к этой странице')
        return redirect('home')
    
    news_list = News.objects.all().order_by('-created_at')
    paginator = Paginator(news_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'sntapp/news_manage.html', {'page_obj': page_obj})

@login_required
def news_create(request):
    if not (request.user.is_staff or request.user.is_moderator):
        messages.error(request, 'У вас нет прав для создания новостей')
        return redirect('home')
    
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            news = form.save(commit=False)
            news.author = request.user
            news.save()
            messages.success(request, 'Новость успешно создана')
            return redirect('news_manage')
    else:
        form = NewsForm()
    return render(request, 'sntapp/news_form.html', {'form': form, 'title': 'Создать новость'})

@login_required
def news_edit(request, pk):
    if not (request.user.is_staff or request.user.is_moderator):
        messages.error(request, 'У вас нет прав для редактирования новостей')
        return redirect('home')
    
    news = get_object_or_404(News, pk=pk)
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES, instance=news)
        if form.is_valid():
            form.save()
            messages.success(request, 'Новость обновлена')
            return redirect('news_manage')
    else:
        form = NewsForm(instance=news)
    return render(request, 'sntapp/news_form.html', {'form': form, 'title': 'Редактировать новость'})

@login_required
def news_delete(request, pk):
    if not (request.user.is_staff or request.user.is_moderator):
        messages.error(request, 'У вас нет прав для удаления новостей')
        return redirect('home')
    
    news = get_object_or_404(News, pk=pk)
    if request.method == 'POST':
        news.delete()
        messages.success(request, 'Новость удалена')
        return redirect('news_manage')
    return render(request, 'sntapp/news_confirm_delete.html', {'news': news})

def documents_list(request):
    documents = Document.objects.filter(is_visible=True)
    doc_type = request.GET.get('type', '')
    if doc_type:
        documents = documents.filter(document_type=doc_type)
    
    search = request.GET.get('search', '')
    if search:
        documents = documents.filter(title__icontains=search)
    
    sort = request.GET.get('sort', '-uploaded_at')
    documents = documents.order_by(sort)
    
    paginator = Paginator(documents, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    document_types = Document.DOCUMENT_TYPES
    
    return render(request, 'sntapp/documents.html', {
        'page_obj': page_obj,
        'document_types': document_types,
        'current_type': doc_type,
        'current_search': search,
        'current_sort': sort,
    })

@login_required
def document_upload(request):
    if not (request.user.is_staff or request.user.is_moderator):
        messages.error(request, 'У вас нет прав для загрузки документов')
        return redirect('documents')
    
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.save()
            messages.success(request, f'Документ "{document.title}" успешно загружен')
            return redirect('documents')
    else:
        form = DocumentForm()
    
    return render(request, 'sntapp/document_upload.html', {'form': form})

@login_required
def document_delete(request, pk):
    if not (request.user.is_staff or request.user.is_moderator):
        messages.error(request, 'У вас нет прав для удаления документов')
        return redirect('documents')
    
    document = get_object_or_404(Document, pk=pk)
    
    if request.method == 'POST':
        title = document.title
        document.delete()
        messages.success(request, f'Документ "{title}" удален')
        return redirect('documents')
    
    return render(request, 'sntapp/document_confirm_delete.html', {'document': document})

@login_required
def document_download(request, pk):
    document = get_object_or_404(Document, pk=pk, is_visible=True)
    
    document.downloads_count += 1
    document.save()
    
    response = HttpResponse(document.file, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{document.file.name.split("/")[-1]}"'
    return response

def document_detail(request, pk):
    document = get_object_or_404(Document, pk=pk, is_visible=True)
    return render(request, 'sntapp/document_detail.html', {'document': document})

@login_required
def upload_debts(request):
    if not (request.user.is_staff or request.user.is_moderator):
        messages.error(request, 'У вас нет прав для загрузки данных о долгах')
        return redirect('profile')
    
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            
            result = parse_excel_debts(excel_file, request)
            
            if 'error' in result:
                messages.error(request, result['error'])
            else:
                success_msg = f"Обработано участков: {result.get('total_users', 0)} | "
                success_msg += f"Обновлено записей о долгах: {result.get('updated_debts', 0)} | "
                success_msg += f"Пропущено (не зарегистрированы): {result.get('skipped', 0)} | "
                success_msg += f"Ошибок: {result.get('errors', 0)}"
                messages.success(request, success_msg)
                
                if result.get('error_details'):
                    error_text = "\n".join(result['error_details'][:10]) 
                    messages.warning(request, f"Проблемы:\n{error_text}")
                
                if result.get('processed_lots'):
                    processed = ", ".join(result['processed_lots'][:15])
                    if len(result['processed_lots']) > 15:
                        processed += f" и еще {len(result['processed_lots']) - 15}"
                    messages.info(request, f"Обработаны участки: {processed}")
                
                return redirect('debt_summary')
    else:
        form = ExcelUploadForm()
    
    return render(request, 'sntapp/upload_debts.html', {'form': form})

@login_required
def debt_summary(request):
    if not (request.user.is_staff or request.user.is_moderator):
        messages.error(request, 'У вас нет прав для просмотра этой страницы')
        return redirect('profile')
    
    summary = get_debt_summary()
    debtors = Debt.objects.filter(amount__gt=0).select_related('user').order_by('-amount')
    
    debtors_list = {}
    for debt in debtors:
        if debt.user.id not in debtors_list:
            debtors_list[debt.user.id] = {
                'user': debt.user,
                'membership_debt': 0,
                'target_debt': 0,
                'total': 0
            }
        if debt.fee_type == 'membership':
            debtors_list[debt.user.id]['membership_debt'] = debt.amount
        else:
            debtors_list[debt.user.id]['target_debt'] = debt.amount
        debtors_list[debt.user.id]['total'] += debt.amount
    
    debtors_sorted = sorted(debtors_list.values(), key=lambda x: x['total'], reverse=True)
    
    return render(request, 'sntapp/debt_summary.html', {
        'summary': summary,
        'debtors': debtors_sorted
    })


@login_required
def debt_history(request, user_id=None):
    if not (request.user.is_staff or request.user.is_moderator):
        messages.error(request, 'У вас нет прав для просмотра этой страницы')
        return redirect('profile')
    
    if user_id:
        user = get_object_or_404(User, id=user_id)
        debts = Debt.objects.filter(user=user).order_by('-period')
    else:
        user = request.user
        debts = Debt.objects.filter(user=request.user).order_by('-period')
    
    return render(request, 'sntapp/debt_history.html', {'user': user, 'debts': debts})

from django.core.mail import send_mail
from django.conf import settings

def contacts(request):
    page = StaticPage.objects.filter(page_type='contacts', is_active=True).first()
    if not page:
        page = StaticPage.objects.create(
            page_type='contacts',
            title='Контакты',
            content='<p>Свяжитесь с нами любым удобным способом. Мы всегда рады ответить на ваши вопросы!</p>'
        )
    
    contacts_list = ContactInfo.objects.filter(is_active=True)
    
    contacts_by_type = {}
    for contact in contacts_list:
        if contact.contact_type not in contacts_by_type:
            contacts_by_type[contact.contact_type] = []
        contacts_by_type[contact.contact_type].append(contact)
    
    return render(request, 'sntapp/contacts.html', {
        'page': page,
        'contacts_by_type': contacts_by_type,
    })

def news_detail(request, pk):
    news = get_object_or_404(News, pk=pk, is_published=True)
    return render(request, 'sntapp/news_detail.html', {'news': news})

@login_required
def announcement_create(request):
    if not (request.user.is_staff or request.user.is_moderator):
        messages.error(request, 'У вас нет прав')
        return redirect('home')
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            announcement.save()
            messages.success(request, 'Объявление добавлено!')
            return redirect('home')
    else:
        form = AnnouncementForm()
    
    return render(request, 'sntapp/announcement_form.html', {'form': form})