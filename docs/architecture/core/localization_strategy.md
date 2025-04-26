
# Localization (i18n/L10n) Strategy

## 1. Overview

*   **Purpose**: To define the strategy and technical approach for implementing internationalization (i18n - supporting multiple languages) and localization (L10n - adapting to regional formats/conventions) within the ERP system.
*   **Scope**: Covers language support for UI text and potentially model data, locale-aware formatting of dates/times/numbers/currencies, timezone handling, and the chosen tools/libraries. Excludes building a custom translation management platform.
*   **Goal**: Provide a consistent user experience tailored to the user's preferred language and regional settings, and enable translation of application interfaces and potentially database content.

## 2. Core Principles

*   **Leverage Django Framework**: Utilize Django's built-in i18n and L10n capabilities as the foundation.
*   **Standard Formats**: Use industry standards for language codes (ISO 639-1, e.g., `en`, `es`, `fr-ca`) and country codes (ISO 3166-1 alpha-2, e.g., `US`, `GB`, `CA`).
*   **UTF-8 Everywhere**: Ensure all text data is handled and stored using UTF-8 encoding.
*   **UTC for Timestamps**: Store all timezone-aware datetimes in the database as UTC (as mandated by `USE_TZ=True`). Convert to user's local timezone for display only.
*   **Separation of Code and Translations**: Keep translatable strings separate from code logic using `gettext`.
*   **Model Translation Solution**: Select and consistently use a dedicated library for translating database content fields.

## 3. Internationalization (i18n) - Language Support

### 3.1. Supported Languages (`settings.LANGUAGES`)
*   Define the list of languages the application will officially support in `settings.py`.
    ```python
    from django.utils.translation import gettext_lazy as _

    LANGUAGES = [
        ('en', _('English')),
        ('es', _('Spanish')),
        ('fr', _('French')),
        # Add other required languages
    ]
    ```
*   Define the default language (`settings.LANGUAGE_CODE`, e.g., `'en'`).
*   Enable Django's i18n system (`settings.USE_I18N = True`).

### 3.2. Marking Strings for Translation
*   **Python Code (.py files):** Use `from django.utils.translation import gettext_lazy as _` and wrap translatable strings: `_("Your translatable string")`. Use `gettext` for immediate translation if needed (less common). Use `pgettext` for context and `ngettext` for pluralization.
*   **Django Templates (.html files):** Load the `i18n` tag library (`{% load i18n %}`) and use:
    *   `{% trans "Your translatable string" %}`
    *   `{% blocktrans %}String with {{ variable }}{% endblocktrans %}`
    *   `{% blocktrans count counter=my_list|length %}Singular string{% plural %}Plural string with {{ counter }} items{% endblocktrans %}`
*   **DRF Serializers/Models:** Use `gettext_lazy` for `verbose_name`, `help_text`, and potentially `choices` display values.

### 3.3. Translation File Workflow (`.po`/`.mo` files)
*   **Extraction:** Use `django-admin makemessages -l <lang_code>` (e.g., `-l es`) to extract translatable strings into `.po` files within `locale/<lang_code>/LC_MESSAGES/` directories in each app (or a project-level locale path).
*   **Translation:** Provide the generated `.po` files to translators (human or machine translation service). Translators fill in the `msgstr` entries.
*   **Compilation:** Use `django-admin compilemessages` to compile the translated `.po` files into binary `.mo` files, which Django uses at runtime.
*   **Version Control:** Commit both `.po` and `.mo` files to the Git repository.
*   **Process:** Integrate `makemessages` and `compilemessages` into development and deployment workflows.

### 3.4. Locale Detection (Middleware)
*   Enable Django's `django.middleware.locale.LocaleMiddleware` in `settings.MIDDLEWARE` (usually placed after `SessionMiddleware` and before `CommonMiddleware`).
*   This middleware determines the user's preferred language based on (in order): URL prefix, session, cookie, `Accept-Language` HTTP header, default `LANGUAGE_CODE`.

