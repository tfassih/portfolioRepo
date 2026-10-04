from datetime import timedelta
from django import forms
from django.contrib import admin, messages
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.urls import path
from django.utils import timezone
from .models import (
    Asset,
    SiteSettings,
    ResumeSection,
    Job,
    Accomplishment,
    Tag,
    Entry,
    GalleryItem,
    Subscriber,
    Notification,
)
from .models import Visit
from .drive import import_metadata
from .emailing import process_one


class StudioAdmin(admin.AdminSite):
    site_header = "Thomas Fassih | Studio"
    site_title = "Studio"
    index_title = "Content and publishing"


    def get_urls(self):
        return [
            path("traffic/", self.admin_view(self.traffic), name="traffic")
        ] + super().get_urls()

    
    def traffic(self, request):
        today = timezone.localdate()
        first = today - timedelta(days=29)
        visits = Visit.objects.filter(created_at__date__gte=first)
        counts = {
            r["day"]: r["n"]
            for r in visits.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(n=Count("pk"))
        }
        rows = [
            {
                "day": first + timedelta(days=i),
                "n": counts.get(first + timedelta(days=i), 0),
            }
            for i in range(30)
        ]
        maximum = max([r["n"] for r in rows] + [1])
        for r in rows:
            r["width"] = round(100 * r["n"] / maximum, 1)
        context = {
            **self.each_context(request),
            "title": "Traffic - last 30 days",
            "total": visits.count(),
            "rows": rows,
            "pages": visits.values("path").annotate(n=Count("pk")).order_by("-n")[:10],
            "referrers": visits.values("referrer")
            .annotate(n=Count("pk"))
            .order_by("-n")[:10],
        }
        return render(request, "admin/traffic.html", context)

    
studio = StudioAdmin(name="studio")
class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("drive_id"):
            self.instance.drive_id = cleaned["drive_id"]
            try:
                import_metadata(self.instance)
            except Exception:
                raise forms.ValidationError(
                    "Cannot import this file. Check its ID, folder, type, size, and Drive access."
                )
            if self.instance.mime.startswith("image/") and not cleaned.get("alt"):
                self.add_error("alt", "Write a useful text alternative.")
        return cleaned

    
@admin.register(Asset, site=studio)
class AssetAdmin(admin.ModelAdmin):
    form = AssetForm
    list_display = ["name", "mime", "size", "public"]
    list_filter = ["public", "mime"]
    search_fields = ["name", "drive_id"]
    readonly_fields = [
        "mime",
        "size",
        "width",
        "height",
        "duration_ms",
        "checksum",
        "updated_at",
    ]


@admin.register(SiteSettings, site=studio)
class SettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False

    
@admin.register(ResumeSection, site=studio)
class SectionAdmin(admin.ModelAdmin):
    list_display = ["title", "position", "visible"]
    list_editable = ["position", "visible"]


class AccomplishmentInline(admin.TabularInline):
    model = Accomplishment
    extra = 1


@admin.register(Job, site=studio)
class JobAdmin(admin.ModelAdmin):
    list_display = ["title", "company", "start", "end", "visible"]
    list_filter = ["visible", "section"]
    inlines = [AccomplishmentInline]


@admin.register(Tag, site=studio)
class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Entry, site=studio)
class EntryAdmin(admin.ModelAdmin):
    list_display = ["title", "kind", "category", "published", "published_at"]
    list_filter = ["kind", "category", "published", "tags"]
    search_fields = ["title", "body"]
    filter_horizontal = ["tags"]
    prepopulated_fields = {"slug": ["title"]}
    actions = ["publish_and_queue"]

    @admin.action(description="Publish selected entries and queue blog notifications")
    def publish_and_queue(self, request, queryset):
        for e in queryset:
            e.published = True
            e.save()
            if e.kind == "blog":
                Notification.objects.get_or_create(entry=e)
        self.message_user(request, "Published. New blog notifications are queued.")


@admin.register(GalleryItem, site=studio)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ["title", "kind", "position", "published"]
    list_filter = ["kind", "published"]


@admin.register(Subscriber, site=studio)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ["email", "requested_at", "confirmed_at"]
    readonly_fields = ["email", "requested_at", "confirmed_at", "contact_id", "token"]

    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Remove the provider contact before purging local consent history.
        return False


@admin.register(Notification, site=studio)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["entry", "status", "broadcast_id", "updated_at"]
    readonly_fields = ["entry", "status", "broadcast_id", "error", "updated_at"]
    actions = ["send_now"]
    def has_add_permission(self, request):
        return False
    @admin.action(description="Send one queued notification now")
    def send_now(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(
                request, "Select exactly one notification.", messages.ERROR
            )
            return
        self.message_user(request, process_one(queryset.first().pk))
# Keep user/password management inside the same protected admin site.
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
studio.register(User, UserAdmin)
studio.register(Group, GroupAdmin)