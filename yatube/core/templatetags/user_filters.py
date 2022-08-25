from django import template

register = template.Library()


@register.filter
def addclass(field, css):
    return field.as_widget(attrs={"class": css})


@register.filter
def uglify(text):
    index = 0
    new_text = []
    for letter in text:
        index += 1
        if index % 2:
            new_text.append(letter.lower())
            continue
        new_text.append(letter.upper())
    return "".join(new_text)
