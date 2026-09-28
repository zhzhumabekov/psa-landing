"""Раздел «Проекты» и три страницы проектов.

Тексты перенесены из статичного блока «Проекты» главной (переводы и
projectDetails в static/script.js на 2026-09-28): краткое описание — блок
«Текст», факты («Тип соглашения», «Расположение», «Роль PSA») — блок
«Таблица». Дальше контент живёт в админке; блок на главной не трогаем.
"""
import uuid

from django.db import migrations
from django.utils import timezone

PROJECTS = {'kashagan': {'ru': {'title': 'Кашаган',
                     'region': 'Северный Каспий',
                     'teaser': 'Одно из крупнейших морских месторождений региона на шельфе Каспийского моря.',
                     'summary': 'Кашаган — гигантское нефтяное месторождение на шельфе Северного Каспия, '
                                'одно из крупнейших открытий в мире за последние десятилетия. Реализуется в '
                                'рамках Северо-Каспийского соглашения о разделе продукции.',
                     'facts': [['Тип соглашения', 'Соглашение о разделе продукции (СРП)'],
                               ['Расположение', 'Шельф Каспийского моря'],
                               ['Роль PSA',
                                'Представление интересов государства, контроль исполнения соглашения']]},
              'kz': {'title': 'Қашаған',
                     'region': 'Солтүстік Каспий',
                     'teaser': 'Каспий теңізінің шельфіндегі аймақтың ірі теңіз кен орындарының бірі.',
                     'summary': 'Қашаған — Солтүстік Каспий шельфіндегі алып мұнай кен орны, соңғы '
                                'онжылдықтардағы әлемдегі ірі ашылымдардың бірі. Солтүстік Каспий өнімді '
                                'бөлу туралы келісімі аясында іске асырылады.',
                     'facts': [['Келісім түрі', 'Өнімді бөлу туралы келісім (ӨБК)'],
                               ['Орналасқан жері', 'Каспий теңізінің шельфі'],
                               ['PSA рөлі', 'Мемлекет мүддесін білдіру, келісімнің орындалуын бақылау']]},
              'en': {'title': 'Kashagan',
                     'region': 'North Caspian',
                     'teaser': "One of the region's largest offshore fields, located on the Caspian Sea "
                               'shelf.',
                     'summary': 'Kashagan is a giant offshore oil field in the North Caspian Sea, one of the '
                                'largest discoveries worldwide in recent decades. It is developed under the '
                                'North Caspian production sharing agreement.',
                     'facts': [['Agreement type', 'Production sharing agreement (PSA)'],
                               ['Location', 'Caspian Sea shelf'],
                               ["PSA's role",
                                'Representing state interests, overseeing agreement compliance']]}},
 'karachaganak': {'ru': {'title': 'Карачаганак',
                         'region': 'Западный Казахстан',
                         'teaser': 'Гигантское нефтегазоконденсатное месторождение в Западно-Казахстанской '
                                   'области.',
                         'summary': 'Карачаганак — одно из крупнейших в мире нефтегазоконденсатных '
                                    'месторождений, расположенное в Западно-Казахстанской области. '
                                    'Разработка ведётся на условиях окончательного соглашения о разделе '
                                    'продукции.',
                         'facts': [['Тип соглашения', 'Окончательное соглашение о разделе продукции'],
                                   ['Расположение', 'Западно-Казахстанская область'],
                                   ['Роль PSA',
                                    'Контроль исполнения соглашения, защита национальных интересов']]},
                  'kz': {'title': 'Қарашығанақ',
                         'region': 'Батыс Қазақстан',
                         'teaser': 'Батыс Қазақстан облысындағы алып мұнай-газ конденсат кен орны.',
                         'summary': 'Қарашығанақ — Батыс Қазақстан облысында орналасқан әлемдегі ірі '
                                    'мұнай-газ конденсат кен орындарының бірі. Игеру өнімді бөлу туралы '
                                    'түпкілікті келісім негізінде жүргізіледі.',
                         'facts': [['Келісім түрі', 'Өнімді бөлу туралы түпкілікті келісім'],
                                   ['Орналасқан жері', 'Батыс Қазақстан облысы'],
                                   ['PSA рөлі', 'Келісімнің орындалуын бақылау, ұлттық мүдделерді қорғау']]},
                  'en': {'title': 'Karachaganak',
                         'region': 'West Kazakhstan',
                         'teaser': 'A giant oil and gas condensate field in the West Kazakhstan region.',
                         'summary': "Karachaganak is one of the world's largest oil and gas condensate "
                                    'fields, located in the West Kazakhstan region. Development proceeds '
                                    'under the final production sharing agreement.',
                         'facts': [['Agreement type', 'Final production sharing agreement'],
                                   ['Location', 'West Kazakhstan region'],
                                   ["PSA's role",
                                    'Overseeing agreement compliance, protecting national interests']]}},
 'dunga': {'ru': {'title': 'Дунга',
                  'region': 'Мангистауская область',
                  'teaser': 'Нефтяное месторождение с действующим соглашением о разделе продукции.',
                  'summary': 'Дунга — нефтяное месторождение в Мангистауской области, разрабатываемое в '
                             'рамках соглашения о разделе продукции. PSA обеспечивает представительство '
                             'интересов государства и развитие казахстанского содержания.',
                  'facts': [['Тип соглашения', 'Соглашение о разделе продукции (СРП)'],
                            ['Расположение', 'Мангистауская область'],
                            ['Роль PSA',
                             'Представление интересов государства, развитие казахстанского содержания']]},
           'kz': {'title': 'Дунга',
                  'region': 'Маңғыстау облысы',
                  'teaser': 'Өнімді бөлу туралы қолданыстағы келісімі бар мұнай кен орны.',
                  'summary': 'Дунга — Маңғыстау облысындағы өнімді бөлу туралы келісім аясында игерілетін '
                             'мұнай кен орны. PSA мемлекет мүддесін білдіруді және қазақстандық қамтуды '
                             'дамытуды қамтамасыз етеді.',
                  'facts': [['Келісім түрі', 'Өнімді бөлу туралы келісім (ӨБК)'],
                            ['Орналасқан жері', 'Маңғыстау облысы'],
                            ['PSA рөлі', 'Мемлекет мүддесін білдіру, қазақстандық қамтуды дамыту']]},
           'en': {'title': 'Dunga',
                  'region': 'Mangystau region',
                  'teaser': 'An oil field operating under an active production sharing agreement.',
                  'summary': 'Dunga is an oil field in the Mangystau region, developed under a production '
                             'sharing agreement. PSA represents state interests and supports the development '
                             'of Kazakhstani content.',
                  'facts': [['Agreement type', 'Production sharing agreement (PSA)'],
                            ['Location', 'Mangystau region'],
                            ["PSA's role", 'Representing state interests, developing Kazakhstani content']]}}}


