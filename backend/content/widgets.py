from django import forms
from django.urls import reverse
from django.utils.safestring import mark_safe


class QuillWidget(forms.Textarea):
    """Textarea с наложенным поверх WYSIWYG-редактором (Quill, с CDN —
    без отдельного pip-пакета, поэтому не завязано на совместимость
    django-ckeditor и т.п. с конкретной версией Django).

    Сама textarea остаётся в DOM (просто скрыта) и участвует в отправке
    формы как обычно — Quill только синхронизирует своё HTML-содержимое
    в неё при каждом изменении. На сервере ничего не парсит и не
    валидирует — поле остаётся обычным models.TextField с HTML внутри.

    Картинки: кнопка "image" на панели инструментов загружает файл на
    сервер (content.views.quill_image_upload, только для staff) и
    вставляет в текст настоящую ссылку на файл — не base64 в самом
    HTML-поле (это раздуло бы TextField и страницу на каждой загрузке).
    """

    class Media:
        css = {
            "all": ["https://cdnjs.cloudflare.com/ajax/libs/quill/1.3.7/quill.snow.min.css"],
        }
        js = ["https://cdnjs.cloudflare.com/ajax/libs/quill/1.3.7/quill.min.js"]

    def render(self, name, value, attrs=None, renderer=None):
        textarea_html = super().render(name, value, attrs, renderer)
        widget_id = (attrs or {}).get("id", f"id_{name}")
        editor_id = f"{widget_id}_quill_editor"
        upload_url = reverse("quill_image_upload")

        script = f"""
<div id="{editor_id}" class="quill-editor" style="background:#fff;"></div>
<script>
(function() {{
  var textarea = document.getElementById("{widget_id}");
  textarea.style.display = "none";
  var editorEl = document.getElementById("{editor_id}");

  function getCookie(name) {{
    var match = document.cookie.match("(^|;\\\\s*)" + name + "=([^;]*)");
    return match ? decodeURIComponent(match[2]) : "";
  }}

  function uploadImage(quill) {{
    var input = document.createElement("input");
    input.type = "file";
    input.accept = "image/*";
    input.onchange = function() {{
      var file = input.files[0];
      if (!file) return;
      var range = quill.getSelection(true);
      var formData = new FormData();
      formData.append("image", file);
      fetch("{upload_url}", {{
        method: "POST",
        headers: {{ "X-CSRFToken": getCookie("csrftoken") }},
        body: formData,
      }})
        .then(function(res) {{ return res.json(); }})
        .then(function(data) {{
          if (data.url) {{
            quill.insertEmbed(range.index, "image", data.url, "user");
            quill.setSelection(range.index + 1);
          }} else {{
            alert("Не удалось загрузить изображение: " + (data.error || "неизвестная ошибка"));
          }}
        }})
        .catch(function() {{ alert("Не удалось загрузить изображение."); }});
    }};
    input.click();
  }}

  var quill = new Quill(editorEl, {{
    theme: "snow",
    modules: {{
      toolbar: {{
        container: [
          [{{ header: [false, 2, 3] }}],
          ["bold", "italic", "underline"],
          [{{ list: "ordered" }}, {{ list: "bullet" }}],
          ["link", "image"],
          ["clean"],
        ],
        handlers: {{
          image: function() {{ uploadImage(quill); }},
        }},
      }},
    }},
  }});
  quill.root.innerHTML = textarea.value;
  quill.on("text-change", function() {{
    var html = quill.root.innerHTML;
    textarea.value = (html === "<p><br></p>") ? "" : html;
  }});
}})();
</script>
"""
        return mark_safe(str(textarea_html) + script)
