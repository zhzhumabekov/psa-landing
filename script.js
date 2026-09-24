/* =========================================================
   ТОО «PSA» — интерактивность лендинга
   1. Плавный скролл по якорным ссылкам
   2. Модальные окна проектов
   3. Валидация формы обратной связи
   4. Переключение языков (KZ | RU | EN)
   ========================================================= */

/* ---------- 4. Переключение языков ---------- */

const translations = {
  ru: {
    "nav.about": "О компании",
    "nav.projects": "Проекты",
    "nav.local_content": "Местное содержание",
    "nav.procurement": "Закупки",
    "nav.documents": "Документы",
    "nav.news": "Новости",
    "nav.contacts": "Контакты",
    "header.login": "Войти",
    "header.org_line1": "Полномочный орган",
    "header.org_line2": "Правительства РК",
    "hero.eyebrow": "Полномочный орган Правительства Республики Казахстан",
    "hero.title": "Представляем интересы государства в соглашениях о разделе продукции",
    "hero.subtitle": "ТОО «PSA» — Полномочный орган Правительства Республики Казахстан в проектах Кашаган, Карачаганак и Дунга.",
    "hero.cta_projects": "Наши проекты",
    "hero.cta_about": "О компании",
    "about.eyebrow": "О компании",
    "about.title": "Государственный партнёр в соглашениях о разделе продукции",
    "about.p1": "ТОО «PSA» учреждено в 2010 году и наделено статусом Полномочного органа Правительства Республики Казахстан в соглашениях о разделе продукции — в соответствии с Постановлением Правительства Республики Казахстан №355. Компания на 100% принадлежит государству.",
    "about.p2": "От имени Правительства Республики Казахстан PSA представляет интересы государства в трёх проектах СРП — Северо-Каспийском (Кашаган), Карачаганакском и Дунга, — обеспечивает контроль исполнения соглашений, защиту национальных интересов и развитие казахстанского содержания в проектах.",
    "about.stat_year": "Год учреждения",
    "about.stat_decree": "Постановление Правительства РК",
    "about.stat_state": "Участие государства",
    "about.stat_projects": "Проекта СРП",
    "projects.eyebrow": "Наши проекты",
    "projects.title": "Три соглашения о разделе продукции",
    "projects.lead": "Нажмите на карточку проекта, чтобы открыть подробное описание.",
    "projects.cta_more": "Подробнее →",
    "project.kashagan.title": "Кашаган",
    "project.kashagan.region": "Северный Каспий",
    "project.kashagan.teaser": "Одно из крупнейших морских месторождений региона на шельфе Каспийского моря.",
    "project.karachaganak.title": "Карачаганак",
    "project.karachaganak.region": "Западный Казахстан",
    "project.karachaganak.teaser": "Гигантское нефтегазоконденсатное месторождение в Западно-Казахстанской области.",
    "project.dunga.title": "Дунга",
    "project.dunga.region": "Мангистауская область",
    "project.dunga.teaser": "Нефтяное месторождение с действующим соглашением о разделе продукции.",
    "partners.eyebrow": "Партнёры",
    "partners.title": "Партнёры и участники проектов",
    "partners.lead": "Государственные органы, операторы проектов СРП и отраслевые ассоциации, с которыми взаимодействует ТОО «PSA».",
    "partner.energo.tag": "Государственный орган",
    "partner.energo.title": "Министерство энергетики Республики Казахстан",
    "partner.energo.text": "Осуществляет доверительное управление 100% доли участия ТОО «PSA» и наделило компанию функциями Полномочного органа по трём проектам СРП.",
    "partner.kmg.tag": "Национальная компания",
    "partner.kmg.title": "АО «НК «КазМунайГаз»",
    "partner.kmg.text": "Представляет интересы государства в составе консорциумов Северо-Каспийского и Карачаганакского проектов.",
    "partner.ncoc.tag": "Оператор проекта · Кашаган",
    "partner.ncoc.title": "North Caspian Operating Company N.V.",
    "partner.ncoc.text": "Оператор Северо-Каспийского проекта (месторождение Кашаган).",
    "partner.kpo.tag": "Оператор проекта · Карачаганак",
    "partner.kpo.title": "Karachaganak Petroleum Operating B.V.",
    "partner.kpo.text": "Операционная компания, созданная участниками соглашения по Карачаганакскому месторождению.",
    "partner.total.tag": "Оператор проекта · Дунга",
    "partner.total.title": "Total E&P Dunga GmbH",
    "partner.total.text": "Оператор проекта разработки месторождения Дунга.",
    "partner.atameken.tag": "Бизнес-ассоциация",
    "partner.atameken.title": "Национальная палата предпринимателей «Атамекен»",
    "partner.atameken.text": "Представляет интересы бизнеса при взаимодействии с государственными органами.",
    "partner.kazenergy.tag": "Отраслевая ассоциация",
    "partner.kazenergy.title": "KAZENERGY",
    "partner.kazenergy.text": "Ассоциация, содействующая развитию топливно-энергетического комплекса Казахстана.",
    "contacts.eyebrow": "Связаться с нами",
    "contacts.title": "Контакты",
    "contacts.lead": "Заполните форму, и мы ответим на ваше обращение.",
    "contacts.form.name_label": "Имя",
    "contacts.form.name_placeholder": "Как к вам обращаться",
    "contacts.form.email_label": "E-mail",
    "contacts.form.email_placeholder": "name@example.com",
    "contacts.form.message_label": "Сообщение",
    "contacts.form.message_placeholder": "Опишите ваш вопрос",
    "contacts.form.submit": "Отправить",
    "modal.close": "Закрыть",
    "errors.name_required": "Пожалуйста, укажите имя.",
    "errors.email_required": "Пожалуйста, укажите e-mail.",
    "errors.email_invalid": "Проверьте формат e-mail.",
    "errors.message_required": "Пожалуйста, добавьте сообщение.",
    "form.success": "Спасибо! Сообщение отправлено — мы свяжемся с вами в ближайшее время.",
  },
  kz: {
    "nav.about": "Компания туралы",
    "nav.projects": "Жобалар",
    "nav.local_content": "Жергілікті қамту",
    "nav.procurement": "Сатып алулар",
    "nav.documents": "Құжаттар",
    "nav.news": "Жаңалықтар",
    "nav.contacts": "Байланыс",
    "header.login": "Кіру",
    "header.org_line1": "Қазақстан Республикасы",
    "header.org_line2": "Үкіметінің өкілетті органы",
    "hero.eyebrow": "Қазақстан Республикасы Үкіметінің өкілетті органы",
    "hero.title": "Өнімді бөлу туралы келісімдерде мемлекет мүддесін білдіреміз",
    "hero.subtitle": "«PSA» ЖШС — Қашаған, Қарашығанақ және Дунга жобаларында Қазақстан Республикасы Үкіметінің өкілетті органы.",
    "hero.cta_projects": "Біздің жобалар",
    "hero.cta_about": "Компания туралы",
    "about.eyebrow": "Компания туралы",
    "about.title": "Өнімді бөлу туралы келісімдердегі мемлекеттік серіктес",
    "about.p1": "«PSA» ЖШС 2010 жылы құрылды және Қазақстан Республикасы Үкіметінің №355 қаулысына сәйкес өнімді бөлу туралы келісімдер бойынша Үкіметтің өкілетті органы мәртебесіне ие. Компания 100% мемлекетке тиесілі.",
    "about.p2": "Қазақстан Республикасы Үкіметінің атынан «PSA» үш ӨБК жобасында — Солтүстік Каспий (Қашаған), Қарашығанақ және Дунга — мемлекет мүддесін білдіреді, келісімдердің орындалуын бақылайды, ұлттық мүдделерді қорғайды және жобалардағы қазақстандық қамтуды дамытады.",
    "about.stat_year": "Құрылған жылы",
    "about.stat_decree": "ҚР Үкіметінің қаулысы",
    "about.stat_state": "Мемлекеттің қатысуы",
    "about.stat_projects": "ӨБК жобасы",
    "projects.eyebrow": "Біздің жобалар",
    "projects.title": "Өнімді бөлу туралы үш келісім",
    "projects.lead": "Толық сипаттаманы ашу үшін жоба карточкасын басыңыз.",
    "projects.cta_more": "Толығырақ →",
    "project.kashagan.title": "Қашаған",
    "project.kashagan.region": "Солтүстік Каспий",
    "project.kashagan.teaser": "Каспий теңізінің шельфіндегі аймақтың ірі теңіз кен орындарының бірі.",
    "project.karachaganak.title": "Қарашығанақ",
    "project.karachaganak.region": "Батыс Қазақстан",
    "project.karachaganak.teaser": "Батыс Қазақстан облысындағы алып мұнай-газ конденсат кен орны.",
    "project.dunga.title": "Дунга",
    "project.dunga.region": "Маңғыстау облысы",
    "project.dunga.teaser": "Өнімді бөлу туралы қолданыстағы келісімі бар мұнай кен орны.",
    "partners.eyebrow": "Серіктестер",
    "partners.title": "Жобалардың серіктестері мен қатысушылары",
    "contacts.eyebrow": "Бізбен байланысыңыз",
    "contacts.title": "Байланыс",
    "contacts.lead": "Форманы толтырыңыз — сұрауыңызға жауап береміз.",
    "contacts.form.name_label": "Аты-жөні",
    "contacts.form.name_placeholder": "Сізге қалай жүгінейік",
    "contacts.form.email_label": "E-mail",
    "contacts.form.email_placeholder": "name@example.com",
    "contacts.form.message_label": "Хабарлама",
    "contacts.form.message_placeholder": "Сұрағыңызды сипаттаңыз",
    "contacts.form.submit": "Жіберу",
    "modal.close": "Жабу",
    "errors.name_required": "Аты-жөніңізді көрсетіңіз.",
    "errors.email_required": "E-mail мекенжайын көрсетіңіз.",
    "errors.email_invalid": "E-mail форматын тексеріңіз.",
    "errors.message_required": "Хабарлама мәтінін қосыңыз.",
    "form.success": "Рақмет! Хабарлама жіберілді — жақын арада хабарласамыз.",
  },
  en: {
    "nav.about": "About",
    "nav.projects": "Projects",
    "nav.local_content": "Local content",
    "nav.procurement": "Procurement",
    "nav.documents": "Documents",
    "nav.news": "News",
    "nav.contacts": "Contacts",
    "header.login": "Log in",
    "header.org_line1": "Authorized body",
    "header.org_line2": "of the RK Government",
    "hero.eyebrow": "Authorized body of the Government of the Republic of Kazakhstan",
    "hero.title": "Representing the state's interests in production sharing agreements",
    "hero.subtitle": "PSA LLP is the authorized body of the Government of the Republic of Kazakhstan in the Kashagan, Karachaganak and Dunga projects.",
    "hero.cta_projects": "Our projects",
    "hero.cta_about": "About the company",
    "about.eyebrow": "About the company",
    "about.title": "The state's partner in production sharing agreements",
    "about.p1": "PSA LLP was established in 2010 and holds the status of authorized body of the Government of the Republic of Kazakhstan for production sharing agreements, in accordance with Government Decree No. 355. The company is 100% state-owned.",
    "about.p2": "On behalf of the Government of the Republic of Kazakhstan, PSA represents the state's interests in three PSA projects — North Caspian (Kashagan), Karachaganak and Dunga — overseeing agreement compliance, protecting national interests and developing Kazakhstani content in the projects.",
    "about.stat_year": "Year founded",
    "about.stat_decree": "Government decree",
    "about.stat_state": "State ownership",
    "about.stat_projects": "PSA projects",
    "projects.eyebrow": "Our projects",
    "projects.title": "Three production sharing agreements",
    "projects.lead": "Click a project card to open its detailed description.",
    "projects.cta_more": "Learn more →",
    "project.kashagan.title": "Kashagan",
    "project.kashagan.region": "North Caspian",
    "project.kashagan.teaser": "One of the region's largest offshore fields, located on the Caspian Sea shelf.",
    "project.karachaganak.title": "Karachaganak",
    "project.karachaganak.region": "West Kazakhstan",
    "project.karachaganak.teaser": "A giant oil and gas condensate field in the West Kazakhstan region.",
    "project.dunga.title": "Dunga",
    "project.dunga.region": "Mangystau region",
    "project.dunga.teaser": "An oil field operating under an active production sharing agreement.",
    "contacts.eyebrow": "Get in touch",
    "contacts.title": "Contacts",
    "contacts.lead": "Fill in the form and we will respond to your request.",
    "contacts.form.name_label": "Name",
    "contacts.form.name_placeholder": "How should we address you",
    "contacts.form.email_label": "E-mail",
    "contacts.form.email_placeholder": "name@example.com",
    "contacts.form.message_label": "Message",
    "contacts.form.message_placeholder": "Describe your question",
    "contacts.form.submit": "Send",
    "modal.close": "Close",
    "errors.name_required": "Please enter your name.",
    "errors.email_required": "Please enter your e-mail.",
    "errors.email_invalid": "Please check the e-mail format.",
    "errors.message_required": "Please add a message.",
    "form.success": "Thank you! Your message has been sent — we will get back to you soon.",
  },
};

