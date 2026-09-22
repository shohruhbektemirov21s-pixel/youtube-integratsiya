"""Status qiymatlarini normalizatsiya qiladi va DB darajasida qulflaydi.

Muammo: Django `choices` DB cheklovi EMAS — `Model.objects.create(status=...)`
`full_clean()` ni chaqirmaydi. Skriptlar `docker exec ... manage.py shell -c`
orqali to'g'ridan-to'g'ri ORM ga yozgani uchun bazaga katta harfli qiymatlar
tushgan:

    VideoGenerationTask: 'COMPLETED' x7,  'completed' x18
    ScheduledUpload:     'SCHEDULED' x2,  'scheduled' x7

Oqibati real edi: `filter(status='scheduled')` katta harfli 2 ta yozuvni
ko'rmagani uchun ular hech qachon nashr qilinmasdi, lekin daemon buferni
hisoblashda `.lower()` ishlatgani uchun ularni "band" deb sanardi — ya'ni
yangi kontent generatsiyasi ham to'xtab turardi.

Shuningdek: `youtube_video_id` bo'sh, sanasi kelajakda bo'lgan, lekin
'published' deb belgilangan yozuvlar tuzatiladi. Ular hech qachon YouTube'ga
yuklanmagan (upload qatlami soxta ID qaytarardi), shuning uchun ularni
'scheduled' ga qaytaramiz — bu haqiqiy holat.
"""
from django.db import migrations, models

UPLOAD_STATUSES = ['pending_confirmation', 'scheduled', 'processing', 'published', 'failed']
GENERATION_STATUSES = ['queued', 'generating', 'completed', 'failed']


def normalize(apps, schema_editor):
    ScheduledUpload = apps.get_model('youtube', 'ScheduledUpload')
    VideoGenerationTask = apps.get_model('youtube', 'VideoGenerationTask')

    for model, valid, default in (
        (ScheduledUpload, UPLOAD_STATUSES, 'scheduled'),
        (VideoGenerationTask, GENERATION_STATUSES, 'failed'),
    ):
        for row in model.objects.exclude(status__in=valid).only('id', 'status'):
            lowered = (row.status or '').strip().lower()
            row.status = lowered if lowered in valid else default
            row.save(update_fields=['status'])

    # Yuklanmagan, lekin "nashr qilingan" deb belgilangan yozuvlarni tuzatish
    ScheduledUpload.objects.filter(status='published', youtube_video_id='').update(
        status='scheduled', published_at=None
    )


def noop_reverse(apps, schema_editor):
    """Orqaga qaytarish ma'nosiz — buzilgan qiymatlarni tiklamaymiz."""


class Migration(migrations.Migration):

    dependencies = [
        ('youtube', '0004_alter_scheduledupload_status'),
    ]

    operations = [
        migrations.RunPython(normalize, noop_reverse),
        migrations.AddConstraint(
            model_name='scheduledupload',
            constraint=models.CheckConstraint(
                condition=models.Q(status__in=UPLOAD_STATUSES),
                name='scheduledupload_status_valid',
            ),
        ),
        migrations.AddConstraint(
            model_name='videogenerationtask',
            constraint=models.CheckConstraint(
                condition=models.Q(status__in=GENERATION_STATUSES),
                name='videogenerationtask_status_valid',
            ),
        ),
    ]