### 3.5. Translating Database Content (Model Translation)
*   **Requirement**: Specific model fields (e.g., `Product.name`, `Product.description`, `Category.name`) need to store content in multiple supported languages.
*   **Chosen Library**: **`django-parler`** (Recommended). Provides good integration with Django Admin, DRF serializers, and handles translation storage in separate tables efficiently. *(Alternative: `django-modeltranslation` modifies the original model table directly)*.
    *   *(Decision Confirmation Needed: Confirm `django-parler` is the chosen library)*.
*   **Implementation**:
    1.  Install `django-parler`.
    2.  Add `'parler'` to `INSTALLED_APPS`.
    3.  Configure `PARLER_LANGUAGES` in settings (usually mirrors `LANGUAGES`).
    4.  Modify target models to inherit `parler.models.TranslatableModel`.
    5.  Define translatable fields within a `parler.models.TranslatedFields` wrapper.
    ```python
    # Example product model
    from parler.models import TranslatableModel, TranslatedFields

    class Product(Timestamped, Auditable, OrganizationScoped, TranslatableModel):
        sku = models.CharField(...)
        # ... other non-translatable fields ...

        translations = TranslatedFields(
            name = models.CharField(max_length=255, db_index=True),
            description = models.TextField(blank=True)
        )
        # ...
    ```
    *   Run `makemigrations` and `migrate` (creates translation tables).
    *   Use `parler`'s utilities in Admin (`TranslatableAdmin`), Serializers (`TranslatableModelSerializer`), and Views/Templates to access/manage translated fields.

## 4. Localization (L10n) - Regional Formatting

### 4.1. Core Setting (`settings.py`)
*   Enable Django's L10n system: `USE_L10N = True`.

### 4.2. Date & Time Formatting
*   **Storage**: Store datetimes as timezone-aware UTC (requires `USE_TZ = True`).
*   **Display**: Use Django template tags (`{% load l10n %}`, `{{ my_datetime|localize }}`) or `django.utils.formats` functions (`formats.date_format(my_datetime, format='SHORT_DATETIME_FORMAT', use_l10n=True)`) to display dates and times according to the *active locale*. Define standard formats (`DATE_FORMAT`, `DATETIME_FORMAT`, etc.) in settings if needed.

### 4.3. Number & Currency Formatting
*   **Display**: Use Django template tags (`{{ my_number|localize }}`) or `django.utils.formats` functions (`formats.number_format(my_number, use_l10n=True)`) for locale-aware decimal/thousand separators.
*   **Currency**: Combine L10n number formatting with the `Currency` model's symbol and potentially symbol position conventions (though dedicated money formatting libraries might offer more control).

### 4.4. Timezone Handling
*   **Storage**: Store datetimes as UTC (`USE_TZ = True`).
*   **User Preference**: Store user's preferred timezone (`UserProfile.timezone`).
*   **Display**: Use Django's timezone utilities (`django.utils.timezone`) and middleware (`TimezoneMiddleware` - custom or from a package) to activate the user's preferred timezone for the duration of a request. Convert UTC datetimes to the user's timezone before display using `datetime_obj.astimezone(user_timezone)`.

## 5. Strategy Summary

1.  Enable Django's `USE_I18N`, `USE_L10N`, `USE_TZ` settings.
2.  Define supported `LANGUAGES`.
3.  Use `gettext_lazy` (`_()`) in Python and `{% trans %}`/`{% blocktrans %}` in templates for UI strings. Follow `makemessages`/`compilemessages` workflow.
4.  Use `LocaleMiddleware` for language detection.
5.  Select and integrate **`django-parler`** for translating required database model fields.
6.  Use Django's template tags/format functions (`|localize`) for locale-aware display of dates, times, and numbers.
7.  Store user timezone preferences and activate them (via middleware) for displaying times correctly.

## 6. Testing

*   Test translation string extraction (`makemessages`).
*   Test display of UI elements in different languages (requires loading `.mo` files). Use `override_settings(LANGUAGE_CODE=...)` and `translation.activate(lang_code)` in tests.
*   Test locale-aware formatting of dates/numbers.
*   Test model translation: Create/update/retrieve translated fields via API/ORM in different languages. Use `parler`'s testing utilities if needed.
*   Test timezone conversions and display.

--- END OF FILE localization_strategy.md ---