const projectDetails = {
  kashagan: {
    ru: {
      summary: "Кашаган — гигантское нефтяное месторождение на шельфе Северного Каспия, одно из крупнейших открытий в мире за последние десятилетия. Реализуется в рамках Северо-Каспийского соглашения о разделе продукции.",
      facts: [
        ["Тип соглашения", "Соглашение о разделе продукции (СРП)"],
        ["Расположение", "Шельф Каспийского моря"],
        ["Роль PSA", "Представление интересов государства, контроль исполнения соглашения"],
      ],
    },
    kz: {
      summary: "Қашаған — Солтүстік Каспий шельфіндегі алып мұнай кен орны, соңғы онжылдықтардағы әлемдегі ірі ашылымдардың бірі. Солтүстік Каспий өнімді бөлу туралы келісімі аясында іске асырылады.",
      facts: [
        ["Келісім түрі", "Өнімді бөлу туралы келісім (ӨБК)"],
        ["Орналасқан жері", "Каспий теңізінің шельфі"],
        ["PSA рөлі", "Мемлекет мүддесін білдіру, келісімнің орындалуын бақылау"],
      ],
    },
    en: {
      summary: "Kashagan is a giant offshore oil field in the North Caspian Sea, one of the largest discoveries worldwide in recent decades. It is developed under the North Caspian production sharing agreement.",
      facts: [
        ["Agreement type", "Production sharing agreement (PSA)"],
        ["Location", "Caspian Sea shelf"],
        ["PSA's role", "Representing state interests, overseeing agreement compliance"],
      ],
    },
  },
  karachaganak: {
    ru: {
      summary: "Карачаганак — одно из крупнейших в мире нефтегазоконденсатных месторождений, расположенное в Западно-Казахстанской области. Разработка ведётся на условиях окончательного соглашения о разделе продукции.",
      facts: [
        ["Тип соглашения", "Окончательное соглашение о разделе продукции"],
        ["Расположение", "Западно-Казахстанская область"],
        ["Роль PSA", "Контроль исполнения соглашения, защита национальных интересов"],
      ],
    },
    kz: {
      summary: "Қарашығанақ — Батыс Қазақстан облысында орналасқан әлемдегі ірі мұнай-газ конденсат кен орындарының бірі. Игеру өнімді бөлу туралы түпкілікті келісім негізінде жүргізіледі.",
      facts: [
        ["Келісім түрі", "Өнімді бөлу туралы түпкілікті келісім"],
        ["Орналасқан жері", "Батыс Қазақстан облысы"],
        ["PSA рөлі", "Келісімнің орындалуын бақылау, ұлттық мүдделерді қорғау"],
      ],
    },
    en: {
      summary: "Karachaganak is one of the world's largest oil and gas condensate fields, located in the West Kazakhstan region. Development proceeds under the final production sharing agreement.",
      facts: [
        ["Agreement type", "Final production sharing agreement"],
        ["Location", "West Kazakhstan region"],
        ["PSA's role", "Overseeing agreement compliance, protecting national interests"],
      ],
    },
  },
  dunga: {
    ru: {
      summary: "Дунга — нефтяное месторождение в Мангистауской области, разрабатываемое в рамках соглашения о разделе продукции. PSA обеспечивает представительство интересов государства и развитие казахстанского содержания.",
      facts: [
        ["Тип соглашения", "Соглашение о разделе продукции (СРП)"],
        ["Расположение", "Мангистауская область"],
        ["Роль PSA", "Представление интересов государства, развитие казахстанского содержания"],
      ],
    },
    kz: {
      summary: "Дунга — Маңғыстау облысындағы өнімді бөлу туралы келісім аясында игерілетін мұнай кен орны. PSA мемлекет мүддесін білдіруді және қазақстандық қамтуды дамытуды қамтамасыз етеді.",
      facts: [
        ["Келісім түрі", "Өнімді бөлу туралы келісім (ӨБК)"],
        ["Орналасқан жері", "Маңғыстау облысы"],
        ["PSA рөлі", "Мемлекет мүддесін білдіру, қазақстандық қамтуды дамыту"],
      ],
    },
    en: {
      summary: "Dunga is an oil field in the Mangystau region, developed under a production sharing agreement. PSA represents state interests and supports the development of Kazakhstani content.",
      facts: [
        ["Agreement type", "Production sharing agreement (PSA)"],
        ["Location", "Mangystau region"],
        ["PSA's role", "Representing state interests, developing Kazakhstani content"],
      ],
    },
  },
};

