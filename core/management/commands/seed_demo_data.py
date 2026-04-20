from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import Profile
from courses.models import Course, Lesson, Module, Question, Quiz


class Command(BaseCommand):
    help = "Seed demo data for UNITE eLearn MVP"

    def handle(self, *args, **options):
        staff_user, _ = User.objects.get_or_create(username="staff_demo", defaults={"email": "staff@unite.demo"})
        staff_user.set_password("DemoPass123!")
        staff_user.is_staff = True
        staff_user.save()
        staff_profile = staff_user.profile
        staff_profile.full_name = "UNITE Staff Admin"
        staff_profile.email = "staff@unite.demo"
        staff_profile.role = Profile.ROLE_STAFF
        staff_profile.institution_name = "UNITE"
        staff_profile.save()

        teacher_payload = [
            ("teacher_a", "teacher.a@unite.demo", "Amina Nansubuga"),
            ("teacher_b", "teacher.b@unite.demo", "Peter Okello"),
        ]
        for username, email, name in teacher_payload:
            teacher, _ = User.objects.get_or_create(username=username, defaults={"email": email})
            teacher.set_password("DemoPass123!")
            teacher.save()
            profile = teacher.profile
            profile.full_name = name
            profile.email = email
            profile.role = Profile.ROLE_TEACHER
            profile.institution_name = "UNITE Partner School"
            profile.district = "Kampala"
            profile.save()

        courses_data = [
            {
                "title": "Competency-Based Curriculum Foundations",
                "short_description": "Understand CBC principles and practical classroom application.",
                "description": "This course introduces CBC foundations, learner outcomes, and practical planning.",
            },
            {
                "title": "Classroom Assessment Methods",
                "short_description": "Use formative and summative assessment methods effectively.",
                "description": "Learn assessment design, rubrics, feedback cycles, and progress tracking.",
            },
            {
                "title": "Inclusive Teaching Strategies",
                "short_description": "Build inclusive and equitable classrooms for all learners.",
                "description": "Cover UDL principles, differentiated instruction, and learner support strategies.",
            },
        ]

        for course_entry in courses_data:
            course, _ = Course.objects.get_or_create(
                title=course_entry["title"],
                defaults={
                    "short_description": course_entry["short_description"],
                    "description": course_entry["description"],
                    "is_published": True,
                    "passing_score": 60,
                    "estimated_duration_hours": 6,
                },
            )

            for module_index in range(1, 3):
                module, _ = Module.objects.get_or_create(
                    course=course,
                    order=module_index,
                    defaults={
                        "title": f"Module {module_index}: Practice Focus",
                        "description": f"Practical teaching strategies for module {module_index}.",
                    },
                )

                for lesson_index in range(1, 3):
                    Lesson.objects.get_or_create(
                        module=module,
                        order=lesson_index,
                        defaults={
                            "title": f"Lesson {module_index}.{lesson_index}",
                            "summary": "Key concepts and classroom examples.",
                            "content": (
                                "In this lesson, teachers explore practical approaches, discuss examples from Ugandan "
                                "classrooms, and identify immediate actions for learner-centered instruction."
                            ),
                        },
                    )

            quiz, _ = Quiz.objects.get_or_create(
                course=course,
                defaults={
                    "title": f"{course.title} - Endline Quiz",
                    "description": "Answer all questions to evaluate understanding.",
                    "is_active": True,
                },
            )

            if quiz.questions.count() < 4:
                Question.objects.get_or_create(
                    quiz=quiz,
                    text="Which approach best supports competency development?",
                    defaults={
                        "option_a": "Lecture-only instruction",
                        "option_b": "Learner-centered tasks and reflection",
                        "option_c": "Memorization without practice",
                        "option_d": "Skipping assessment",
                        "correct_option": "B",
                    },
                )
                Question.objects.get_or_create(
                    quiz=quiz,
                    text="Formative assessment is mainly used to:",
                    defaults={
                        "option_a": "Rank schools",
                        "option_b": "Punish learners",
                        "option_c": "Improve ongoing learning",
                        "option_d": "Replace instruction",
                        "correct_option": "C",
                    },
                )
                Question.objects.get_or_create(
                    quiz=quiz,
                    text="Inclusive teaching means:",
                    defaults={
                        "option_a": "One method for all learners",
                        "option_b": "Adapting teaching to diverse needs",
                        "option_c": "Ignoring learner barriers",
                        "option_d": "Teaching only high performers",
                        "correct_option": "B",
                    },
                )
                Question.objects.get_or_create(
                    quiz=quiz,
                    text="A strong lesson objective should be:",
                    defaults={
                        "option_a": "Clear and measurable",
                        "option_b": "Vague and broad",
                        "option_c": "Unrelated to outcomes",
                        "option_d": "Optional for planning",
                        "correct_option": "A",
                    },
                )
                Question.objects.get_or_create(
                    quiz=quiz,
                    text="Feedback is most effective when it is:",
                    defaults={
                        "option_a": "Delayed for months",
                        "option_b": "Specific and timely",
                        "option_c": "Only negative",
                        "option_d": "Given once per term",
                        "correct_option": "B",
                    },
                )

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
        self.stdout.write("\nCredentials:")
        self.stdout.write("Staff: staff_demo / DemoPass123!")
        self.stdout.write("Teacher: teacher_a / DemoPass123!")
        self.stdout.write("Teacher: teacher_b / DemoPass123!")
