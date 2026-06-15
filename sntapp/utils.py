import pandas as pd
from django.contrib import messages
from decimal import Decimal
from datetime import datetime
from .models import User, Debt
from django.db.models import Sum
from django.db.models import Sum, Count, Q

def parse_excel_debts(file, request):
    try:
        df = pd.read_excel(file, engine='openpyxl', header=2)
        df.columns = [
            'lot_number', 'target_2025', 'membership_1_2026', 'membership_2_2025',
            'membership_1_2025', 'membership_2_2024', 'membership_1_2024',
            'membership_2_2023', 'membership_1_2023', 'membership_2022',
            'target_2022_2024', 'target_2020_2021', 'target_2018_2019',
            'ppm', 'vzu'
        ]
        
        df = df.dropna(subset=['lot_number'])
        df = df[df['lot_number'].astype(str).str.strip() != '']
        df = df[~df['lot_number'].astype(str).str.contains('СРОК|срок', na=False)]
        
        stats = {
            'total_users': 0,
            'updated_debts': 0,
            'errors': 0,
            'skipped': 0,
            'error_details': [],
            'processed_lots': []
        }
        
        for index, row in df.iterrows():
            try:
                lot_number_raw = str(row['lot_number']).strip()
                if pd.isna(lot_number_raw) or lot_number_raw == 'nan':
                    stats['skipped'] += 1
                    continue
                
                stats['total_users'] += 1
                
                lot_numbers_to_check = [lot_number_raw]
                if '/' in lot_number_raw:
                    parts = lot_number_raw.split('/')
                    lot_numbers_to_check.extend(parts)
                
                user = None
                for lot in lot_numbers_to_check:
                    try:
                        user = User.objects.get(lot_number=lot.strip())
                        break
                    except User.DoesNotExist:
                        continue
                
                if not user:
                    stats['skipped'] += 1
                    stats['error_details'].append(f"Участок {lot_number_raw} не зарегистрирован на сайте")
                    continue
                
                stats['processed_lots'].append(lot_number_raw)
                
                debts_to_update = []
                
                # 1. Целевой взнос 2025
                target_2025 = safe_decimal(row['target_2025'])
                if target_2025 > 0:
                    debts_to_update.append({
                        'fee_type': 'target',
                        'period': 'Целевой взнос 2025',
                        'amount': target_2025
                    })
                
                # 2. Членские взносы 1 полугодие 2026
                membership_1_2026 = safe_decimal(row['membership_1_2026'])
                if membership_1_2026 > 0:
                    debts_to_update.append({
                        'fee_type': 'membership',
                        'period': 'Членские взносы 1 полугодие 2026',
                        'amount': membership_1_2026
                    })
                
                # 3. Членские взносы 2 полугодие 2025
                membership_2_2025 = safe_decimal(row['membership_2_2025'])
                if membership_2_2025 > 0:
                    debts_to_update.append({
                        'fee_type': 'membership',
                        'period': 'Членские взносы 2 полугодие 2025',
                        'amount': membership_2_2025
                    })
                
                # 4. Членские взносы 1 полугодие 2025
                membership_1_2025 = safe_decimal(row['membership_1_2025'])
                if membership_1_2025 > 0:
                    debts_to_update.append({
                        'fee_type': 'membership',
                        'period': 'Членские взносы 1 полугодие 2025',
                        'amount': membership_1_2025
                    })
                
                # 5. Членские взносы 2 полугодие 2024
                membership_2_2024 = safe_decimal(row['membership_2_2024'])
                if membership_2_2024 > 0:
                    debts_to_update.append({
                        'fee_type': 'membership',
                        'period': 'Членские взносы 2 полугодие 2024',
                        'amount': membership_2_2024
                    })
                
                # 6. Членские взносы 1 полугодие 2024
                membership_1_2024 = safe_decimal(row['membership_1_2024'])
                if membership_1_2024 > 0:
                    debts_to_update.append({
                        'fee_type': 'membership',
                        'period': 'Членские взносы 1 полугодие 2024',
                        'amount': membership_1_2024
                    })
                
                # 7. Членские взносы 2 полугодие 2023
                membership_2_2023 = safe_decimal(row['membership_2_2023'])
                if membership_2_2023 > 0:
                    debts_to_update.append({
                        'fee_type': 'membership',
                        'period': 'Членские взносы 2 полугодие 2023',
                        'amount': membership_2_2023
                    })
                
                # 8. Членские взносы 1 полугодие 2023
                membership_1_2023 = safe_decimal(row['membership_1_2023'])
                if membership_1_2023 > 0:
                    debts_to_update.append({
                        'fee_type': 'membership',
                        'period': 'Членские взносы 1 полугодие 2023',
                        'amount': membership_1_2023
                    })
                
                # 9. Членские взносы 2022
                membership_2022 = safe_decimal(row['membership_2022'])
                if membership_2022 > 0:
                    debts_to_update.append({
                        'fee_type': 'membership',
                        'period': 'Членские взносы 2022',
                        'amount': membership_2022
                    })
                
                # 10. Целевой взнос 2022-2024
                target_2022_2024 = safe_decimal(row['target_2022_2024'])
                if target_2022_2024 > 0:
                    debts_to_update.append({
                        'fee_type': 'target',
                        'period': 'Целевой взнос 2022-2024',
                        'amount': target_2022_2024
                    })
                
                # 11. Целевой взнос 2020-2021
                target_2020_2021 = safe_decimal(row['target_2020_2021'])
                if target_2020_2021 > 0:
                    debts_to_update.append({
                        'fee_type': 'target',
                        'period': 'Целевой взнос 2020-2021',
                        'amount': target_2020_2021
                    })
                
                # 12. Целевой взнос 2018-2019
                target_2018_2019 = safe_decimal(row['target_2018_2019'])
                if target_2018_2019 > 0:
                    debts_to_update.append({
                        'fee_type': 'target',
                        'period': 'Целевой взнос 2018-2019',
                        'amount': target_2018_2019
                    })
                
                # 13. ППМ 
                ppm = safe_decimal(row['ppm'])
                if ppm > 0:
                    debts_to_update.append({
                        'fee_type': 'other',
                        'period': 'ППМ ',
                        'amount': ppm
                    })
                
                # 14. ВЗУ
                vzu = safe_decimal(row['vzu'])
                if vzu > 0:
                    debts_to_update.append({
                        'fee_type': 'other',
                        'period': 'ВЗУ',
                        'amount': vzu
                    })
                
                for debt_info in debts_to_update:
                    obj, created = Debt.objects.update_or_create(
                        user=user,
                        fee_type=debt_info['fee_type'],
                        period=debt_info['period'],
                        defaults={'amount': debt_info['amount']}
                    )
                    stats['updated_debts'] += 1
                    
            except Exception as e:
                stats['errors'] += 1
                stats['error_details'].append(f"Строка {index + 3}: Участок {row['lot_number']} - {str(e)}")
        
        return stats
        
    except Exception as e:
        return {'error': f"Ошибка чтения файла: {str(e)}"}