let currentLang = "kz";
let openProjectId = null;

function translate(key) {
  return (translations[currentLang] && translations[currentLang][key]) || translations.ru[key] || key;
}

function applyLanguage(lang) {
  if (!translations[lang]) return;
  currentLang = lang;
  document.documentElement.lang = lang;

  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = translate(el.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    el.setAttribute("placeholder", translate(el.dataset.i18nPlaceholder));
  });
  document.querySelectorAll("[data-i18n-aria-label]").forEach((el) => {
    el.setAttribute("aria-label", translate(el.dataset.i18nAriaLabel));
  });

  document.querySelectorAll(".lang-btn").forEach((btn) => {
    const isActive = btn.dataset.lang === lang;
    btn.classList.toggle("is-active", isActive);
    btn.setAttribute("aria-pressed", String(isActive));
  });

  if (openProjectId) fillProjectModal(openProjectId);
}

document.querySelectorAll(".lang-btn").forEach((btn) => {
  btn.addEventListener("click", () => applyLanguage(btn.dataset.lang));
});

/* ---------- Мобильное меню ---------- */

const navToggle = document.getElementById("nav-toggle");
const mainNav = document.getElementById("main-nav");

function closeMobileNav() {
  if (!navToggle || !mainNav) return;
  mainNav.classList.remove("is-open");
  navToggle.setAttribute("aria-expanded", "false");
}

