import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Professional, WorkingHours
from booking.models import Service, ProfessionalService
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
            'name': 'Alessandra Souza',
            'role': 'Manicure & Nail Designer',
            'bio': 'Especialista em alongamento em gel, blindagem e manicure classica com mais de 5 anos de experiencia em cuidados e estetica das unhas.',
            'photo': 'professionals/alessandra.jpg'
        },
        {
            'user': prof_users['luana'],
            'name': 'Luana Rocha',
            'role': 'Manicure & Spa de Pes',
            'bio': 'Apaixonada por esmaltacao em gel, decoracao artistica (nail art) e tratamentos relaxantes de spa dos pes para um cuidado completo.',
            'photo': 'professionals/luana.jpg'
        },
        {
            'user': prof_users['larissa'],
            'name': 'Larissa Mendes',
            'role': 'Designer de Sobrancelhas',
            'bio': 'Especialista em visagismo facial, design de sobrancelhas personalizado, aplicacao de henna e lash lifting para valorizar o seu olhar.',
            'photo': 'professionals/larissa.jpg'
        }
    ]

    professionals = {}
    for data in professionals_data:
        prof, created = Professional.objects.get_or_create(
            name=data['name'],
            defaults={
                'user': data['user'],
                'role': data['role'],
                'bio': data['bio'],
                'is_active': True
            }
        )
        # Se for nova ou antiga, salvamos para relacionar
        professionals[data['name'].split()[0].lower()] = prof
        if created:
            print(f"[OK] Profissional {data['name']} cadastrada.")
        else:
            print(f"[OK] Profissional {data['name']} ja existia.")

    # 4. Criar Servicos
    services_data = [
        {
            'name': 'Manicure Classica',
            'description': 'Corte, lixamento, remocao de cuticulas e esmaltacao tradicional com acabamento perfeito.',
            'duration_minutes': 45,
            'price': 40.00,
            'profs': ['alessandra', 'luana']
        },
        {
            'name': 'Manicure em Gel (Blindagem)',
            'description': 'Aplicacao de camada de gel para protecao e fortalecimento das unhas naturais, garantindo esmaltacao duradoura (ate 20 dias).',
            'duration_minutes': 60,
            'price': 80.00,
            'profs': ['alessandra', 'luana']
        },
        {
            'name': 'Alongamento de Unhas em Gel',
            'description': 'Alongamento completo das unhas com gel premium e tips ou moldes, proporcionando unhas longas, naturais e resistentes.',
            'duration_minutes': 120,
            'price': 150.00,
            'profs': ['alessandra', 'luana']
        },
        {
            'name': 'Spa dos Pes + Manicure',
            'description': 'Tratamento completo de esfoliacao, hidratacao profunda, massagem relaxante nos pes e servico de manicure classica inclusa.',
            'duration_minutes': 75,
            'price': 90.00,
            'profs': ['alessandra', 'luana']
        },
        {
            'name': 'Design de Sobrancelhas Simples',
            'description': 'Mapeamento facial e remocao de pelos com pinca e linha para um contorno harmonico e limpo das sobrancelhas.',
            'duration_minutes': 30,
            'price': 35.00,
            'profs': ['larissa']
        },
        {
            'name': 'Design de Sobrancelhas com Henna',
            'description': 'Design de sobrancelhas personalizado combinado com preenchimento temporario em henna para realce e cobertura de falhas.',
            'duration_minutes': 45,
            'price': 55.00,
            'profs': ['larissa']
        },
        {
            'name': 'Lash Lifting & Nutricao',
            'description': 'Curvatura e coloracao natural dos cilios superiores combinada com tratamento nutritivo, destacando o olhar por ate 6 semanas.',
            'duration_minutes': 60,
            'price': 110.00,
            'profs': ['larissa']
        }
    ]

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
        if created:
            print(f"[OK] Servico '{data['name']}' cadastrado.")
        else:
            print(f"[OK] Servico '{data['name']}' ja existia.")

        # Relacionar profissionais ao servico
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
