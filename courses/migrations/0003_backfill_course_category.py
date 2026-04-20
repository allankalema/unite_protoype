from django.db import migrations


def backfill_course_category(apps, schema_editor):
    Course = apps.get_model("courses", "Course")
    Course.objects.filter(category="").update(category="General")


def noop_reverse(apps, schema_editor):
    # Keep existing data as-is on reverse migration.
    return


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0002_course_category_course_created_by_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_course_category, noop_reverse),
    ]