if (navToggle && mainNav) {
  navToggle.addEventListener("click", () => {
    const isOpen = mainNav.classList.toggle("is-open");
    navToggle.setAttribute("aria-expanded", String(isOpen));
  });
}

/* ---------- 1. Плавный скролл по якорным ссылкам ---------- */

document.querySelectorAll('a[href^="#"]').forEach((link) => {
  link.addEventListener("click", (event) => {
    const hash = link.getAttribute("href");
    if (!hash || hash === "#") return;

    const target = document.querySelector(hash);
    if (!target) return;

    event.preventDefault();
    target.scrollIntoView({ behavior: "smooth", block: "start" });
    target.setAttribute("tabindex", "-1");
    target.focus({ preventScroll: true });

    closeMobileNav();
    const openDetails = link.closest("details");
    if (openDetails) openDetails.open = false;
  });
});

/* ---------- 2. Модальные окна проектов ---------- */

const projectModal = document.getElementById("project-modal");
const projectModalEyebrow = document.getElementById("project-modal-eyebrow");
const projectModalTitle = document.getElementById("project-modal-title");
const projectModalBody = document.getElementById("project-modal-body");
const projectModalClose = document.getElementById("project-modal-close");

function fillProjectModal(projectId) {
  const details = projectDetails[projectId] && projectDetails[projectId][currentLang];
  if (!details) return;

  projectModalEyebrow.textContent = translate(`project.${projectId}.region`);
  projectModalTitle.textContent = translate(`project.${projectId}.title`);

  projectModalBody.innerHTML = "";

  const summary = document.createElement("p");
  summary.textContent = details.summary;
  projectModalBody.append(summary);

  const dl = document.createElement("dl");
  details.facts.forEach(([term, desc]) => {
    const dt = document.createElement("dt");
    dt.textContent = term;
    const dd = document.createElement("dd");
    dd.textContent = desc;
    dl.append(dt, dd);
  });
  projectModalBody.append(dl);
}

