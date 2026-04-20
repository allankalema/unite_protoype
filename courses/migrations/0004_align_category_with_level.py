from django.db import migrations


def align_category_with_level(apps, schema_editor):
    Course = apps.get_model("courses", "Course")
    for course in Course.objects.all():
        current = (course.category or "").strip().lower()
        if current in {"", "general"}:
            course.category = (course.level or "beginner").strip()
            course.save(update_fields=["category"])


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0003_backfill_course_category"),
    ]

    operations = [
        migrations.RunPython(align_category_with_level, noop_reverse),
    ]

