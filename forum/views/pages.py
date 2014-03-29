from django.shortcuts import render


def calendar(request):
    return render(request, 'pages/calendar.html', {
        'tab': 'calendar'
    })