function openProjectModal(projectId) {
  if (!projectDetails[projectId] || typeof projectModal.showModal !== "function") return;
  openProjectId = projectId;
  fillProjectModal(projectId);
  projectModal.showModal();
}

function closeProjectModal() {
  projectModal.close();
}

document.querySelectorAll(".project-card").forEach((card) => {
  card.addEventListener("click", () => openProjectModal(card.dataset.project));
});

if (projectModalClose) {
  projectModalClose.addEventListener("click", closeProjectModal);
}

if (projectModal) {
  projectModal.addEventListener("click", (event) => {
    if (event.target === projectModal) closeProjectModal();
  });
  projectModal.addEventListener("close", () => {
    openProjectId = null;
  });
}

/* ---------- 3. Валидация формы обратной связи ---------- */

const contactForm = document.getElementById("contact-form");
const contactFormStatus = document.getElementById("contact-form-status");

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function setFieldError(fieldId, message) {
  const input = document.getElementById(fieldId);
  const errorEl = document.getElementById(`${fieldId}-error`);
  const field = input.closest(".form-field");

  if (message) {
    field.classList.add("has-error");
    input.setAttribute("aria-invalid", "true");
    errorEl.textContent = message;
  } else {
    field.classList.remove("has-error");
    input.removeAttribute("aria-invalid");
    errorEl.textContent = "";
  }
}

