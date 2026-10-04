import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

class Asset(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	name = models.CharField(max_length=180)
	drive_id = models.CharField(max_length=180, unique=True)
	alt = models.CharField(max_length=300, blank=True)
	public = models.BooleanField(default=False)
	mime = models.CharField(max_length=100, blank=True)
	size = models.PositiveBigIntegerField(default=0)
	width = models.PositiveIntegerField(default=0)
	height = models.PositiveIntegerField(default=0)
	duration_ms = models.PositiveBigIntegerField(default=0)
	checksum = models.CharField(max_length=64, blank=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.name


class SiteSettings(models.Model):
	name = models.CharField(max_length=100, default="Thomas Fassih")
	title = models.CharField(max_length=80, default="Polymath")
	about = models.TextField(blank=True)
	description = models.CharField(max_length=180, blank=True)
	email = models.EmailField(blank=True)
	calendly = models.URLField(blank=True)
	linkedin = models.URLField(blank=True)
	github = models.URLField(blank=True)
	social_image = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
	privacy = models.TextField(blank=True)
	updated_at = models.DateTimeField(auto_now=True)

	def save(self, *args, **kwargs):
		self.pk = 1
		super().save(*args, **kwargs)

	def __str__(self):
		return "Website Settings"


class ResumeSection(models.Model):
	title = models.CharField(max_length=100)
	position = models.PositiveIntegerField(default=0)
	body = models.TextField(blank=True)
	visible = models.BooleanField(default=True)

	class Meta:
		ordering = ['position', 'pk']

	def __str__(self):
		return self.title


class Job(models.Model):
	section = models.ForeignKey(ResumeSection, on_delete=models.CASCADE, related_name="jobs")
	title = models.CharField(max_length=160)
	company = models.CharField(max_length=160)
	logo = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
	start = models.DateField(help_text="First day of the month.")
	end = models.DateField(null=True, blank=True)
	location = models.CharField(max_length=160, blank=True)
	job_type = models.CharField(max_length=80, blank=True)
	description = models.TextField(blank=True)
	visible = models.BooleanField(default=True)

	class Meta:
		ordering = ['-start', '-pk']

	def clean(self):
		if self.end and self.start and self.end < self.start:
			raise ValidationError("End date cannot be before start date.")

	def __str__(self):
		return f"{self.title} - {self.company}"


class Accomplishment(models.Model):
	job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="accomplishments")
	text = models.TextField()
	position = models.PositiveIntegerField(default=0)

	class Meta:
		ordering = ['position', 'pk']

class Tag(models.Model):
	name = models.CharField(max_length=60, unique=True)
	slug = models.SlugField(unique=True)

	def __str__(self):
		return self.name


class Entry(models.Model):
	KINDS = [("writing", "Writing"), ("software", "Software"), ("blog", "Blog")]
	CATEGORIES = [
		("fiction", "Fiction"),
		("research", "Research & Analysis"),
		("technical", "Technical"),
		("screenplays", "Screenplays"),
	]
	kind = models.CharField(max_length=12, choices=KINDS)
	category = models.CharField(max_length=16, choices=CATEGORIES, blank=True)
	title = models.CharField(max_length=180)
	slug = models.SlugField(max_length=180, unique=True)
	thumbnail = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
	excerpt = models.CharField(max_length=300, blank=True)
	body = models.TextField()
	repo_url = models.URLField(blank=True)
	tags = models.ManyToManyField(Tag, blank=True)
	published = models.BooleanField(default=False)
	published_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(auto_now=True)
	seo_description = models.CharField(max_length=180, blank=True)

	class Meta:
		ordering = ['-published_at', '-pk']
		indexes = [
			models.Index(fields=['kind', 'published', 'published_at']),
		]

	def clean(self):
		if self.kind == "writing" and not self.category:
			raise ValidationError("Category is required for writing entries.")

	def __str__(self):
		return self.title


class GalleryItem(models.Model):
	kind = models.CharField(max_length=8, choices=[("images", "Image"), ("videos", "Video")])
	title = models.CharField(max_length=180)
	description = models.TextField(blank=True)
	asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="+")
	poster = models.ForeignKey(Asset, on_delete=models.PROTECT, null=True, blank=True, related_name="+")
	captions = models.ForeignKey(Asset, on_delete=models.PROTECT, null=True, blank=True, related_name="+")
	described_video = models.ForeignKey(Asset, on_delete=models.PROTECT, null=True, blank=True, related_name="+")
	transcript = models.TextField(blank=True)
	position = models.PositiveIntegerField(default=0)
	published = models.BooleanField(default=False)

	class Meta:
		ordering = ['position', 'pk']

	def clean(self):
		if self.kind == "videos" and not self.poster_id:
			raise ValidationError("Poster is required for video gallery items.")
		for field in ["asset", "poster", "captions", "described_video"]:
			obj = getattr(self, field, None)
			if self.published and obj and not obj.public:
				raise ValidationError(f"{field} must be public to publish this gallery item.")
		if self.asset_id and self.asset.mime:
			expected = "image/" if self.kind == "images" else "video/"
			if not self.asset.mime.startswith(expected):
				raise ValidationError(f"Asset MIME type must start with '{expected}' for {self.kind} gallery items.")

	def __str__(self):
		return self.title


class Subscriber(models.Model):
	email = models.EmailField(unique=True)
	token = models.UUIDField(null=True, blank=True, unique=True)
	requested_at = models.DateTimeField(auto_now_add=True)
	confirmed_at = models.DateTimeField(null=True, blank=True)
	contact_id = models.CharField(max_length=80, blank=True)


class Notification(models.Model):
	entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
	status = models.CharField(max_length=16, default="queued")
	broadcast_id = models.CharField(max_length=80, blank=True)
	error = models.CharField(max_length=300, blank=True)
	updated_at = models.DateTimeField(auto_now=True)


class Visit(models.Model):
	event_id = models.UUIDField(unique=True)
	path = models.CharField(max_length=240)
	referrer = models.CharField(max_length=180, blank=True)
	created_at = models.DateTimeField(auto_now_add=True, db_index=True)


class RateBucket(models.Model):
	key = models.CharField(max_length=64, unique=True)
	count = models.PositiveIntegerField(default=0)
	expires_at = models.DateTimeField(db_index=True)