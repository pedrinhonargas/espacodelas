from django.shortcuts import render
from accounts.models import Professional
from booking.models import Service

def home(request):
    services = Service.objects.filter(is_active=True)
    professionals = Professional.objects.filter(is_active=True)

    # Serviços da Larissa (sobrancelha & cílios)
    brow_service_names = [
        'Brow Lamination', 'Design de Sobrancelha', 'Design + Henna', 'Lash Lifting',
    ]
    nail_services = services.exclude(name__in=brow_service_names)
    brow_services = services.filter(name__in=brow_service_names)

    return render(request, 'core/home.html', {
        'services': services,
        'nail_services': nail_services,
        'brow_services': brow_services,
        'professionals': professionals
    })


def sitemap_view(request):
    from django.http import HttpResponse
    from django.urls import reverse
    
    host = request.build_absolute_uri('/')[:-1]
    
    pages = [
        {'loc': host + reverse('core:home'), 'changefreq': 'daily', 'priority': '1.0'},
        {'loc': host + reverse('booking:start'), 'changefreq': 'weekly', 'priority': '0.8'},
    ]
    
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for page in pages:
        xml_content += '  <url>\n'
        xml_content += f"    <loc>{page['loc']}</loc>\n"
        xml_content += f"    <changefreq>{page['changefreq']}</changefreq>\n"
        xml_content += f"    <priority>{page['priority']}</priority>\n"
        xml_content += '  </url>\n'
    xml_content += '</urlset>'
    
    return HttpResponse(xml_content, content_type="application/xml")


def robots_view(request):
    from django.http import HttpResponse
    from django.urls import reverse
    
    sitemap_url = request.build_absolute_uri(reverse('core:sitemap'))
    content = f"""User-agent: *
Disallow: /studio/
Disallow: /conta/
Disallow: /agendar/data-hora/
Disallow: /agendar/dados/
Disallow: /agendar/confirmar/
Disallow: /agendar/sucesso/
Disallow: /agendar/cancelar/
Disallow: /agendar/horarios/

Sitemap: {sitemap_url}
"""
    return HttpResponse(content, content_type="text/plain")

