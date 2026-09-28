"""Перенос раздела «Закупки» со старого сайта psa.kz/zakupki/ в Wagtail.

    manage.py import_psa_procurement            # только если подразделов ещё нет
    manage.py import_psa_procurement --replace  # удалить текущие подразделы/записи и импортировать заново

Создаёт под страницей «Закупки» четыре подраздела (как на psa.kz), в каждом —
записи со всех страниц списка: дата, заголовок, текст (со страницы записи,
если она есть), файлы — скачиваются в библиотеку документов Wagtail,
коллекция «Закупки». Казахские заголовки/тексты берутся с psa.kz/kz/ там,
где они есть (кроме архива — там на psa.kz всё по-русски).

Страницы psa.kz и файлы кэшируются на диске (--cache-dir), повторный запуск
ничего не качает заново. HTTPS — через системное хранилище сертификатов
(truststore), иначе в сетях с перехватом TLS запросы не проходят.
"""
import datetime
import hashlib
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import truststore
from anyascii import anyascii
from bs4 import BeautifulSoup, Comment, NavigableString, Tag
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify
from wagtail.documents.models import Document
from wagtail.models import Collection
from wagtail.rich_text import RichText

from content.models import ProcurementIndexPage, ProcurementPage, ProcurementSectionPage

BASE_URL = "https://psa.kz"

SECTIONS = [
    {
        "slug": "contacts",
        "path": "/zakupki/otvetstvennyye_litsa/",
        "title": "Контактные лица",
        "title_kz": "Байланыс тұлғалары",
        "title_en": "Contact persons",
        "kz": True,
    },
    {
        "slug": "archive",
        "path": "/zakupki/archiv/",
        "title": "Архив",
        "title_kz": "Архив",
        "title_en": "Archive",
        "kz": False,
    },
    {
        "slug": "announcements",
        "path": "/zakupki/announce/",
        "title": "Объявления",
        "title_kz": "Хабарландырулар",
        "title_en": "Announcements",
        "kz": True,
    },
    {
        "slug": "special-procedure",
        "path": "/zakupki/osobiy-poriadok-osushestvlenija-zakupok/",
        "title": "Особый порядок осуществления закупок",
        "title_kz": "Сатып алуды жүзеге асырудың ерекше тәртібі",
        "title_en": "Special procurement procedure",
        "kz": True,
    },
]

INLINE_TAGS = {"a", "b", "strong", "i", "em", "u", "br", "span", "font", "sup", "sub"}
KEEP_TAGS = {"p", "br", "a", "b", "strong", "i", "em", "ul", "ol", "li", "h2", "h3", "h4",
             "table", "thead", "tbody", "tr", "th", "td", "img"}
KEEP_ATTRS = {"a": {"href"}, "td": {"colspan", "rowspan"}, "th": {"colspan", "rowspan"}, "img": {"src", "alt"}}
FILE_LINK_TEXTS = {"", "скачать", "скачать файл", "жүктеу", "жүктеп алу", "файлды жүктеу", "download"}


class FileMissing(Exception):
    """Файл, на который ссылается psa.kz, там уже не существует (404)."""