function validateContactForm() {
  const name = document.getElementById("contact-name").value.trim();
  const email = document.getElementById("contact-email").value.trim();
  const message = document.getElementById("contact-message").value.trim();

  let firstInvalidId = null;

  if (!name) {
    setFieldError("contact-name", translate("errors.name_required"));
    firstInvalidId = firstInvalidId || "contact-name";
  } else {
    setFieldError("contact-name", "");
  }

  if (!email) {
    setFieldError("contact-email", translate("errors.email_required"));
    firstInvalidId = firstInvalidId || "contact-email";
  } else if (!EMAIL_PATTERN.test(email)) {
    setFieldError("contact-email", translate("errors.email_invalid"));
    firstInvalidId = firstInvalidId || "contact-email";
  } else {
    setFieldError("contact-email", "");
  }

  if (!message) {
    setFieldError("contact-message", translate("errors.message_required"));
    firstInvalidId = firstInvalidId || "contact-message";
  } else {
    setFieldError("contact-message", "");
  }

  return firstInvalidId;
}

if (contactForm) {
  contactForm.addEventListener("submit", (event) => {
    event.preventDefault();

    contactFormStatus.classList.remove("is-success", "is-error");
    contactFormStatus.textContent = "";

    const firstInvalidId = validateContactForm();
    if (firstInvalidId) {
      document.getElementById(firstInvalidId).focus();
      return;
    }

    contactForm.reset();
    contactFormStatus.classList.add("is-success");
    contactFormStatus.textContent = translate("form.success");
  });

  ["contact-name", "contact-email", "contact-message"].forEach((id) => {
    document.getElementById(id).addEventListener("input", () => setFieldError(id, ""));
  });
}

/* ---------- Инициализация ---------- */

applyLanguage(currentLang);