def body(lang_data):
    return [
        {"type": "text", "value": f"<p>{lang_data['summary']}</p>", "id": str(uuid.uuid4())},
        {
            "type": "table",
            "value": {
                "data": [list(row) for row in lang_data["facts"]],
                "first_row_is_table_header": False,
                "first_col_is_header": True,
                "table_header_choice": "column",
                "table_caption": "",
                "cell": [],
                "mergeCells": [],
            },
            "id": str(uuid.uuid4()),
        },
    ]


def create_projects(apps, schema_editor):
    ContentType = apps.get_model("contenttypes.ContentType")
    HomePage = apps.get_model("content", "HomePage")
    ProjectsIndexPage = apps.get_model("content", "ProjectsIndexPage")
    ProjectPage = apps.get_model("content", "ProjectPage")
    Page = apps.get_model("wagtailcore.Page")

    home = HomePage.objects.filter(depth=2).first()
    if home is None or ProjectsIndexPage.objects.exists():
        return
    now = timezone.now()

    def next_child_path(parent):
        last = Page.objects.filter(path__startswith=parent.path, depth=parent.depth + 1).order_by("-path").first()
        index = int(last.path[-4:], 36) + 1 if last else 1
        return parent.path + format_base36(index)

    def common(model_name, parent, title, slug, numchild=0):
        content_type, _ = ContentType.objects.get_or_create(app_label="content", model=model_name)
        return dict(
            title=title,
            draft_title=title,
            slug=slug,
            content_type=content_type,
            locale_id=parent.locale_id,
            path=next_child_path(parent),
            depth=parent.depth + 1,
            numchild=numchild,
            url_path=f"{parent.url_path}{slug}/",
            live=True,
            first_published_at=now,
            last_published_at=now,
        )

    index = ProjectsIndexPage.objects.create(**common("projectsindexpage", home, "Проекты", "projects", numchild=len(PROJECTS)))
    Page.objects.filter(pk=home.pk).update(numchild=home.numchild + 1)

    for slug, langs in PROJECTS.items():
        ru, kz, en = langs["ru"], langs["kz"], langs["en"]
        ProjectPage.objects.create(
            **common("projectpage", index, ru["title"], slug),
            region=ru["region"],
            teaser=ru["teaser"],
            body=body(ru),
            title_kz=kz["title"],
            region_kz=kz["region"],
            teaser_kz=kz["teaser"],
            body_kz=body(kz),
            title_en=en["title"],
            region_en=en["region"],
            teaser_en=en["teaser"],
            body_en=body(en),
        )


def format_base36(number):
    # treebeard: 4 символа base36 на уровень, верхний регистр
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    out = ""
    while number:
        number, rem = divmod(number, 36)
        out = digits[rem] + out
    return out.rjust(4, "0")


def remove_projects(apps, schema_editor):
    ProjectsIndexPage = apps.get_model("content", "ProjectsIndexPage")
    HomePage = apps.get_model("content", "HomePage")
    Page = apps.get_model("wagtailcore.Page")
    for index in ProjectsIndexPage.objects.all():
        Page.objects.filter(path__startswith=index.path).delete()
    for home in HomePage.objects.filter(depth=2):
        Page.objects.filter(pk=home.pk).update(numchild=Page.objects.filter(path__startswith=home.path, depth=3).count())


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0005_projects"),
    ]

    operations = [
        migrations.RunPython(create_projects, remove_projects),
    ]
