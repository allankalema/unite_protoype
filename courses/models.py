from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify


class Course(models.Model):
    LEVEL_BEGINNER = "beginner"
    LEVEL_INTERMEDIATE = "intermediate"
    LEVEL_ADVANCED = "advanced"
    LEVEL_CHOICES = [
        (LEVEL_BEGINNER, "Beginner"),
        (LEVEL_INTERMEDIATE, "Intermediate"),
        (LEVEL_ADVANCED, "Advanced"),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    category = models.CharField(max_length=120, blank=True, db_index=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default=LEVEL_BEGINNER)
    short_description = models.CharField(max_length=300)
    description = models.TextField()
    learning_objectives = models.TextField(blank=True)
    prerequisites = models.TextField(blank=True)
    target_audience = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_courses",
    )
    cover_image = models.URLField(blank=True)
    is_published = models.BooleanField(default=True)
    passing_score = models.PositiveIntegerField(default=60)
    estimated_duration_hours = models.PositiveIntegerField(default=6)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["course", "order", "id"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    TYPE_VIDEO = "video"
    TYPE_READING = "reading"
    TYPE_ASSIGNMENT = "assignment"
    TYPE_CHOICES = [
        (TYPE_VIDEO, "Video"),
        (TYPE_READING, "Reading"),
        (TYPE_ASSIGNMENT, "Assignment"),
    ]

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)
    lesson_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_READING)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    content = models.TextField()
    summary = models.TextField(blank=True)
    ai_summary = models.TextField(blank=True)
    ai_keywords = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    downloadable_material_url = models.URLField(blank=True)

    class Meta:
        ordering = ["module", "order", "id"]

    def __str__(self):
        return f"{self.module.title} - {self.title}"


class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "course")
        ordering = ["-enrolled_at"]

    def __str__(self):
        return f"{self.user.username} enrolled in {self.course.title}"


class LessonProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress_entries")
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "lesson")

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title} ({'Done' if self.is_completed else 'In Progress'})"


class Quiz(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="quizzes")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    max_attempts = models.PositiveIntegerField(default=3)

    class Meta:
        ordering = ["course", "id"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Question(models.Model):
    OPTION_CHOICES = [
        ("A", "Option A"),
        ("B", "Option B"),
        ("C", "Option C"),
        ("D", "Option D"),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES)
    explanation = models.TextField(blank=True)

    def __str__(self):
        return f"Question {self.id} - {self.quiz.title}"


class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quiz_attempts")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    score = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    percentage = models.FloatField(default=0)
    passed = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-attempted_at"]

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} ({self.percentage:.1f}%)"


class LessonResource(models.Model):
    TYPE_PDF = "pdf"
    TYPE_DOC = "doc"
    TYPE_LINK = "link"
    TYPE_VIDEO = "video"
    TYPE_CHOICES = [
        (TYPE_PDF, "PDF"),
        (TYPE_DOC, "Document"),
        (TYPE_LINK, "Link"),
        (TYPE_VIDEO, "Video"),
    ]

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="resources")
    title = models.CharField(max_length=255)
    file_url = models.URLField()
    resource_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_LINK)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.lesson.title} - {self.title}"