def safe_decimal(value):
    if pd.isna(value) or value == '' or value is None:
        return Decimal('0')
    try:
        str_value = str(value).replace(',', '.')
        return Decimal(str_value)
    except:
        return Decimal('0')

def get_debt_summary():
    total_debt = Debt.objects.filter(amount__gt=0).aggregate(Sum('amount'))['amount__sum'] or 0
    total_debtors = Debt.objects.filter(amount__gt=0).values('user').distinct().count()
    
    membership_debt = Debt.objects.filter(fee_type='membership', amount__gt=0).aggregate(Sum('amount'))['amount__sum'] or 0
    target_debt = Debt.objects.filter(fee_type='target', amount__gt=0).aggregate(Sum('amount'))['amount__sum'] or 0
    other_debt = Debt.objects.filter(fee_type='other', amount__gt=0).aggregate(Sum('amount'))['amount__sum'] or 0
    
    debts_by_period = Debt.objects.filter(amount__gt=0).values('period').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-period')
    
    summary = {
        'total_debt': total_debt,
        'total_debtors': total_debtors,
        'membership_debt': membership_debt,
        'target_debt': target_debt,
        'other_debt': other_debt,
        'debts_by_period': debts_by_period,
    }
    return summary


def get_user_total_debt(user):
    
    total = Debt.objects.filter(user=user, amount__gt=0).aggregate(Sum('amount'))['amount__sum'] or 0
    membership = Debt.objects.filter(user=user, fee_type='membership', amount__gt=0).aggregate(Sum('amount'))['amount__sum'] or 0
    target = Debt.objects.filter(user=user, fee_type='target', amount__gt=0).aggregate(Sum('amount'))['amount__sum'] or 0
    other = Debt.objects.filter(user=user, fee_type='other', amount__gt=0).aggregate(Sum('amount'))['amount__sum'] or 0
    
    return {
        'total': total,
        'membership': membership,
        'target': target,
        'other': other
    }