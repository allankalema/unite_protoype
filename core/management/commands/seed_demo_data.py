from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import Profile
from certificates.services import get_or_create_certificate_if_eligible
from courses.models import Course, Enrollment, Lesson, LessonProgress, LessonResource, Module, Question, Quiz, QuizAttempt


class Command(BaseCommand):
    help = "Seed presentation-grade data for UNITE eLearn"

    def _upsert_user(self, payload, role, default_password):
        user, _ = User.objects.get_or_create(
            username=payload["username"],
            defaults={"email": payload["email"]},
        )
        user.email = payload["email"]
        user.is_staff = payload.get("is_staff", False)
        user.is_superuser = payload.get("is_superuser", False)
        user.set_password(payload.get("password", default_password))
        user.save()

        profile = user.profile
        profile.full_name = payload["full_name"]
        profile.email = payload["email"]
        profile.institution_name = payload.get("institution_name", "")
        profile.district = payload.get("district", "")
        profile.phone_number = payload.get("phone_number", "")
        profile.role = role
        profile.save()

        return user

    def _build_course(self, owner, payload):
        course, _ = Course.objects.update_or_create(
            slug=payload["slug"],
            defaults={
                "title": payload["title"],
                "category": payload["category"],
                "level": payload["level"],
                "short_description": payload["short_description"],
                "description": payload["description"],
                "learning_objectives": payload["learning_objectives"],
                "prerequisites": payload["prerequisites"],
                "target_audience": payload["target_audience"],
                "created_by": owner,
                "cover_image": payload["cover_image"],
                "is_published": True,
                "passing_score": payload["passing_score"],
                "estimated_duration_hours": payload["estimated_duration_hours"],
            },
        )

        course.modules.all().delete()
        course.quizzes.all().delete()

        for module_order, module_payload in enumerate(payload["modules"], start=1):
            module = Module.objects.create(
                course=course,
                title=module_payload["title"],
                order=module_order,
                description=module_payload["description"],
            )
            for lesson_order, lesson_payload in enumerate(module_payload["lessons"], start=1):
                lesson = Lesson.objects.create(
                    module=module,
                    title=lesson_payload["title"],
                    order=lesson_order,
                    lesson_type=lesson_payload["lesson_type"],
                    duration_minutes=lesson_payload["duration_minutes"],
                    content=lesson_payload["content"],
                    summary=lesson_payload["summary"],
                    ai_summary="",
                    ai_keywords="",
                    video_url=lesson_payload.get("video_url", ""),
                    downloadable_material_url=lesson_payload.get("downloadable_material_url", ""),
                )

                for resource_payload in lesson_payload.get("resources", []):
                    LessonResource.objects.create(
                        lesson=lesson,
                        title=resource_payload["title"],
                        file_url=resource_payload["file_url"],
                        resource_type=resource_payload["resource_type"],
                    )

        quiz = Quiz.objects.create(
            course=course,
            title=payload["quiz"]["title"],
            description=payload["quiz"]["description"],
            is_active=True,
            max_attempts=3,
        )

        for question_payload in payload["quiz"]["questions"]:
            Question.objects.create(
                quiz=quiz,
                text=question_payload["text"],
                option_a=question_payload["option_a"],
                option_b=question_payload["option_b"],
                option_c=question_payload["option_c"],
                option_d=question_payload["option_d"],
                correct_option=question_payload["correct_option"],
                explanation=question_payload["explanation"],
            )

        return course

    def _seed_learning_activity(self, teacher_users, courses):
        for index, teacher in enumerate(teacher_users):
            for course in courses[:2]:
                Enrollment.objects.get_or_create(user=teacher, course=course)

            first_course = courses[0]
            first_course_lessons = list(Lesson.objects.filter(module__course=first_course).order_by("id"))
            for lesson in first_course_lessons:
                LessonProgress.objects.update_or_create(
                    user=teacher,
                    lesson=lesson,
                    defaults={"is_completed": True},
                )

            first_course_quiz = first_course.quizzes.first()
            if first_course_quiz:
                score = 80 + (index * 5)
                total = first_course_quiz.questions.count()
                QuizAttempt.objects.create(
                    user=teacher,
                    quiz=first_course_quiz,
                    score=max(round((score / 100) * total), 1),
                    total_questions=total,
                    percentage=float(score),
                    passed=True,
                )
                get_or_create_certificate_if_eligible(teacher, first_course)

            second_course = courses[1]
            second_lessons = list(Lesson.objects.filter(module__course=second_course).order_by("id"))
            partial_count = min(2 + index, len(second_lessons))
            for lesson in second_lessons[:partial_count]:
                LessonProgress.objects.update_or_create(
                    user=teacher,
                    lesson=lesson,
                    defaults={"is_completed": True},
                )

    def handle(self, *args, **options):
        admin_payload = [
            {
                "username": "unite_admin",
                "full_name": "Grace Nankya",
                "email": "grace.nankya@unite.demo",
                "institution_name": "UNITE Secretariat",
                "district": "Kampala",
                "phone_number": "+256700100101",
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "username": "content_manager",
                "full_name": "Moses Ochan",
                "email": "moses.ochan@unite.demo",
                "institution_name": "UNITE Content Unit",
                "district": "Gulu",
                "phone_number": "+256700100102",
                "is_staff": True,
            },
        ]

        teacher_payload = [
            {
                "username": "teacher_nansubuga",
                "full_name": "Amina Nansubuga",
                "email": "amina.nansubuga@school.demo",
                "institution_name": "Makerere College School",
                "district": "Kampala",
                "phone_number": "+256700200101",
            },
            {
                "username": "teacher_okello",
                "full_name": "Peter Okello",
                "email": "peter.okello@school.demo",
                "institution_name": "Gulu High School",
                "district": "Gulu",
                "phone_number": "+256700200102",
            },
            {
                "username": "teacher_namuli",
                "full_name": "Sarah Namuli",
                "email": "sarah.namuli@school.demo",
                "institution_name": "Mbale Secondary School",
                "district": "Mbale",
                "phone_number": "+256700200103",
            },
            {
                "username": "teacher_kato",
                "full_name": "Ronald Kato",
                "email": "ronald.kato@school.demo",
                "institution_name": "Mbarara High School",
                "district": "Mbarara",
                "phone_number": "+256700200104",
            },
        ]

        courses_payload = [
            {
                "slug": "cbc-foundations-practice",
                "title": "Competency-Based Curriculum Foundations and Practice",
                "category": "Curriculum & Instruction",
                "level": Course.LEVEL_BEGINNER,
                "short_description": "Build practical mastery of CBC planning, teaching, and reflection cycles.",
                "description": (
                    "This course supports teachers to move from content coverage to competency growth. "
                    "It focuses on planning with outcomes, designing active lessons, and reflecting with evidence."
                ),
                "learning_objectives": (
                    "- Explain the shift from knowledge transmission to competency development.\n"
                    "- Write lesson outcomes linked to learner competencies.\n"
                    "- Design learner-centered tasks suitable for mixed-ability classrooms.\n"
                    "- Use reflection notes and learner work to improve instruction."
                ),
                "prerequisites": "Basic lesson planning experience and active classroom teaching role.",
                "target_audience": "Primary and secondary teachers, school-based mentors, and instructional leaders.",
                "cover_image": "https://images.unsplash.com/photo-1523050854058-8df90110c9f1",
                "passing_score": 60,
                "estimated_duration_hours": 10,
                "modules": [
                    {
                        "title": "Module 1: CBC Core Concepts",
                        "description": "Understand competencies, progression, and classroom implications.",
                        "lessons": [
                            {
                                "title": "What Competency-Based Learning Looks Like",
                                "lesson_type": Lesson.TYPE_READING,
                                "duration_minutes": 35,
                                "summary": "Defines competency development and contrasts it with content-only teaching.",
                                "content": (
                                    "Teachers unpack competency as the integrated use of knowledge, skills, values, "
                                    "and attitudes. The lesson includes practical examples of classroom routines that "
                                    "build communication, collaboration, and critical thinking through daily tasks."
                                ),
                                "resources": [
                                    {
                                        "title": "UNESCO Teacher Task Force Knowledge Hub",
                                        "file_url": "https://teachertaskforce.org/knowledge-hub",
                                        "resource_type": LessonResource.TYPE_LINK,
                                    }
                                ],
                            },
                            {
                                "title": "Writing Competency-Aligned Learning Outcomes",
                                "lesson_type": Lesson.TYPE_ASSIGNMENT,
                                "duration_minutes": 45,
                                "summary": "Practice writing measurable outcomes and success criteria.",
                                "content": (
                                    "Participants convert broad syllabus topics into clear outcomes and success criteria. "
                                    "They review examples, identify weak wording, and produce improved outcomes for their subjects."
                                ),
                                "downloadable_material_url": "https://www.gcedclearinghouse.org/resources/lesson-plan-template",
                                "resources": [
                                    {
                                        "title": "Lesson Planning Template",
                                        "file_url": "https://www.gcedclearinghouse.org/resources/lesson-plan-template",
                                        "resource_type": LessonResource.TYPE_DOC,
                                    }
                                ],
                            },
                            {
                                "title": "Planning for Active Learning in Large Classes",
                                "lesson_type": Lesson.TYPE_VIDEO,
                                "duration_minutes": 30,
                                "summary": "Shows routines for pair, group, and peer-feedback work in crowded classrooms.",
                                "content": (
                                    "This lesson demonstrates practical activity structures for classes with high enrollment. "
                                    "Teachers learn how to organize low-cost collaborative tasks, rotate support, and track participation."
                                ),
                                "video_url": "https://www.youtube.com/watch?v=QfYY0x7U3zQ",
                                "resources": [
                                    {
                                        "title": "Active Learning Classroom Guide",
                                        "file_url": "https://www.edutopia.org/article/active-learning-strategies",
                                        "resource_type": LessonResource.TYPE_LINK,
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "title": "Module 2: Classroom Implementation",
                        "description": "Turn plans into routines, assessment, and improvement actions.",
                        "lessons": [
                            {
                                "title": "Formative Checks During Instruction",
                                "lesson_type": Lesson.TYPE_READING,
                                "duration_minutes": 40,
                                "summary": "Use exit tickets, mini-whiteboards, and oral probes for fast feedback.",
                                "content": (
                                    "Teachers design quick checks that reveal misconceptions while teaching is happening. "
                                    "The lesson focuses on immediate response moves and lesson adaptation."
                                ),
                                "resources": [
                                    {
                                        "title": "Formative Assessment Strategies",
                                        "file_url": "https://www.edutopia.org/blog/5-fast-formative-assessment-strategies-todd-finley",
                                        "resource_type": LessonResource.TYPE_LINK,
                                    }
                                ],
                            },
                            {
                                "title": "Giving Actionable Learner Feedback",
                                "lesson_type": Lesson.TYPE_ASSIGNMENT,
                                "duration_minutes": 35,
                                "summary": "Practice feedback language that drives improvement.",
                                "content": (
                                    "Participants analyze weak versus strong feedback examples and draft subject-specific "
                                    "feedback statements that include feed-up, feedback, and feed-forward."
                                ),
                                "resources": [
                                    {
                                        "title": "Effective Feedback Research Summary",
                                        "file_url": "https://www.visiblelearningmetax.com/influences/view/feedback",
                                        "resource_type": LessonResource.TYPE_LINK,
                                    }
                                ],
                            },
                            {
                                "title": "Reflective Practice and Professional Growth",
                                "lesson_type": Lesson.TYPE_READING,
                                "duration_minutes": 30,
                                "summary": "Establish weekly reflection routines tied to learner evidence.",
                                "content": (
                                    "The lesson introduces simple reflection protocols and peer support cycles. "
                                    "Teachers identify one instructional improvement target per week and track progress."
                                ),
                                "resources": [
                                    {
                                        "title": "Teacher Reflection Toolkit",
                                        "file_url": "https://www.readingrockets.org/topics/professional-development/articles/teacher-reflection",
                                        "resource_type": LessonResource.TYPE_LINK,
                                    }
                                ],
                            },
                        ],
                    },
                ],
                "quiz": {
                    "title": "CBC Foundations Endline Quiz",
                    "description": "Checks practical understanding of CBC planning and classroom routines.",
                    "questions": [
                        {
                            "text": "Which outcome statement is most competency-focused?",
                            "option_a": "Understand photosynthesis",
                            "option_b": "Know chapter 3 notes",
                            "option_c": "Explain plant food production and apply it in a farm activity",
                            "option_d": "Read textbook pages 10 to 15",
                            "correct_option": "C",
                            "explanation": "It combines knowledge and practical application.",
                        },
                        {
                            "text": "The best use of exit tickets is to:",
                            "option_a": "Grade learners at end of term",
                            "option_b": "Collect immediate evidence for next-step teaching",
                            "option_c": "Replace all quizzes",
                            "option_d": "Punish weak performance",
                            "correct_option": "B",
                            "explanation": "Exit tickets support formative decision-making.",
                        },
                        {
                            "text": "Actionable feedback should include:",
                            "option_a": "General praise only",
                            "option_b": "A score without comment",
                            "option_c": "Specific next steps to improve",
                            "option_d": "Comparison with top learners",
                            "correct_option": "C",
                            "explanation": "Learners need clear improvement guidance.",
                        },
                        {
                            "text": "In a large class, active learning is strengthened when teachers:",
                            "option_a": "Use lecture for the whole period",
                            "option_b": "Use structured pair or group tasks with clear roles",
                            "option_c": "Avoid peer interaction",
                            "option_d": "Only call on high performers",
                            "correct_option": "B",
                            "explanation": "Structured collaboration increases engagement and practice.",
                        },
                    ],
                },
            },
            {
                "slug": "assessment-for-learning-practice",
                "title": "Assessment for Learning: Practical Classroom Methods",
                "category": "Assessment & Evaluation",
                "level": Course.LEVEL_INTERMEDIATE,
                "short_description": "Design fair, practical, and competency-aligned assessment in everyday teaching.",
                "description": (
                    "Teachers build strong formative and summative assessment workflows, from rubrics and item writing "
                    "to moderation and feedback cycles for improved learner outcomes."
                ),
                "learning_objectives": (
                    "- Design assessment plans aligned to outcomes.\n"
                    "- Develop quality items across cognitive levels.\n"
                    "- Use rubrics and moderation for fairness.\n"
                    "- Interpret evidence and adapt instruction."
                ),
                "prerequisites": "Experience administering class tests and assignments.",
                "target_audience": "Teachers, heads of department, and assessment coordinators.",
                "cover_image": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173",
                "passing_score": 65,
                "estimated_duration_hours": 12,
                "modules": [
                    {
                        "title": "Module 1: Assessment Design",
                        "description": "Plan classroom assessment with quality and purpose.",
                        "lessons": [
                            {
                                "title": "Building Balanced Assessment Plans",
                                "lesson_type": Lesson.TYPE_READING,
                                "duration_minutes": 40,
                                "summary": "Map outcomes to methods, timing, and evidence sources.",
                                "content": (
                                    "Participants map term outcomes against low-stakes checks, assignments, projects, "
                                    "and end-of-unit assessments. The focus is balanced evidence collection."
                                ),
                                "resources": [
                                    {
                                        "title": "Assessment Planning Basics",
                                        "file_url": "https://www.edutopia.org/article/what-meaningful-assessment-looks",
                                        "resource_type": LessonResource.TYPE_LINK,
                                    }
                                ],
                            },
                            {
                                "title": "Writing High-Quality Test and Quiz Items",
                                "lesson_type": Lesson.TYPE_ASSIGNMENT,
                                "duration_minutes": 50,
                                "summary": "Improve clarity, validity, and challenge level in classroom items.",
                                "content": (
                                    "Teachers analyze item flaws such as cueing, ambiguity, and mismatch to outcomes. "
                                    "They then rewrite items and peer-review quality."
                                ),
                                "resources": [
                                    {
                                        "title": "Guide to Better MCQ Writing",
                                        "file_url": "https://cei.umn.edu/support-services/tutorials/question-writing",
                                        "resource_type": LessonResource.TYPE_LINK,
                                    }
                                ],
                            },
                            {
                                "title": "Using Rubrics for Transparent Marking",
                                "lesson_type": Lesson.TYPE_READING,
                                "duration_minutes": 35,
                                "summary": "Create criterion-based rubrics learners can understand and use.",
                                "content": (
                                    "The lesson provides rubric examples and a build process from outcomes. "
                                    "Teachers produce one rubric for a real assignment in their subject."
                                ),
                                "resources": [
                                    {
                                        "title": "Rubric Design Handbook",
                                        "file_url": "https://teaching.berkeley.edu/resources/improve/assessment-rubrics",
                                        "resource_type": LessonResource.TYPE_LINK,
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "title": "Module 2: Feedback, Moderation, and Action",
                        "description": "Use data and professional dialogue to improve learning.",
                        "lessons": [
                            {
                                "title": "Feedback Cycles that Improve Learner Work",
                                "lesson_type": Lesson.TYPE_READING,
                                "duration_minutes": 35,
                                "summary": "Establish draft-feedback-redraft loops in practical ways.",
                                "content": (
                                    "Teachers design short feedback cycles that are manageable and meaningful. "
                                    "They integrate peer and self-assessment to reduce marking load."
                                ),
                                "resources": [
                                    {
                                        "title": "Feedback for Learning Overview",
                                        "file_url": "https://www.cambridge-community.org.uk/professional-development/gswfl/index.html",
                                        "resource_type": LessonResource.TYPE_LINK,
                                    }
                                ],
                            },
                            {
                                "title": "Collaborative Moderation for Fairness",
                                "lesson_type": Lesson.TYPE_ASSIGNMENT,
                                "duration_minutes": 45,
                                "summary": "Use moderation meetings to align marking standards.",
                                "content": (
                                    "Participants practice moderation using anonymized learner scripts and common rubrics. "
                                    "They define moderation protocols for departments."
                                ),
                                "resources": [
                                    {
                                        "title": "Moderation Protocol Template",
                                        "file_url": "https://www.aare.edu.au/blog/?p=13790",
                                        "resource_type": LessonResource.TYPE_LINK,
                                    }
                                ],
                            },
                            {
                                "title": "Using Assessment Data to Reteach",
                                "lesson_type": Lesson.TYPE_VIDEO,
                                "duration_minutes": 30,
                                "summary": "Turn quiz and assignment results into reteaching plans.",
                                "content": (
                                    "Teachers identify error patterns and plan targeted remediation groups. "
                                    "The lesson highlights practical routines for weak-topic intervention."
                                ),
                                "video_url": "https://www.youtube.com/watch?v=9fWlQfmvM2k",
                                "resources": [
                                    {
                                        "title": "Data-Driven Instruction Primer",
                                        "file_url": "https://www.gse.harvard.edu/ideas/usable-knowledge/17/07/data-driven-instruction",
                                        "resource_type": LessonResource.TYPE_LINK,
                                    }
                                ],
                            },
                        ],
                    },
                ],
                "quiz": {
                    "title": "Assessment for Learning Endline Quiz",
                    "description": "Measures practical assessment design and improvement decisions.",
                    "questions": [
                        {
                            "text": "A balanced classroom assessment plan should:",
                            "option_a": "Use only end-of-term exams",
                            "option_b": "Rely only on oral questioning",
                            "option_c": "Mix formative and summative evidence",
                            "option_d": "Avoid practical tasks",
                            "correct_option": "C",
                            "explanation": "Balanced evidence improves reliability and usefulness.",
                        },
                        {
                            "text": "The main purpose of a rubric is to:",
                            "option_a": "Increase marking speed only",
                            "option_b": "Clarify criteria and performance levels",
                            "option_c": "Remove teacher judgment",
                            "option_d": "Replace feedback comments",
                            "correct_option": "B",
                            "explanation": "Rubrics make expectations and judgments explicit.",
                        },
                        {
                            "text": "Moderation meetings help teachers to:",
                            "option_a": "Punish strict markers",
                            "option_b": "Align standards and reduce bias",
                            "option_c": "Skip feedback writing",
                            "option_d": "Increase test difficulty randomly",
                            "correct_option": "B",
                            "explanation": "Moderation improves fairness and consistency.",
                        },
                        {
                            "text": "After identifying weak performance in one topic, the best next step is to:",
                            "option_a": "Move to new content immediately",
                            "option_b": "Reteach with targeted support and check again",
                            "option_c": "Drop the topic",
                            "option_d": "Ignore low scores",
                            "correct_option": "B",
                            "explanation": "Data should trigger instructional adjustment.",
                        },
                    ],
                },
            },
            {
                "slug": "inclusive-teaching-and-udl",
                "title": "Inclusive Teaching and Universal Design for Learning",
                "category": "Inclusion & Learner Support",
                "level": Course.LEVEL_INTERMEDIATE,
                "short_description": "Design inclusive classrooms that support diverse learner needs every day.",
                "description": (
                    "This course equips teachers with practical inclusion approaches: barrier identification, UDL planning, "
                    "differentiated instruction, and family support partnerships."
                ),
                "learning_objectives": (
                    "- Identify learning barriers and participation gaps.\n"
                    "- Apply UDL principles in lesson planning.\n"
                    "- Differentiate tasks, scaffolds, and assessment.\n"
                    "- Build inclusion partnerships with families and peers."
                ),
                "prerequisites": "General teaching experience and willingness to adapt practice.",
                "target_audience": "Mainstream teachers, SEN coordinators, and school leaders.",
                "cover_image": "https://images.unsplash.com/photo-1509062522246-3755977927d7",
                "passing_score": 65,
                "estimated_duration_hours": 11,
                "modules": [
                    {
                        "title": "Module 1: Foundations of Inclusion",
                        "description": "Understand barriers and practical inclusion choices.",
                        "lessons": [
                            {
                                "title": "Recognizing Barriers to Participation",
                                "lesson_type": Lesson.TYPE_READING,
                                "duration_minutes": 35,
                                "summary": "Map physical, instructional, language, and social barriers.",
                                "content": (
                                    "Teachers use case studies to identify learner barriers and prioritize modifications. "
                                    "The lesson emphasizes practical classroom-level solutions."
                                ),
                                "resources": [
                                    {
                                        "title": "UNICEF Inclusive Education Overview",
                                        "file_url": "https://www.unicef.org/education/inclusive-education",
                                        "resource_type": LessonResource.TYPE_LINK,
                                    }
                                ],
                            },
                            {
                                "title": "UDL Principles in Everyday Planning",
                                "lesson_type": Lesson.TYPE_ASSIGNMENT,
                                "duration_minutes": 45,
                                "summary": "Apply multiple means of engagement, representation, and expression.",
                                "content": (
                                    "Participants redesign one lesson using UDL checkpoints and peer feedback. "
                                    "The goal is practical adaptation without excessive preparation burden."
                                ),
                                "resources": [
                                    {
                                        "title": "CAST UDL Guidelines",
                                        "file_url": "https://udlguidelines.cast.org/",
                                        "resource_type": LessonResource.TYPE_LINK,
                                    }
                                ],
                            },
                            {
                                "title": "Positive Classroom Climate and Belonging",
                                "lesson_type": Lesson.TYPE_VIDEO,
                                "duration_minutes": 30,
                                "summary": "Build routines that improve safety, belonging, and participation.",
                                "content": (
                                    "This lesson introduces inclusive language, restorative routines, and peer support "
                                    "structures that reduce exclusion and increase engagement."
                                ),
                                "video_url": "https://www.youtube.com/watch?v=JmLFh7xDa6k",
                                "resources": [
                                    {
                                        "title": "Social Inclusion in Schools",
                                        "file_url": "https://www.educationworld.com/a_curr/strategy/strategy054.shtml",
                                        "resource_type": LessonResource.TYPE_LINK,
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "title": "Module 2: Instructional Adaptation",
                        "description": "Differentiate materials, support, and assessment fairly.",
                        "lessons": [
                            {
                                "title": "Differentiating Tasks by Readiness",
                                "lesson_type": Lesson.TYPE_READING,
                                "duration_minutes": 40,
                                "summary": "Use tiered tasks and scaffolds without lowering expectations.",
                                "content": (
                                    "Teachers plan task tiers with common goals and varied support levels. "
                                    "They create scaffolds for language, literacy, and pace differences."
                                ),
                                "resources": [
                                    {
                                        "title": "Differentiated Instruction Strategies",
                                        "file_url": "https://www.readingrockets.org/classroom/classroom-strategies/differentiated-instruction",
                                        "resource_type": LessonResource.TYPE_LINK,
                                    }
                                ],
                            },
                            {
                                "title": "Reasonable Assessment Accommodations",
                                "lesson_type": Lesson.TYPE_ASSIGNMENT,
                                "duration_minutes": 35,
                                "summary": "Design accommodations while keeping validity and fairness.",
                                "content": (
                                    "Participants evaluate accommodation options and document rationale. "
                                    "The lesson clarifies adjustment versus unfair advantage."
                                ),
                                "resources": [
                                    {
                                        "title": "Assessment Accommodations Guide",
                                        "file_url": "https://www.wrightslaw.com/info/test.accoms.strategy.htm",
                                        "resource_type": LessonResource.TYPE_LINK,
                                    }
                                ],
                            },
                            {
                                "title": "Engaging Families in Learner Support",
                                "lesson_type": Lesson.TYPE_READING,
                                "duration_minutes": 30,
                                "summary": "Create practical home-school communication and support plans.",
                                "content": (
                                    "Teachers design communication routines with families that focus on strengths, "
                                    "clear goals, and collaborative support for learner progress."
                                ),
                                "resources": [
                                    {
                                        "title": "Family Engagement Framework",
                                        "file_url": "https://www.pta.org/home/run-your-pta/National-Standards-for-Family-School-Partnerships",
                                        "resource_type": LessonResource.TYPE_LINK,
                                    }
                                ],
                            },
                        ],
                    },
                ],
                "quiz": {
                    "title": "Inclusive Teaching Endline Quiz",
                    "description": "Assesses practical inclusion and UDL implementation choices.",
                    "questions": [
                        {
                            "text": "Universal Design for Learning encourages teachers to provide:",
                            "option_a": "One fixed teaching method",
                            "option_b": "Multiple ways to engage, represent, and express learning",
                            "option_c": "Only oral instruction",
                            "option_d": "Identical tasks for all learners",
                            "correct_option": "B",
                            "explanation": "UDL is built on flexibility for learner variability.",
                        },
                        {
                            "text": "A useful first step in inclusion planning is to:",
                            "option_a": "Label learners by weakness",
                            "option_b": "Identify barriers to participation",
                            "option_c": "Remove challenging content",
                            "option_d": "Avoid group work",
                            "correct_option": "B",
                            "explanation": "Barrier analysis guides meaningful support actions.",
                        },
                        {
                            "text": "Differentiation is most effective when teachers:",
                            "option_a": "Lower expectations for some learners",
                            "option_b": "Maintain goals while varying support and pathways",
                            "option_c": "Give extra work to fast learners only",
                            "option_d": "Use identical materials at identical pace",
                            "correct_option": "B",
                            "explanation": "High expectations and flexible support must coexist.",
                        },
                        {
                            "text": "Family engagement improves when communication is:",
                            "option_a": "Only during discipline incidents",
                            "option_b": "Regular, strengths-based, and goal-focused",
                            "option_c": "Limited to report cards",
                            "option_d": "Highly technical and one-way",
                            "correct_option": "B",
                            "explanation": "Partnership communication increases learner support quality.",
                        },
                    ],
                },
            },
        ]

        self.stdout.write("Creating admin and teacher profiles...")
        admins = [
            self._upsert_user(payload, Profile.ROLE_STAFF, "UniteAdmin#2026")
            for payload in admin_payload
        ]
        teachers = [
            self._upsert_user(payload, Profile.ROLE_TEACHER, "TeacherPass#2026")
            for payload in teacher_payload
        ]

        self.stdout.write("Creating courses, modules, lessons, resources, and quizzes...")
        courses = [self._build_course(admins[0], payload) for payload in courses_payload]

        self.stdout.write("Creating realistic learner activity and completion records...")
        self._seed_learning_activity(teachers, courses)

        self.stdout.write(self.style.SUCCESS("\nPresentation data seeded successfully."))
        self.stdout.write("Admin credentials:")
        self.stdout.write(" - unite_admin / UniteAdmin#2026")
        self.stdout.write(" - content_manager / UniteAdmin#2026")
        self.stdout.write("Teacher credentials:")
        self.stdout.write(" - teacher_nansubuga / TeacherPass#2026")
        self.stdout.write(" - teacher_okello / TeacherPass#2026")
        self.stdout.write(" - teacher_namuli / TeacherPass#2026")
        self.stdout.write(" - teacher_kato / TeacherPass#2026")