class Command(BaseCommand):
    help = "Импорт раздела «Закупки» с psa.kz (подразделы, записи, файлы, казахские переводы)."

    def add_arguments(self, parser):
        parser.add_argument("--replace", action="store_true", help="Удалить текущие подразделы «Закупок» и файлы коллекции «Закупки» перед импортом.")
        parser.add_argument("--cache-dir", default=str(Path(tempfile.gettempdir()) / "psa_import_cache"))

    def handle(self, *args, replace=False, cache_dir=None, **options):
        truststore.inject_into_ssl()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        index = ProcurementIndexPage.objects.first()
        if index is None:
            raise CommandError("Нет страницы «Закупки» (ProcurementIndexPage) — сначала manage.py migrate.")
        if index.get_children().exists():
            if not replace:
                raise CommandError("В «Закупках» уже есть страницы. Запустите с --replace, чтобы заменить их импортом.")
            self.stdout.write("Удаляю текущие страницы в «Закупках»…")
            for child in index.get_children():
                child.delete()

        self.collection = self.get_collection(replace)
        self.documents = {}  # URL файла на psa.kz → Document (None — файла на psa.kz нет)
        self.by_hash = {}  # один и тот же файл под разными ссылками (ru/kz) — один документ
        self.missing = []

        # Сначала всё скачиваем/разбираем (долго, сеть), потом одной транзакцией пишем в базу.
        parsed = []
        for spec in SECTIONS:
            items = self.parse_list(spec["path"])
            self.stdout.write(f"{spec['title']}: {len(items)} записей")
            for item in items:
                if item["href"]:
                    item.update(self.parse_detail(item["href"]))
            if spec["kz"]:
                self.attach_kz(spec["path"], items)
            parsed.append((spec, items))

        for spec, items in parsed:
            for item in items:
                item["documents"] = [d for d in (self.get_document(url, title) for url, title in item["files"]) if d]

        with transaction.atomic():
            for spec, items in parsed:
                self.create_section(index, spec, items)

        self.stdout.write(self.style.SUCCESS(
            f"Готово: {sum(len(items) for _, items in parsed)} записей, {len(self.by_hash)} файлов."
        ))
        if self.missing:
            self.stdout.write(self.style.WARNING(f"На psa.kz не найдены (404), пропущены — {len(self.missing)}:"))
            for url in self.missing:
                self.stdout.write(f"  {url}")

    # ---------- сеть ----------

    def fetch(self, url, binary=False):
        key = hashlib.sha1(url.encode()).hexdigest()
        cached = self.cache_dir / key
        if cached.exists():
            data = cached.read_bytes()
        else:
            parts = urllib.parse.urlsplit(url)
            # В ссылках psa.kz встречаются и сырые пробелы/кириллица, и уже закодированные %20.
            safe_path = urllib.parse.quote(urllib.parse.unquote(parts.path))
            safe_url = urllib.parse.urlunsplit(parts._replace(path=safe_path))
            for attempt in range(4):
                try:
                    with urllib.request.urlopen(urllib.request.Request(safe_url, headers={"User-Agent": "psa-import"}), timeout=60) as response:
                        data = response.read()
                    break
                except urllib.error.HTTPError as error:
                    if error.code == 404:
                        raise FileMissing(url) from error
                    if attempt == 3:
                        raise CommandError(f"Не удалось скачать {url}: {error}") from error
                    time.sleep(2 * (attempt + 1))
                except Exception as error:  # noqa: BLE001
                    if attempt == 3:
                        raise CommandError(f"Не удалось скачать {url}: {error}") from error
                    time.sleep(2 * (attempt + 1))
            cached.write_bytes(data)
        return data if binary else data.decode("utf-8", errors="replace")

    def soup(self, url):
        return BeautifulSoup(self.fetch(url), "html.parser")

    # ---------- разбор psa.kz ----------

    def parse_list(self, path, lang_prefix=""):
        first = self.soup(BASE_URL + lang_prefix + path)
        pages = [int(n) for n in re.findall(r"PAGEN_1=(\d+)", str(first))]
        items = []
        for number in range(1, max(pages, default=1) + 1):
            page = first if number == 1 else self.soup(f"{BASE_URL}{lang_prefix}{path}?PAGEN_1={number}")
            for block in page.select("div.content .news-v3"):
                heading = block.select_one("h2")
                if heading is None:
                    continue
                link = heading.select_one("a")
                date = block.select_one(".posted-info li")
                files = [(self.absolute(a["href"]), "") for a in block.select(".download-files a[href]")]
                text_parts = [p for p in block.find_all("p", recursive=True) if "download-files" not in (p.get("class") or [])]
                items.append({
                    "href": link["href"] if link else None,
                    "id": self.item_id(link["href"]) if link else None,
                    "title": " ".join(heading.get_text().split()),
                    "date": self.parse_date(date.get_text(strip=True) if date else ""),
                    "body": "".join(str(p) for p in text_parts),
                    "files": files,
                })
        return items

    def parse_detail(self, href, lang_prefix=""):
        if lang_prefix and href.startswith(lang_prefix + "/"):
            lang_prefix = ""  # ссылки в /kz/-списках уже с префиксом
        page = self.soup(BASE_URL + lang_prefix + href)
        block = page.select_one("div.content .news-v3") or page.select_one("div.content")
        heading = block.select_one("h2")
        title = " ".join(heading.get_text().split()) if heading else None
        if heading:
            heading.decompose()
        for tag in block.select("ul.posted-info"):
            tag.decompose()
        files = []
        for a in block.select("a[href]"):
            href_abs = self.absolute(a["href"])
            if "/upload/" in href_abs:
                text = a.get_text(" ", strip=True)
                files.append((href_abs, "" if text.lower() in FILE_LINK_TEXTS else text))
                if text.lower() in FILE_LINK_TEXTS:
                    parent = a.parent
                    a.decompose()
                    if parent.name == "p" and not parent.get_text(strip=True):
                        parent.decompose()
        result = {"body": block.decode_contents(), "files": files}
        if title:
            result["title"] = title
        return result

    def attach_kz(self, path, items):
        # У казахских версий на psa.kz свои ID записей (1157 ↔ 1156 и т.п.),
        # поэтому сопоставляем по порядку в списке; если записей разное
        # количество — по дате (первая свободная запись с той же датой).
        kz_items = [i for i in self.parse_list(path, lang_prefix="/kz") if i["href"]]
        ru_items = [i for i in items if i["href"]]
        if len(kz_items) == len(ru_items):
            pairs = zip(ru_items, kz_items)
        else:
            free = list(ru_items)
            pairs = []
            for kz_item in kz_items:
                match = next((i for i in free if i["date"] and i["date"] == kz_item["date"]), None)
                if match:
                    free.remove(match)
                    pairs.append((match, kz_item))
        for item, kz_item in pairs:
            detail = self.parse_detail(kz_item["href"], lang_prefix="/kz")
            item["title_kz"] = detail.get("title") or kz_item["title"]
            item["body_kz"] = detail["body"]
            known = {url for url, _ in item["files"]}
            item["files"] += [f for f in detail["files"] if f[0] not in known]

    @staticmethod
    def item_id(href):
        numbers = re.findall(r"/(\d+)/?$", href)
        return numbers[0] if numbers else href

    @staticmethod
    def parse_date(value):
        try:
            return datetime.datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            return None

    @staticmethod
    def absolute(href):
        if href.startswith(("http://", "https://", "mailto:", "tel:", "#")):
            return href
        return urllib.parse.urljoin(BASE_URL + "/", href)

    # ---------- файлы ----------

    def get_collection(self, replace):
        root = Collection.get_first_root_node()
        collection = root.get_children().filter(name="Закупки").first()
        if collection and replace:
            # Файлы с диска Wagtail удаляет сам при удалении документа.
            for document in Document.objects.filter(collection=collection):
                document.delete()
        return collection or root.add_child(name="Закупки")

    def get_document(self, url, title=""):
        if url in self.documents:
            return self.documents[url]
        filename = urllib.parse.unquote(url.rsplit("/", 1)[-1]) or "file"
        try:
            data = self.fetch(url, binary=True)
        except FileMissing:
            self.missing.append(url)
            self.documents[url] = None
            return None
        digest = hashlib.sha1(data).hexdigest()
        if digest in self.by_hash:
            self.documents[url] = self.by_hash[digest]
            return self.by_hash[digest]
        document = Document(title=(title or Path(filename).stem)[:255], collection=self.collection)
        document.file.save(filename, ContentFile(data), save=False)
        document._set_document_file_metadata()
        document.save()
        self.documents[url] = self.by_hash[digest] = document
        return document

    # ---------- HTML → блоки Wagtail ----------

    def to_blocks(self, html):
        """Чистый HTML (только теги редактора, без стилей) → блок «Текст»;
        если внутри таблица или картинка — блок «HTML» (Draftail их не умеет)."""
        if not html or not BeautifulSoup(html, "html.parser").get_text(strip=True):
            return []
        cleaned, rich = self.clean_html(html)
        if not cleaned:
            return []
        if rich:
            return [("text", RichText(cleaned))]
        return [("html", cleaned)]

    def clean_html(self, html):
        soup = BeautifulSoup(html, "html.parser")
        for node in soup.find_all(string=lambda s: isinstance(s, Comment)):
            node.extract()
        for tag in soup.find_all(["script", "style", "noscript"]):
            tag.decompose()
        rich = not soup.find(["table", "img"])
        for tag in soup.find_all(True):
            if tag.name == "div":
                tag.name = "p"
            if tag.name not in KEEP_TAGS:
                tag.unwrap()
                continue
            tag.attrs = {k: v for k, v in tag.attrs.items() if k in KEEP_ATTRS.get(tag.name, ())}
            if tag.name == "a" and tag.get("href"):
                href = self.absolute(tag["href"])
                document = self.get_document(href, tag.get_text(" ", strip=True)) if "/upload/" in href else None
                if document:
                    tag.attrs = {"linktype": "document", "id": str(document.pk)} if rich else {"href": document.url}
                else:
                    tag["href"] = href
                    # На psa.kz бывает: текст ссылки — один e-mail, а mailto — старый
                    # адрес другого сотрудника. Верим тому, что видит посетитель.
                    text = tag.get_text(strip=True)
                    if href.startswith("mailto:") and re.fullmatch(r"[\w.+-]+@[\w-]+(\.[\w-]+)+", text) and href[7:].lower() != text.lower():
                        tag["href"] = f"mailto:{text}"
            if tag.name == "img" and tag.get("src"):
                tag["src"] = self.absolute(tag["src"])

        # Текст и inline-теги верхнего уровня (на psa.kz часть текста лежит прямо
        # в <div> через <br>) собираем в абзацы.
        out, run = [], []

        def flush():
            fragment = "".join(str(n) for n in run).strip()
            fragment = re.sub(r"^(<br/?>\s*)+|(<br/?>\s*)+$", "", fragment)
            if BeautifulSoup(fragment, "html.parser").get_text(strip=True):
                out.append(f"<p>{fragment}</p>")
            run.clear()

        for node in list(soup.children):
            if isinstance(node, NavigableString) or (isinstance(node, Tag) and node.name in INLINE_TAGS):
                run.append(node)
            else:
                flush()
                if node.get_text(strip=True) or node.find("img"):
                    out.append(str(node))
        flush()
        return "".join(out), rich

    # ---------- запись в Wagtail ----------

    def create_section(self, index, spec, items):
        section = ProcurementSectionPage(
            title=spec["title"], slug=spec["slug"], title_kz=spec["title_kz"], title_en=spec["title_en"],
        )
        index.add_child(instance=section)
        section.save_revision().publish()

        used_slugs = set()
        for item in items:
            base = slugify(anyascii(item["title"]))[:60].strip("-") or "zapis"
            slug, n = base, 2
            while slug in used_slugs:
                slug, n = f"{base}-{n}", n + 1
            used_slugs.add(slug)

            page = ProcurementPage(
                title=item["title"][:255],
                slug=slug,
                date=item["date"],
                description=self.to_blocks(item["body"]),
                attachments=[("file", document) for document in dict.fromkeys(item["documents"])],
                title_kz=item.get("title_kz", "")[:255],
                description_kz=self.to_blocks(item.get("body_kz", "")),
            )
            section.add_child(instance=page)
            page.save_revision().publish()
            if item["date"]:
                published = datetime.datetime.combine(item["date"], datetime.time(9, 0), tzinfo=datetime.timezone.utc)
                ProcurementPage.objects.filter(pk=page.pk).update(first_published_at=published, last_published_at=published)
