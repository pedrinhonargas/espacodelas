import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Professional, WorkingHours
from booking.models import Service, ProfessionalService, Appointment
import datetime

def populate():
    print("Iniciando a populacao do banco de dados...")

    # 1. Criar Superusuario se nao existir
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@espacodelas.com.br', 'admin123')
        print("[OK] Superusuario 'admin' criado (Senha: admin123)")
    else:
        print("[OK] Superusuario 'admin' ja existe")

    # 2. Criar Usuarios para as profissionais (para futuro painel)
    prof_users = {}
    for name in ['alessandra', 'luana', 'larissa']:
        username = name
        email = f"{name}@espacodelas.com.br"
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(username, email, 'senha123')
            prof_users[name] = user
            print(f"[OK] Usuario para {name} criado (Senha: senha123)")
        else:
            prof_users[name] = User.objects.get(username=username)

    # 3. Criar Profissionais
    professionals_data = [
        {
            'user': prof_users['alessandra'],
            'name': 'Alessandra Santos',
            'phone': '41988477213',
            'role': 'Manicure & Nail Designer',
            'bio': 'Especialista em alongamento em gel, blindagem e manicure classica com mais de 5 anos de experiencia em cuidados e estetica das unhas.',
            'photo': 'professionals/alessandra.jpg'
        },
        {
            'user': prof_users['luana'],
            'name': 'Luana Santos',
            'phone': '41995236201',
            'role': 'Manicure & Spa de Pes',
            'bio': 'Apaixonada por esmaltacao em gel, decoracao artistica (nail art) e tratamentos relaxantes de spa dos pes para um cuidado completo.',
            'photo': 'professionals/luana.jpg'
        },
        {
            'user': prof_users['larissa'],
            'name': 'Larissa Santos',
            'phone': '41985265463',
            'role': 'Designer de Sobrancelhas',
            'bio': 'Especialista em visagismo facial, design de sobrancelhas personalizado, aplicacao de henna e lash lifting para valorizar o seu olhar.',
            'photo': 'professionals/larissa.jpg'
        }
    ]

    professionals = {}
    for data in professionals_data:
        prof, created = Professional.objects.get_or_create(
            user=data['user'],
            defaults={
                'name': data['name'],
                'phone': data['phone'],
                'role': data['role'],
                'bio': data['bio'],
                'photo': data['photo'],
                'is_active': True
            }
        )
        if not created:
            prof.name = data['name']
            prof.phone = data['phone']
            prof.role = data['role']
            prof.bio = data['bio']
            prof.photo = data['photo']
            prof.save()
            
        # Se for nova ou antiga, salvamos para relacionar
        professionals[data['user'].username] = prof
        if created:
            print(f"[OK] Profissional {data['name']} cadastrada.")
        else:
            print(f"[OK] Profissional {data['name']} ja existia e foi atualizada.")

    # 4. Criar Servicos
    services_data = [
        # Unhas (Mãos e Pés)
        {
            'name': 'Esmaltação em Gel (Mãos)',
            'description': 'Esmaltação em Gel lisa (uma cor só) nas Mãos.',
            'duration_minutes': 60,
            'price': 80.00,
            'profs': ['alessandra', 'luana']
        },
        {
            'name': 'Esmaltação em Gel (Pés)',
            'description': 'Esmaltação em Gel lisa (uma cor só) nos pés.',
            'duration_minutes': 60,
            'price': 80.00,
            'profs': ['alessandra', 'luana']
        },
        {
            'name': 'Francesinha / Sorriso',
            'description': 'Francesinha/Sorriso em todas as unhas.',
            'duration_minutes': 30,
            'price': 20.00,
            'profs': ['alessandra', 'luana']
        },
        {
            'name': 'Decoração Simples',
            'description': 'Decoração simples em todas as unhas.',
            'duration_minutes': 30,
            'price': 25.00,
            'profs': ['alessandra', 'luana']
        },
        {
            'name': 'Decorações Elaboradas',
            'description': 'Decorações mais elaboradas.',
            'duration_minutes': 45,
            'price': 35.00,
            'profs': ['alessandra', 'luana']
        },
        {
            'name': 'Aplicação Pó Cromado',
            'description': 'Aplicação de Pó Cromado.',
            'duration_minutes': 20,
            'price': 10.00,
            'profs': ['alessandra', 'luana']
        },
        {
            'name': 'Banho de Gel',
            'description': 'Banho de Gel.',
            'duration_minutes': 90,
            'price': 130.00,
            'profs': ['alessandra', 'luana']
        },
        {
            'name': 'Manutenção Banho de Gel',
            'description': 'Manutenção Banho de Gel.',
            'duration_minutes': 75,
            'price': 100.00,
            'profs': ['alessandra', 'luana']
        },
        {
            'name': 'Alongamento Molde F1',
            'description': 'Alongamento molde F1.',
            'duration_minutes': 120,
            'price': 180.00,
            'profs': ['alessandra', 'luana']
        },
        {
            'name': 'Manutenção de Alongamento',
            'description': 'Manutenção de Alongamento. Manutenções devem ser feitas até 30 dias no máximo, após isso aplicação nova.',
            'duration_minutes': 90,
            'price': 150.00,
            'profs': ['alessandra', 'luana']
        },
        {
            'name': 'Remoção de Alongamento',
            'description': 'Remoção de Alongamento.',
            'duration_minutes': 45,
            'price': 50.00,
            'profs': ['alessandra', 'luana']
        },
        {
            'name': 'Remoção de Esmalte em Gel',
            'description': 'Remoção de Esmalte em Gel.',
            'duration_minutes': 30,
            'price': 25.00,
            'profs': ['alessandra', 'luana']
        },
        {
            'name': 'Reconstrução de Unha Quebrada',
            'description': 'Reconstrução de unha quebrada.',
            'duration_minutes': 15,
            'price': 10.00,
            'profs': ['alessandra', 'luana']
        },
        # Sobrancelha & Cílios
        {
            'name': 'Brow Lamination',
            'description': 'Brow Lamination.',
            'duration_minutes': 60,
            'price': 70.00,
            'profs': ['larissa']
        },
        {
            'name': 'Design de Sobrancelha',
            'description': 'Design de Sobrancelha.',
            'duration_minutes': 30,
            'price': 25.00,
            'profs': ['larissa']
        },
        {
            'name': 'Design + Henna',
            'description': 'Design + Henna.',
            'duration_minutes': 45,
            'price': 35.00,
            'profs': ['larissa']
        },
        {
            'name': 'Lash Lifting',
            'description': 'Lash lifting.',
            'duration_minutes': 60,
            'price': 70.00,
            'profs': ['larissa']
        }
    ]

    # Mapeamento para migrar agendamentos antigos para os novos nomes de forma limpa
    migration_map = {
        'Alongamento de Unhas em Gel': 'Alongamento Molde F1',
        'Lash Lifting & Nutricao': 'Lash Lifting',
        'Design de Sobrancelhas Simples': 'Design de Sobrancelha',
        'Design de Sobrancelhas com Henna': 'Design + Henna',
        'Manicure em Gel (Blindagem)': 'Esmaltação em Gel (Mãos)',
    }

    # Criar novos serviços que precisam existir para a migração antes do loop geral
    for old_name, new_name in migration_map.items():
        if Service.objects.filter(name=old_name).exists():
            old_service = Service.objects.get(name=old_name)
            new_service_data = next((item for item in services_data if item['name'] == new_name), None)
            if new_service_data:
                new_service, _ = Service.objects.get_or_create(
                    name=new_service_data['name'],
                    defaults={
                        'description': new_service_data['description'],
                        'duration_minutes': new_service_data['duration_minutes'],
                        'price': new_service_data['price'],
                        'is_active': True
                    }
                )
                # Atualizar os agendamentos antigos para apontar para o novo serviço correspondente
                Appointment.objects.filter(service=old_service).update(service=new_service)
                print(f"[OK] Migrados agendamentos de '{old_name}' para '{new_name}'")

    # Agora podemos remover com segurança quaisquer serviços antigos que não fazem parte do novo menu
    new_names = [s['name'] for s in services_data]
    deleted_count, _ = Service.objects.exclude(name__in=new_names).delete()
    if deleted_count > 0:
        print(f"[OK] Removidos {deleted_count} serviços antigos obsoletos.")

    for data in services_data:
        service, created = Service.objects.get_or_create(
            name=data['name'],
            defaults={
                'description': data['description'],
                'duration_minutes': data['duration_minutes'],
                'price': data['price'],
                'is_active': True
            }
        )
        if not created:
            # Se já existia (ou foi criado na pré-migração), atualizamos os valores e descrição
            service.description = data['description']
            service.duration_minutes = data['duration_minutes']
            service.price = data['price']
            service.save()
            print(f"[OK] Servico '{data['name']}' atualizado com novos valores.")
        else:
            print(f"[OK] Servico '{data['name']}' cadastrado.")

        # Relacionar profissionais ao serviço (e limpar relações antigas deste serviço para garantir exatidão)
        ProfessionalService.objects.filter(service=service).delete()
        for prof_key in data['profs']:
            prof = professionals[prof_key]
            ProfessionalService.objects.get_or_create(
                professional=prof,
                service=service
            )

    # 5. Criar Grade de Horarios de Trabalho (Monday to Saturday)
    # Seg-Sex: 09:00 - 19:00
    # Sab: 09:00 - 17:00
    print("Configurando grades de horarios de trabalho...")
    start_weekday = datetime.time(9, 0)
    end_weekday = datetime.time(19, 0)
    start_sat = datetime.time(9, 0)
    end_sat = datetime.time(17, 0)

    for prof_name, prof in professionals.items():
        # Segunda a Sexta (weekday 0 a 4)
        for day in range(5):
            WorkingHours.objects.get_or_create(
                professional=prof,
                weekday=day,
                defaults={
                    'start_time': start_weekday,
                    'end_time': end_weekday,
                    'is_active': True
                }
            )
        # Sabado (weekday 5)
        WorkingHours.objects.get_or_create(
            professional=prof,
            weekday=5,
            defaults={
                'start_time': start_sat,
                'end_time': end_sat,
                'is_active': True
            }
        )
        print(f"  [OK] Grade semanal de {prof.name} configurada.")

    print("\nBanco de dados populado com sucesso!")

if __name__ == '__main__':
    populate()
